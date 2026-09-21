"""Deterministic validation applied after every provider response."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ksc_api.services.ai_providers import (
    SAFE_ANALYSIS_TEXT,
    ProviderClaim,
    ProviderResponse,
    ProviderSource,
)

ERROR_CODES = frozenset(
    {
        "UNSUPPORTED_CLAIM",
        "CITATION_NOT_FOUND",
        "CITATION_DOES_NOT_SUPPORT_CLAIM",
        "QUOTE_NOT_VERIFIED",
        "DOCUMENT_NOT_FOUND",
        "TRANSCRIPT_LOCATION_NOT_FOUND",
        "EXHIBIT_NOT_FOUND",
    }
)

_KINDS = (
    "court",
    "evidence",
    "testimony",
    "spo",
    "defence",
    "court_response",
    "human_note",
    "ai",
)
_ORDER = {kind: index for index, kind in enumerate(_KINDS)}
_CONTENT_TYPES = {"verbatim_quote", "source_paraphrase", "ai_analysis", "abstention"}
_CATEGORY_KIND = {
    "court_finding": "court",
    "witness_testimony": "testimony",
    "spo_argument": "spo",
    "defence_argument": "defence",
    "document_exhibit": "evidence",
    "court_response": "court_response",
    "human_note": "human_note",
}
_PROHIBITED = re.compile(
    r"\b(guilt|guilty|culpable|credibility score|judicial quality|appeal success|"
    r"success probability|likely guilty|probably guilty)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ValidationError:
    code: str
    detail: str
    claim_index: int | None = None

    def as_dict(self) -> dict[str, str | int | None]:
        return {"code": self.code, "detail": self.detail, "claim_index": self.claim_index}


def validate_response(
    response: ProviderResponse, sources: tuple[ProviderSource, ...]
) -> tuple[ValidationError, ...]:
    errors: list[ValidationError] = []
    whitelist = {source.id: source for source in sources}
    previous_order = -1
    for index, claim in enumerate(response.claims):
        errors.extend(_validate_claim(index, claim, whitelist))
        order = _ORDER.get(claim.kind)
        if order is None:
            errors.append(ValidationError("UNSUPPORTED_CLAIM", "unknown answer category", index))
        elif order < previous_order:
            errors.append(
                ValidationError("UNSUPPORTED_CLAIM", "answer categories are out of order", index)
            )
        else:
            previous_order = order
    if not response.claims:
        errors.append(ValidationError("UNSUPPORTED_CLAIM", "provider returned no claims"))
    return tuple(errors)


def _validate_claim(
    index: int, claim: ProviderClaim, whitelist: dict[str, ProviderSource]
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    if claim.content_type not in _CONTENT_TYPES:
        errors.append(ValidationError("UNSUPPORTED_CLAIM", "unknown content type", index))
    if not claim.source_ids and claim.content_type != "abstention":
        errors.append(ValidationError("UNSUPPORTED_CLAIM", "material claim has no source", index))
    found = [whitelist[source_id] for source_id in claim.source_ids if source_id in whitelist]
    missing = [source_id for source_id in claim.source_ids if source_id not in whitelist]
    if missing:
        errors.append(
            ValidationError(
                "CITATION_NOT_FOUND",
                f"claim cited source outside retrieval whitelist: {', '.join(missing)}",
                index,
            )
        )
    if claim.kind != "ai" and found:
        expected = _CATEGORY_KIND.get(found[0].category)
        if expected != claim.kind or any(
            _CATEGORY_KIND.get(source.category) != expected for source in found
        ):
            errors.append(
                ValidationError(
                    "CITATION_DOES_NOT_SUPPORT_CLAIM",
                    "answer category does not match source category",
                    index,
                )
            )
    if claim.kind == "ai" and claim.content_type == "ai_analysis":
        if _normalise(claim.text) != _normalise(SAFE_ANALYSIS_TEXT):
            errors.append(
                ValidationError(
                    "UNSUPPORTED_CLAIM",
                    "AI analysis is outside the approved non-factual safety boundary",
                    index,
                )
            )
    elif claim.content_type == "ai_analysis":
        errors.append(
            ValidationError(
                "CITATION_DOES_NOT_SUPPORT_CLAIM",
                "record categories cannot contain AI analysis",
                index,
            )
        )
    if claim.content_type == "verbatim_quote" and not any(
        _normalise(claim.text) == _normalise(source.text) for source in found
    ):
        errors.append(
            ValidationError("QUOTE_NOT_VERIFIED", "quote does not exactly match a source", index)
        )
    if claim.content_type == "source_paraphrase":
        errors.append(
            ValidationError(
                "CITATION_DOES_NOT_SUPPORT_CLAIM",
                "unreviewed paraphrases are withheld; use an exact quote or abstain",
                index,
            )
        )
    if _PROHIBITED.search(claim.text):
        errors.append(
            ValidationError("UNSUPPORTED_CLAIM", "prohibited evaluative conclusion", index)
        )
    return errors


def _normalise(value: str) -> str:
    return " ".join(value.split())
