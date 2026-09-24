"""Persist source-backed full-name aliases (Phase 19B).

Full names are recorded only from an official public statement that names a
registered person: the case caption on filing cover pages, which lists the
accused of this case ("Specialist Prosecutor v. Hashim Thaçi, Kadri Veseli,
Rexhep Selimi and Jakup Krasniqi"). Each distinct spelling is its own alias
with the first page and character range that states it; spellings are never
normalized or merged, and homoglyph variants that do not bind are skipped.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ksc_api.models import (
    PUBLIC_VISIBILITIES,
    Case,
    Document,
    DocumentPage,
    DocumentVersion,
    Person,
    PersonAlias,
    version_language,
)
from ksc_ingestion.identity import bind_caption_accused, caption_lists, slug_role_and_key

CAPTION_RULE = "person.alias.case_caption"
_NS = uuid.UUID("c0ffee19-b0a1-4b5e-8a1a-5ca9710a1a5e")


@dataclass(frozen=True)
class AliasResult:
    captions_seen: int
    captions_bound: int
    aliases: int


def project_caption_aliases(session: Session, case: Case) -> AliasResult:
    accused_by_key: dict[str, uuid.UUID] = {}
    for person_id, slug in session.execute(
        select(Person.id, Person.slug).where(Person.case_id == case.id)
    ).all():
        role, key = slug_role_and_key(slug)
        if role == "accused":
            accused_by_key[key] = person_id
    session.execute(
        delete(PersonAlias).where(
            PersonAlias.rule_id == CAPTION_RULE,
            PersonAlias.person_id.in_(list(accused_by_key.values()) or [uuid.uuid4()]),
        )
    )
    public = tuple(PUBLIC_VISIBILITIES)
    pages = session.execute(
        select(DocumentPage, DocumentVersion.official_version_ref, Document.language)
        .join(DocumentVersion, DocumentVersion.id == DocumentPage.document_version_id)
        .join(Document, Document.id == DocumentVersion.document_id)
        .where(
            Document.case_id == case.id,
            Document.visibility.in_(public),
            DocumentVersion.visibility.in_(public),
            DocumentPage.text.ilike("%Specialist Prosecutor%"),
        )
        .order_by(DocumentVersion.official_version_ref, DocumentPage.pdf_page_index)
    ).all()
    seen = bound = 0
    first_source: dict[tuple[uuid.UUID, str], PersonAlias] = {}
    for page, version_ref, language in pages:
        for names in caption_lists(page.text or ""):
            seen += 1
            bindings = bind_caption_accused(names, accused_by_key)
            bound += int(bool(bindings))
            for person_id, name in bindings:
                alias_text = " ".join(name.name.split())
                alias_key = (person_id, alias_text)
                if alias_key in first_source:
                    continue
                first_source[alias_key] = PersonAlias(
                    id=uuid.uuid5(_NS, f"{person_id}:{alias_text}"),
                    person_id=person_id,
                    alias=alias_text,
                    language=version_language(version_ref, language),
                    alias_kind="full_name",
                    source_document_version_id=page.document_version_id,
                    source_pdf_page_index=page.pdf_page_index,
                    source_char_start=name.start,
                    source_char_end=name.end,
                    rule_id=CAPTION_RULE,
                )
    existing = {
        (person_id, alias)
        for person_id, alias in session.execute(
            select(PersonAlias.person_id, PersonAlias.alias).where(
                PersonAlias.person_id.in_(list(accused_by_key.values()) or [uuid.uuid4()])
            )
        ).all()
    }
    added = 0
    for alias_key, alias in first_source.items():
        if alias_key in existing:
            continue
        session.add(alias)
        added += 1
    session.flush()
    return AliasResult(captions_seen=seen, captions_bound=bound, aliases=added)
