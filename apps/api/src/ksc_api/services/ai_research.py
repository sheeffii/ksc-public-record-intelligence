"""Citation-first retrieval, generation, validation, and persistence."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from ksc_api.config import Settings
from ksc_api.models import (
    AiOutput,
    AiRetrievalSource,
    AiRun,
    AiRunStatus,
    AnswerBlockKind,
    Argument,
    Case,
    Citation,
    Document,
    DocumentChunk,
    DocumentVersion,
    Finding,
    Party,
    PromptVersion,
    ResearchNote,
    ResolutionState,
    Transcript,
    TranscriptSegment,
    VerificationState,
)
from ksc_api.repositories.filters import public_visibility
from ksc_api.services.ai_providers import (
    AiProvider,
    AnthropicCompatibleProvider,
    DeterministicExtractiveProvider,
    OpenAiCompatibleProvider,
    ProviderError,
    ProviderRequest,
    ProviderResponse,
    ProviderSource,
)
from ksc_api.services.ai_validation import ValidationError, validate_response

PROMPT_NAME = "citation-first-answer"
PROMPT_VERSION = 2
PROMPT_FILE = "citation-first-answer-v2.txt"
MAX_SOURCES = 8
# Persisted scale of ai_retrieval_sources.retrieval_score (Numeric(12, 8)); the
# returned run must mirror the stored audit value exactly.
_SCORE_SCALE = Decimal("0.00000001")
_PUBLIC = {"public", "public_redacted"}
_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9_/-]{2,}")
_RECORD_REF = re.compile(r"\b(?:KSC-BC-2020-06/)?(F\d{5})(?:/[A-Z0-9/]+)?\b", re.I)
_STOPWORDS = {
    "about",
    "according",
    "available",
    "court",
    "does",
    "from",
    "have",
    "record",
    "say",
    "says",
    "that",
    "the",
    "their",
    "this",
    "what",
    "when",
    "where",
    "which",
    "with",
}


@dataclass(frozen=True)
class Candidate:
    anchor_kind: str
    anchor_id: uuid.UUID
    document_version_id: uuid.UUID | None
    citation_id: uuid.UUID | None
    category: str
    visibility: str
    ref: str
    version_ref: str | None
    display: str
    target_path: str
    source_url: str | None
    text: str
    page_from: int | None = None
    page_to: int | None = None
    pdf_page_index: int | None = None
    para_from: int | None = None
    para_to: int | None = None
    line_from: int | None = None
    line_to: int | None = None
    verification: str = "unreviewed"
    verification_reviewed_by: str | None = None
    verification_reviewed_at: datetime | None = None
    method: str = "lexical_fts"
    score: Decimal = Decimal("0")
    metadata: dict[str, str | None] | None = None


class AiResearchService:
    def __init__(
        self,
        session: Session,
        case: Case,
        settings: Settings,
        provider: AiProvider | None = None,
    ) -> None:
        self.session = session
        self.case = case
        self.settings = settings
        self.provider = provider or provider_from_settings(settings)

    def create_run(self, question: str, *, requested_by: str = "research-ui") -> AiRun:
        question = " ".join(question.split())
        if len(question) < 3 or len(question) > 2000:
            raise ValueError("question must contain between 3 and 2000 characters")
        prompt, prompt_hash = self._prompt()
        prompt_version = self._prompt_version(prompt, prompt_hash)
        run = AiRun(
            case_id=self.case.id,
            prompt_version_id=prompt_version.id,
            provider=self.provider.name,
            model=self.provider.model,
            temperature=Decimal(str(self.settings.ai_temperature)),
            question=question,
            system_prompt_sha256=prompt_hash,
            parameters={"temperature": self.settings.ai_temperature, "max_sources": MAX_SOURCES},
            status=AiRunStatus.PENDING,
            requested_by=requested_by,
            started_at=datetime.now(UTC),
            answer_withheld=False,
            insufficient_evidence=False,
            extra={"retrieval": "structured_plus_postgresql_fts", "source_text_untrusted": True},
        )
        self.session.add(run)
        self.session.flush()

        insufficiency = self._known_insufficiency(question)
        candidates = [] if insufficiency else self._retrieve(question)
        sources = self._persist_sources(run, candidates)
        run.retrieved_citation_ids = [
            str(source.citation_id) for source in sources if source.citation_id is not None
        ]
        run.input_sha256 = self._input_hash(question, prompt_hash, sources)

        if insufficiency or not sources:
            reason = insufficiency or "No verified public source matched the question."
            self._withhold(
                run,
                [ValidationError("DOCUMENT_NOT_FOUND", reason)],
                insufficient=True,
                structured={"claims": [], "abstention": reason},
            )
            self.session.commit()
            return self.get_run(run.id) or run

        provider_sources = tuple(self._provider_source(source) for source in sources)
        try:
            response = self.provider.generate(
                ProviderRequest(
                    question=question,
                    system_prompt=prompt,
                    sources=provider_sources,
                    temperature=self.settings.ai_temperature,
                )
            )
        except ProviderError as exc:
            run.status = AiRunStatus.FAILED
            run.answer_withheld = True
            run.error = str(exc)
            run.validation_errors = [
                ValidationError("UNSUPPORTED_CLAIM", "provider generation failed").as_dict()
            ]
            run.finished_at = datetime.now(UTC)
            self.session.commit()
            return self.get_run(run.id) or run

        errors = validate_response(response, provider_sources)
        run.structured_output = _response_dict(response)
        run.input_tokens = response.input_tokens
        run.output_tokens = response.output_tokens
        abstentions = [claim for claim in response.claims if claim.content_type == "abstention"]
        if not errors and abstentions:
            reason = " ".join(claim.text for claim in abstentions)
            self._withhold(
                run,
                [ValidationError("DOCUMENT_NOT_FOUND", reason)],
                insufficient=True,
                structured=run.structured_output,
            )
        elif errors:
            self._withhold(run, list(errors), insufficient=False, structured=run.structured_output)
        else:
            self._persist_outputs(run, response, sources)
            run.status = AiRunStatus.COMPLETED
            run.finished_at = datetime.now(UTC)
            run.validation_errors = []
        self.session.commit()
        return self.get_run(run.id) or run

    def get_run(self, run_id: uuid.UUID) -> AiRun | None:
        return self.session.scalar(
            select(AiRun)
            .where(AiRun.id == run_id, AiRun.case_id == self.case.id)
            .options(
                selectinload(AiRun.retrieval_sources),
                selectinload(AiRun.prompt_version),
                selectinload(AiRun.outputs).selectinload(AiOutput.sources),
                selectinload(AiRun.outputs).selectinload(AiOutput.citations),
            )
        )

    def list_runs(self, limit: int = 20) -> list[AiRun]:
        return list(
            self.session.scalars(
                select(AiRun)
                .where(AiRun.case_id == self.case.id)
                .options(
                    selectinload(AiRun.prompt_version),
                    selectinload(AiRun.retrieval_sources),
                    selectinload(AiRun.outputs),
                )
                .order_by(AiRun.created_at.desc())
                .limit(limit)
            ).all()
        )

    def save_research_note(
        self, run_id: uuid.UUID, title: str, *, author: str = "research-user"
    ) -> ResearchNote:
        run = self.get_run(run_id)
        if run is None:
            raise LookupError("AI run not found")
        if run.answer_withheld or not run.outputs:
            raise ValueError("withheld or empty AI output cannot be saved")
        body = "\n\n".join(f"[{output.kind.value}] {output.text}" for output in run.outputs)
        citations = {
            citation.id: citation for output in run.outputs for citation in output.citations
        }
        note = ResearchNote(
            case_id=self.case.id,
            author=author,
            title=title.strip(),
            body=body,
            provenance="ai_assisted",
            origin_ai_run_id=run.id,
            citations=list(citations.values()),
        )
        self.session.add(note)
        self.session.commit()
        self.session.refresh(note)
        return note

    def _prompt(self) -> tuple[str, str]:
        path = Path(self.settings.ai_prompt_dir) / PROMPT_FILE
        text = path.read_text(encoding="utf-8")
        return text, hashlib.sha256(text.encode()).hexdigest()

    def _prompt_version(self, template: str, digest: str) -> PromptVersion:
        row = self.session.scalar(
            select(PromptVersion).where(
                PromptVersion.name == PROMPT_NAME, PromptVersion.version == PROMPT_VERSION
            )
        )
        if row is None:
            row = PromptVersion(
                name=PROMPT_NAME,
                version=PROMPT_VERSION,
                template=template,
                template_sha256=digest,
            )
            self.session.add(row)
            self.session.flush()
        elif row.template_sha256 != digest or row.template != template:
            raise RuntimeError("versioned prompt content changed without a version bump")
        return row

    def _known_insufficiency(self, question: str) -> str | None:
        lowered = question.casefold()
        if "trial judgment" in lowered:
            has_trial_judgment = self.session.scalar(
                select(func.count())
                .select_from(Document)
                .where(
                    Document.case_id == self.case.id,
                    public_visibility(Document.visibility),
                    Document.document_type.ilike("%judgment%"),
                )
            )
            if not has_trial_judgment:
                return "The controlled corpus does not contain the public Trial Judgment."
        requested = {match.upper() for match in _RECORD_REF.findall(question)}
        for filing in sorted(requested):
            exists = self.session.scalar(
                select(func.count())
                .select_from(Document)
                .where(Document.case_id == self.case.id, Document.filing_number == filing)
            )
            if not exists:
                return f"The controlled corpus does not contain the requested filing {filing}."
        return None

    def _retrieve(self, question: str) -> list[Candidate]:
        tokens = _query_tokens(question)
        if not tokens:
            return []
        candidates = [*self._structured_candidates(tokens), *self._lexical_candidates(tokens)]
        deduplicated: dict[tuple[str, uuid.UUID], Candidate] = {}
        for candidate in candidates:
            key = (candidate.anchor_kind, candidate.anchor_id)
            current = deduplicated.get(key)
            if current is None or candidate.score > current.score:
                deduplicated[key] = candidate
        ordered = sorted(
            deduplicated.values(), key=lambda item: (-item.score, item.category, item.ref)
        )
        return ordered[:MAX_SOURCES]

    def _structured_candidates(self, tokens: tuple[str, ...]) -> list[Candidate]:
        result: list[Candidate] = []
        findings = self.session.scalars(
            select(Finding)
            .join(Document, Finding.judgment_document_id == Document.id)
            .where(
                Finding.case_id == self.case.id,
                Finding.verification_state != VerificationState.HUMAN_REJECTED,
                public_visibility(Document.visibility),
                or_(*[Finding.text.ilike(f"%{token}%") for token in tokens]),
            )
            .options(
                selectinload(Finding.judgment_document),
                selectinload(Finding.judgment_version),
                selectinload(Finding.citation),
            )
        ).all()
        for finding in findings:
            version = finding.judgment_version
            citation = finding.citation
            if (
                version is None
                or citation is None
                or citation.resolution_state != ResolutionState.RESOLVED
            ):
                continue
            result.append(
                Candidate(
                    anchor_kind="finding",
                    anchor_id=finding.id,
                    document_version_id=version.id,
                    citation_id=citation.id,
                    category="court_finding",
                    visibility=version.visibility.value,
                    ref=finding.judgment_document.official_ref,
                    version_ref=version.official_version_ref,
                    display=_display(
                        version.official_version_ref,
                        para=finding.para_from,
                        para_to=finding.para_to,
                    ),
                    target_path=_document_path(
                        finding.judgment_document,
                        version,
                        pdf_page=citation.target_pdf_page_index,
                        para=finding.para_from,
                    ),
                    source_url=version.source_url,
                    text=finding.text,
                    page_from=citation.target_page,
                    pdf_page_index=citation.target_pdf_page_index,
                    para_from=finding.para_from,
                    para_to=finding.para_to,
                    verification=finding.verification_state.value,
                    verification_reviewed_by=finding.verified_by,
                    verification_reviewed_at=finding.verified_at,
                    method="structured_verified",
                    score=Decimal("100") + _match_score(finding.text, tokens),
                    metadata={"finding_key": finding.finding_key},
                )
            )

        arguments = self.session.scalars(
            select(Argument)
            .join(Document, Argument.document_id == Document.id)
            .where(
                Argument.case_id == self.case.id,
                Argument.verification_state != VerificationState.HUMAN_REJECTED,
                public_visibility(Document.visibility),
                or_(*[Argument.text.ilike(f"%{token}%") for token in tokens]),
            )
            .options(
                selectinload(Argument.document),
                selectinload(Argument.document_version),
                selectinload(Argument.citation),
            )
        ).all()
        for argument in arguments:
            version = argument.document_version
            citation = argument.citation
            document = argument.document
            if (
                version is None
                or document is None
                or citation is None
                or citation.resolution_state != ResolutionState.RESOLVED
            ):
                continue
            category = {
                Party.SPO: "spo_argument",
                Party.DEFENCE: "defence_argument",
                Party.COURT: "court_response",
            }.get(argument.party)
            if category is None:
                continue
            result.append(
                Candidate(
                    anchor_kind="argument",
                    anchor_id=argument.id,
                    document_version_id=version.id,
                    citation_id=citation.id,
                    category=category,
                    visibility=version.visibility.value,
                    ref=document.official_ref,
                    version_ref=version.official_version_ref,
                    display=_display(
                        version.official_version_ref,
                        para=argument.para_from,
                        para_to=argument.para_to,
                    ),
                    target_path=_document_path(
                        document,
                        version,
                        pdf_page=citation.target_pdf_page_index,
                        para=argument.para_from,
                    ),
                    source_url=version.source_url,
                    text=argument.text,
                    page_from=citation.target_page,
                    pdf_page_index=citation.target_pdf_page_index,
                    para_from=argument.para_from,
                    para_to=argument.para_to,
                    verification=argument.verification_state.value,
                    verification_reviewed_by=argument.verified_by,
                    verification_reviewed_at=argument.verified_at,
                    method="structured_verified",
                    score=Decimal("90") + _match_score(argument.text, tokens),
                    metadata={
                        "argument_key": argument.argument_key,
                        "source_scope": argument.source_scope,
                        "underlying_source_ref": argument.underlying_source_ref,
                    },
                )
            )
        return result

    def _lexical_candidates(self, tokens: tuple[str, ...]) -> list[Candidate]:
        query = " | ".join(tokens)
        tsquery = func.to_tsquery("simple", query)
        chunk_rank = func.ts_rank_cd(DocumentChunk.search_vector, tsquery)
        chunks = self.session.execute(
            select(DocumentChunk, DocumentVersion, Document, chunk_rank.label("rank"))
            .join(DocumentVersion, DocumentChunk.document_version_id == DocumentVersion.id)
            .join(Document, DocumentVersion.document_id == Document.id)
            .where(
                Document.case_id == self.case.id,
                Document.document_type != "transcript",
                public_visibility(Document.visibility),
                public_visibility(DocumentVersion.visibility),
                DocumentVersion.parse_requires_review.is_(False),
                DocumentChunk.search_vector.op("@@")(tsquery),
            )
            .order_by(chunk_rank.desc(), Document.official_ref, DocumentChunk.sequence)
            .limit(MAX_SOURCES)
        ).all()
        result = [
            Candidate(
                anchor_kind="document_chunk",
                anchor_id=chunk.id,
                document_version_id=version.id,
                citation_id=None,
                category="document_exhibit",
                visibility=version.visibility.value,
                ref=document.official_ref,
                version_ref=version.official_version_ref,
                display=_display(
                    version.official_version_ref,
                    page=chunk.page_from,
                    para=chunk.para_from,
                    para_to=chunk.para_to,
                ),
                target_path=_document_path(
                    document,
                    version,
                    pdf_page=chunk.pdf_page_index_from,
                    para=chunk.para_from,
                    page=chunk.page_from,
                ),
                source_url=version.source_url,
                text=_excerpt(chunk.text, tokens),
                page_from=chunk.page_from,
                page_to=chunk.page_to,
                pdf_page_index=chunk.pdf_page_index_from,
                para_from=chunk.para_from,
                para_to=chunk.para_to,
                method="lexical_fts",
                score=Decimal(str(rank or 0)),
                metadata={"document_type": document.document_type},
            )
            for chunk, version, document, rank in chunks
        ]

        segment_rank = func.ts_rank_cd(TranscriptSegment.search_vector, tsquery)
        segments = self.session.execute(
            select(
                TranscriptSegment,
                Transcript,
                DocumentVersion,
                Document,
                segment_rank.label("rank"),
            )
            .join(Transcript, TranscriptSegment.transcript_id == Transcript.id)
            .join(DocumentVersion, Transcript.document_version_id == DocumentVersion.id)
            .join(Document, DocumentVersion.document_id == Document.id)
            .where(
                Document.case_id == self.case.id,
                public_visibility(Document.visibility),
                public_visibility(DocumentVersion.visibility),
                public_visibility(Transcript.visibility),
                DocumentVersion.parse_requires_review.is_(False),
                TranscriptSegment.closed_session.is_(False),
                TranscriptSegment.search_vector.op("@@")(tsquery),
            )
            .order_by(segment_rank.desc(), Document.official_ref, TranscriptSegment.sequence)
            .limit(MAX_SOURCES)
        ).all()
        for segment, transcript, version, document, rank in segments:
            category = "witness_testimony" if segment.witness_id is not None else "document_exhibit"
            ref = transcript.official_ref or document.official_ref
            result.append(
                Candidate(
                    anchor_kind="transcript_segment",
                    anchor_id=segment.id,
                    document_version_id=version.id,
                    citation_id=None,
                    category=category,
                    visibility=version.visibility.value,
                    ref=ref,
                    version_ref=version.official_version_ref,
                    display=_display(
                        version.official_version_ref,
                        page=segment.page_number,
                        line=segment.line_from,
                        line_to=segment.line_to,
                    ),
                    target_path=_document_path(
                        document,
                        version,
                        pdf_page=segment.pdf_page_index,
                        page=segment.page_number,
                        line=segment.line_from,
                    ),
                    source_url=version.source_url,
                    text=_excerpt(segment.text, tokens),
                    page_from=segment.page_number,
                    pdf_page_index=segment.pdf_page_index,
                    line_from=segment.line_from,
                    line_to=segment.line_to,
                    method="lexical_fts",
                    score=Decimal(str(rank or 0)),
                    metadata={
                        "speaker": segment.speaker,
                        "speaker_role": segment.speaker_role,
                        "witness_reference": "code_only" if segment.witness_id else None,
                    },
                )
            )
        return result

    def _persist_sources(self, run: AiRun, candidates: list[Candidate]) -> list[AiRetrievalSource]:
        result: list[AiRetrievalSource] = []
        for rank, candidate in enumerate(candidates, start=1):
            anchors: dict[str, uuid.UUID | None] = {
                "document_paragraph_id": None,
                "document_chunk_id": None,
                "transcript_segment_id": None,
                "finding_id": None,
                "argument_id": None,
                "research_note_id": None,
            }
            anchors[f"{candidate.anchor_kind}_id"] = candidate.anchor_id
            row = AiRetrievalSource(
                ai_run_id=run.id,
                rank=rank,
                retrieval_method=candidate.method,
                retrieval_score=candidate.score.quantize(_SCORE_SCALE),
                source_category=candidate.category,
                source_visibility=candidate.visibility,
                source_ref=candidate.ref,
                version_ref=candidate.version_ref,
                display=candidate.display,
                target_path=candidate.target_path,
                source_url=candidate.source_url,
                excerpt=candidate.text,
                excerpt_sha256=hashlib.sha256(candidate.text.encode()).hexdigest(),
                page_from=candidate.page_from,
                page_to=candidate.page_to,
                pdf_page_index=candidate.pdf_page_index,
                para_from=candidate.para_from,
                para_to=candidate.para_to,
                line_from=candidate.line_from,
                line_to=candidate.line_to,
                verification_state=candidate.verification,
                verification_reviewed_by=candidate.verification_reviewed_by,
                verification_reviewed_at=candidate.verification_reviewed_at,
                source_metadata=candidate.metadata,
                document_version_id=candidate.document_version_id,
                citation_id=candidate.citation_id,
                **anchors,
            )
            self.session.add(row)
            result.append(row)
        self.session.flush()
        return result

    def _persist_outputs(
        self, run: AiRun, response: ProviderResponse, sources: list[AiRetrievalSource]
    ) -> None:
        source_by_id = {str(source.id): source for source in sources}
        citation_ids: set[uuid.UUID]
        for sequence, claim in enumerate(response.claims):
            selected = [source_by_id[source_id] for source_id in claim.source_ids]
            output = AiOutput(
                ai_run_id=run.id,
                sequence=sequence,
                kind=AnswerBlockKind(claim.kind),
                text=claim.text,
                content_type=claim.content_type,
                claim_key=f"claim-{sequence + 1}",
                unresolved_citation_count=0,
                verification_state=VerificationState.AI_FLAGGED,
                sources=selected,
            )
            citation_ids = {
                source.citation_id for source in selected if source.citation_id is not None
            }
            if citation_ids:
                output.citations = list(
                    self.session.scalars(
                        select(Citation).where(Citation.id.in_(citation_ids))
                    ).all()
                )
            self.session.add(output)

    def _withhold(
        self,
        run: AiRun,
        errors: list[ValidationError],
        *,
        insufficient: bool,
        structured: dict[str, object] | None,
    ) -> None:
        run.status = AiRunStatus.COMPLETED
        run.answer_withheld = True
        run.insufficient_evidence = insufficient
        run.validation_errors = [error.as_dict() for error in errors]
        run.structured_output = structured
        run.finished_at = datetime.now(UTC)

    @staticmethod
    def _provider_source(source: AiRetrievalSource) -> ProviderSource:
        return ProviderSource(
            id=str(source.id),
            category=source.source_category,
            ref=source.source_ref,
            citation=source.display,
            text=source.excerpt,
        )

    @staticmethod
    def _input_hash(question: str, prompt_hash: str, sources: list[AiRetrievalSource]) -> str:
        canonical = json.dumps(
            {
                "question": question,
                "prompt_sha256": prompt_hash,
                "sources": [
                    {"id": str(source.id), "excerpt_sha256": source.excerpt_sha256}
                    for source in sources
                ],
            },
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode()).hexdigest()


def provider_from_settings(settings: Settings) -> AiProvider:
    provider = settings.ai_provider.casefold() or "deterministic"
    if provider == "deterministic":
        return DeterministicExtractiveProvider()
    if provider == "openai_compatible":
        return OpenAiCompatibleProvider(
            endpoint=settings.openai_compatible_url,
            api_key=settings.openai_api_key,
            model=settings.ai_model,
        )
    if provider == "anthropic_compatible":
        return AnthropicCompatibleProvider(
            endpoint=settings.anthropic_compatible_url,
            api_key=settings.anthropic_api_key,
            model=settings.ai_model,
        )
    raise ProviderError(f"unsupported AI provider: {settings.ai_provider}")


def _query_tokens(question: str) -> tuple[str, ...]:
    values: list[str] = []
    for match in _WORD.findall(question.casefold()):
        token = re.sub(r"[^a-z0-9_]", "", match)
        if len(token) >= 3 and token not in _STOPWORDS and token not in values:
            values.append(token)
    return tuple(values[:12])


def _match_score(text: str, tokens: tuple[str, ...]) -> Decimal:
    lowered = text.casefold()
    matched = sum(token in lowered for token in tokens)
    return Decimal(matched) / Decimal(max(len(tokens), 1))


def _excerpt(text: str, tokens: tuple[str, ...], width: int = 1200) -> str:
    compact = " ".join(text.split())
    if len(compact) <= width:
        return compact
    positions = [compact.casefold().find(token) for token in tokens]
    positions = [position for position in positions if position >= 0]
    start = max(0, (min(positions) if positions else 0) - 240)
    return compact[start : start + width].strip()


def _display(
    version_ref: str,
    *,
    page: int | None = None,
    para: int | None = None,
    para_to: int | None = None,
    line: int | None = None,
    line_to: int | None = None,
) -> str:
    # Keep the complete persisted version reference. Shortening to the final
    # slash-delimited token can make a coordinate ambiguous (for example RED2).
    ref = version_ref
    if para is not None:
        extent = str(para) if para_to in (None, para) else f"{para}–{para_to}"  # noqa: RUF001
        return f"{ref} · ¶{extent}"
    if page is not None and line is not None:
        extent = str(line) if line_to in (None, line) else f"{line}–{line_to}"  # noqa: RUF001
        return f"T. {page}:{extent}"
    if page is not None:
        return f"{ref} · p. {page}"
    return ref


def _document_path(
    document: Document,
    version: DocumentVersion,
    *,
    pdf_page: int | None = None,
    para: int | None = None,
    page: int | None = None,
    line: int | None = None,
) -> str:
    route_id = document.official_ref.split("/", 1)[-1]
    if "/" in route_id:
        path = "/documents/transcript"
        params = [f"document={quote(route_id, safe='')}"]
    else:
        path = f"/documents/{quote(route_id, safe='')}"
        params = []
    params.append(f"version={quote(version.official_version_ref, safe='')}")
    if pdf_page is not None:
        params.append(f"pdfPage={pdf_page}")
    if para is not None:
        params.append(f"para={para}")
    if page is not None:
        params.append(f"page={page}")
    if line is not None:
        params.append(f"line={line}")
    return f"{path}?{'&'.join(params)}"


def _response_dict(response: ProviderResponse) -> dict[str, object]:
    return {
        "claims": [
            {
                "kind": claim.kind,
                "text": claim.text,
                "content_type": claim.content_type,
                "source_ids": list(claim.source_ids),
            }
            for claim in response.claims
        ]
    }
