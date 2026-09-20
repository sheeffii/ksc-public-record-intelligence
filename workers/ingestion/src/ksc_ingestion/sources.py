"""Official KSC public sources: host allowlist and URL classification.

Nothing here builds a URL. URLs arrive from the official site (a listing, a
detail page, an operator's browser) and are classified so the pipeline knows
what it is looking at and can canonicalize the same record's URL spelled two
ways. Anything off the allowlist is rejected before any other step runs.

Observed public URL shapes (discovery 2026-09-20; see docs/ingestion/OFFICIAL_SOURCES.md):

    https://www.scp-ks.org/en/cases/...                              case page
    https://repository.scp-ks.org/?icc_filters[case_number]=…&page=N listing
    https://repository.scp-ks.org/details.php?doc_id=<16 hex>&doc_type=stl_filing&lang=eng
    https://repository.scp-ks.org/LW/Published/Filing/<id>/<title>.pdf
    https://repository.scp-ks.org/LW/Published/Transcript/<case>/<hearing>.pdf
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from ksc_api.models.enums import SourceSystem

OFFICIAL_HOSTS: frozenset[str] = frozenset(
    {"www.scp-ks.org", "scp-ks.org", "repository.scp-ks.org"}
)

PCR_HOST = "repository.scp-ks.org"
CASE_SITE_HOSTS: frozenset[str] = frozenset({"www.scp-ks.org", "scp-ks.org"})

_DOC_ID_RE = re.compile(r"^[0-9a-f]{16}$")
# Official case numbers ("KSC-BC-2020-06") and the synthetic demo case
# ("KSC-DEMO-0000"). The pipeline still requires equality with the configured case.
CASE_NUMBER_PATTERN = r"KSC-[A-Z]{2,6}-\d{4}(?:-\d{2})?"
CASE_NUMBER_RE = re.compile(rf"^{CASE_NUMBER_PATTERN}$")
_PUBLISHED_PATH_RE = re.compile(r"^/LW/Published/(?P<kind>[A-Za-z]+)/(?P<rest>.+)$")


class UrlKind(enum.StrEnum):
    CASE_PAGE = "case_page"
    PCR_LISTING = "pcr_listing"
    PCR_DETAIL = "pcr_detail"
    PCR_ARTIFACT = "pcr_artifact"
    OTHER_OFFICIAL = "other_official"


class NotOfficialSourceError(ValueError):
    """The URL is not on an official KSC public host. Nothing is fetched,
    stored or recorded for it."""


@dataclass(frozen=True)
class ClassifiedUrl:
    url: str
    kind: UrlKind
    host: str
    source_system: SourceSystem
    # PCR detail pages: the repository's own record key (16 hex chars).
    doc_id: str | None = None
    doc_type: str | None = None
    lang: str | None = None
    # PCR artifacts: "Filing", "Transcript", … as spelled in the path.
    artifact_kind: str | None = None
    # Listing pages: the icc_filters[...] values and page number.
    filters: tuple[tuple[str, str], ...] = ()
    page: int | None = None


def require_official(url: str) -> str:
    """Return the URL if its host is official and the scheme is https;
    otherwise raise. Used as the first gate everywhere a URL enters."""

    parts = urlsplit(url.strip())
    host = (parts.hostname or "").lower()
    if parts.scheme != "https" or host not in OFFICIAL_HOSTS:
        raise NotOfficialSourceError(f"not an official KSC public URL: {url!r}")
    return url.strip()


def is_official(url: str) -> bool:
    try:
        require_official(url)
    except NotOfficialSourceError:
        return False
    return True


def _clean_query(query: str) -> list[tuple[str, str]]:
    """Drop empty / junk parameters (search-engine copies carry `&amp=`)."""

    return [(k, v) for k, v in parse_qsl(query, keep_blank_values=True) if k and k != "amp"]


def classify(url: str) -> ClassifiedUrl:
    url = require_official(url)
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()

    if host in CASE_SITE_HOSTS:
        return ClassifiedUrl(
            url=url, kind=UrlKind.CASE_PAGE, host=host, source_system=SourceSystem.KSC_CASE_PAGE
        )

    query = _clean_query(parts.query)
    qdict = dict(query)

    if parts.path == "/details.php" and "doc_id" in qdict:
        doc_id = qdict["doc_id"].lower()
        if not _DOC_ID_RE.match(doc_id):
            raise NotOfficialSourceError(f"malformed PCR doc_id in {url!r}")
        return ClassifiedUrl(
            url=url,
            kind=UrlKind.PCR_DETAIL,
            host=host,
            source_system=SourceSystem.KSC_PUBLIC_COURT_RECORDS,
            doc_id=doc_id,
            doc_type=qdict.get("doc_type"),
            lang=qdict.get("lang"),
        )

    published = _PUBLISHED_PATH_RE.match(parts.path)
    if published:
        return ClassifiedUrl(
            url=url,
            kind=UrlKind.PCR_ARTIFACT,
            host=host,
            source_system=SourceSystem.KSC_PUBLIC_COURT_RECORDS,
            artifact_kind=published.group("kind"),
        )

    filters = tuple(
        (k[len("icc_filters[") : -1], v)
        for k, v in query
        if k.startswith("icc_filters[") and k.endswith("]")
    )
    if parts.path in {"", "/"} and (filters or "page" in qdict):
        page: int | None = None
        if qdict.get("page", "").isdigit():
            page = int(qdict["page"])
        return ClassifiedUrl(
            url=url,
            kind=UrlKind.PCR_LISTING,
            host=host,
            source_system=SourceSystem.KSC_PUBLIC_COURT_RECORDS,
            filters=filters,
            page=page,
        )

    return ClassifiedUrl(
        url=url,
        kind=UrlKind.OTHER_OFFICIAL,
        host=host,
        source_system=SourceSystem.OTHER_OFFICIAL_KSC,
    )


def canonical_detail_url(doc_id: str, doc_type: str | None, lang: str | None) -> str:
    """The canonical spelling of a PCR detail URL *already observed*: same
    host, path and parameters, stable ordering, junk removed. This does not
    invent a record — `doc_id` must come from an observed URL."""

    if not _DOC_ID_RE.match(doc_id):
        raise NotOfficialSourceError(f"malformed PCR doc_id {doc_id!r}")
    params = [("doc_id", doc_id)]
    if doc_type:
        params.append(("doc_type", doc_type))
    if lang:
        params.append(("lang", lang))
    return urlunsplit(("https", PCR_HOST, "/details.php", urlencode(params), ""))


def canonicalize(url: str) -> str:
    """Canonical form of an official URL: detail pages re-encoded with stable
    parameter order; everything else returned as observed (artifact paths are
    already canonical and must not be altered)."""

    c = classify(url)
    if c.kind is UrlKind.PCR_DETAIL and c.doc_id:
        return canonical_detail_url(c.doc_id, c.doc_type, c.lang)
    return c.url


_LANG_CODES = {
    "eng": "en",
    "en": "en",
    "alb": "sq",
    "sq": "sq",
    "sqi": "sq",
    "srb": "sr",
    "sr": "sr",
    "srp": "sr",
}


def normalize_language(value: str | None) -> str | None:
    """Map the PCR language spellings (`eng`, `alb`, `srb`, …) to ISO 639-1.
    Unknown spellings are kept verbatim rather than guessed."""

    if value is None:
        return None
    v = value.strip().lower()
    if not v or v == "_all":
        return None
    return _LANG_CODES.get(v, v)
