"""Deterministic person identity resolution (Phase 19B).

One place decides how a piece of public source text relates to a registered
person. Nothing here is fuzzy, phonetic or model-based, and nothing promotes an
uncertain match to improve coverage.

States:

- ``VERIFIED``: a rule binds the text to exactly one person (a role-qualified
  speaker label, or a full public name recorded with its source).
- ``REVIEW_REQUIRED``: the text is surname-level (Mr./Ms. + surname) or its
  surname is shared by more than one registered person.
- ``AMBIGUOUS``: the exact text is recorded for more than one person; it is
  never assigned.
- ``SEARCH_ONLY``: lexical presence only (for example a bare surname in body
  text); never stored as a mention.
"""

from __future__ import annotations

import enum
import re
import unicodedata
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

_PERSON_PREFIXES: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (
        re.compile(
            r"^(?:PRESIDING JUDGE|JUDGE|GJYKAT[ËE]SI|KRYETAR(?:I|JA) I TRUPIT GJYKUES)(?: Z\.)?\s+(.+)$",
            re.I,
        ),
        "judge",
        "Judge",
    ),
    (re.compile(r"^(?:THE ACCUSED|I AKUZUARI)\s+(.+)$", re.I), "accused", "Accused"),
    (re.compile(r"^(?:MR\.|MS\.|Z\.|ZNJ\.)\s*(.+)$", re.I), "counsel_or_participant", ""),
)
ROLE_QUALIFIED = frozenset({"judge", "accused"})
NAMED_ROLES = frozenset({"judge", "accused", "counsel_or_participant", "witness"})

# Official case caption on filing cover pages: "Specialist Prosecutor v. A, B,
# C and D". Each name is exactly two Title-case tokens (first name, surname),
# which may wrap across a line; a longer name does not bind (fails closed).
_NAME = r"[A-ZÇË][a-zçëA-ZÇË'\u2019-]+\s+[A-ZÇË][a-zçëA-ZÇË'\u2019-]+"
_CAPTION = re.compile(
    rf"Specialist Prosecutor\s+(?:v\.|versus)\s+(?P<names>{_NAME}(?:\s*,\s*{_NAME})*"
    rf"\s*,?\s+and\s+{_NAME})"
)
_CAPTION_NAME = re.compile(_NAME)


class IdentityState(enum.StrEnum):
    VERIFIED = "verified"
    REVIEW_REQUIRED = "review_required"
    AMBIGUOUS = "ambiguous"
    SEARCH_ONLY = "search_only"


@dataclass(frozen=True)
class IdentityResolution:
    state: IdentityState
    rule: str
    person_id: uuid.UUID | None = None
    candidates: tuple[uuid.UUID, ...] = ()


@dataclass(frozen=True)
class CaptionName:
    """A full name read from an official caption, with its exact span."""

    name: str
    start: int
    end: int
    name_key: str


def name_key(value: str) -> str:
    """Diacritic-folded ASCII key used only to compare recorded names."""
    folded = "".join(
        character
        for character in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]+", "-", folded.lower()).strip("-")


def speaker_label_identity(speaker: str) -> tuple[str, str, str] | None:
    """(slug, display name, role) for a transcript speaker label, or None."""
    compact = " ".join(speaker.split()).strip()
    for pattern, role, title in _PERSON_PREFIXES:
        match = pattern.match(compact)
        if match:
            name = " ".join(match.group(1).split()).strip(" .")
            if not name or name in {"I TRUPIT GJYKUES", "COURT"}:
                return None
            display = f"{title} {name.title()}".strip()
            return f"{role}-{name_key(name)}", display, role
    return None


def slug_role_and_key(slug: str) -> tuple[str, str]:
    role, _, key = slug.partition("-")
    return role, key


def classify_label(
    label: str,
    labels: Mapping[str, tuple[uuid.UUID, str, str]],
    surname_counts: Mapping[str, int],
    ambiguous: Iterable[str] = (),
) -> IdentityResolution | None:
    """Classify a speaker label against recorded labels (label -> person, role, key)."""
    if label in set(ambiguous):
        return IdentityResolution(IdentityState.AMBIGUOUS, "person.speaker_label.ambiguous")
    bound = labels.get(label)
    if bound is None:
        return None
    person_id, role, key = bound
    if role in ROLE_QUALIFIED:
        return IdentityResolution(
            IdentityState.VERIFIED, "person.speaker_label.role_qualified", person_id
        )
    if surname_counts.get(key, 0) > 1:
        return IdentityResolution(
            IdentityState.REVIEW_REQUIRED, "person.speaker_label.shared_surname", person_id
        )
    return IdentityResolution(
        IdentityState.REVIEW_REQUIRED, "person.speaker_label.honorific", person_id
    )


def caption_lists(text: str) -> list[list[CaptionName]]:
    """Full names in each official "Specialist Prosecutor v. ..." caption, per caption."""
    captions: list[list[CaptionName]] = []
    for caption in _CAPTION.finditer(text):
        offset = caption.start("names")
        names = []
        for match in _CAPTION_NAME.finditer(caption.group("names")):
            surname = match.group(0).split()[-1]
            names.append(
                CaptionName(
                    name=match.group(0),
                    start=offset + match.start(),
                    end=offset + match.end(),
                    name_key=name_key(surname),
                )
            )
        captions.append(names)
    return captions


def bind_caption_accused(
    names: list[CaptionName], accused_by_key: Mapping[str, uuid.UUID]
) -> list[tuple[uuid.UUID, CaptionName]]:
    """Bind caption names to registered accused by surname key.

    The caption is a closed list of this case's accused. A binding is made only
    when every surname key in the caption is distinct and matches exactly one
    registered accused; otherwise nothing from that caption is bound.
    """
    keys = [name.name_key for name in names]
    if not names or len(set(keys)) != len(keys):
        return []
    if any(key not in accused_by_key for key in keys):
        return []
    return [(accused_by_key[name.name_key], name) for name in names]


def full_name_state(owners: set[uuid.UUID]) -> IdentityState:
    """A recorded full name bound to one person verifies; shared names never do."""
    return IdentityState.VERIFIED if len(owners) == 1 else IdentityState.AMBIGUOUS
