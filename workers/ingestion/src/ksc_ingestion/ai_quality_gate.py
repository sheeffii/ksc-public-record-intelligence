"""Phase 11 deterministic evaluation against the controlled real corpus."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ksc_api.config import Settings
from ksc_api.models import (
    AiRun,
    Argument,
    Case,
    Citation,
    Document,
    DocumentVersion,
    Finding,
    FindingEvidenceLink,
    Relationship,
    SourceRecord,
)
from ksc_api.services.ai_providers import DeterministicExtractiveProvider
from ksc_api.services.ai_research import AiResearchService

_PUBLIC = {"public", "public_redacted"}
_VERIFIED_MODELS = (Citation, Finding, FindingEvidenceLink, Argument, Relationship)


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    question: str
    should_answer: bool
    expected_categories: tuple[str, ...]
    expected_error: str | None


@dataclass(frozen=True)
class EvaluationResult:
    id: str
    answer_withheld: bool
    sources: int
    answer_blocks: int
    claim_source_links: int
    categories: list[str]
    citation_correct: bool
    source_categories_correct: bool
    quotes_accurate: bool
    exact_source_navigation: bool
    abstention_correct: bool
    validation_flags: list[str]
    passed: bool


@dataclass(frozen=True)
class Phase11QualityReport:
    phase: int
    generated_at: str
    case_number: str
    input_manifest: str
    input_manifest_sha256: str
    evaluation_set: str
    evaluation_set_sha256: str
    controlled_records: int
    provider: str
    model: str
    prompt_version: int
    system_prompt_sha256: str
    evaluation_cases: int
    grounded_answer_cases: int
    expected_abstention_cases: int
    correctly_abstained_cases: int
    persisted_audited_runs: int
    retrieved_sources: int
    validated_claim_source_links: int
    unsupported_claims_rendered: int
    citation_correctness_rate: float
    source_category_correctness_rate: float
    quote_accuracy_rate: float
    exact_source_navigation_rate: float
    abstention_quality_rate: float
    source_records_unchanged: bool
    human_verification_unchanged: bool
    trial_judgment_present: bool
    missing_official_material: list[str]
    results: list[EvaluationResult]
    passed: bool


def load_evaluation_set(path: Path) -> tuple[str, int, tuple[EvaluationCase, ...]]:
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("phase") != 11:
        raise ValueError("Phase 11 evaluation set is invalid")
    case_number = payload.get("case_number")
    expected_records = payload.get("controlled_records")
    raw_cases = payload.get("cases")
    if not isinstance(case_number, str) or not isinstance(expected_records, int):
        raise ValueError("evaluation corpus metadata is invalid")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("evaluation set must contain cases")
    cases: list[EvaluationCase] = []
    for item in raw_cases:
        if not isinstance(item, dict):
            raise ValueError("evaluation case must be an object")
        expected_categories = item.get("expected_categories")
        if not isinstance(expected_categories, list) or not all(
            isinstance(value, str) for value in expected_categories
        ):
            raise ValueError("evaluation categories are invalid")
        cases.append(
            EvaluationCase(
                id=str(item["id"]),
                question=str(item["question"]),
                should_answer=bool(item["should_answer"]),
                expected_categories=tuple(expected_categories),
                expected_error=(
                    str(item["expected_error"]) if item.get("expected_error") is not None else None
                ),
            )
        )
    return case_number, expected_records, tuple(cases)


def run_phase11_gate(
    session: Session,
    settings: Settings,
    *,
    manifest_path: Path,
    evaluation_path: Path,
    generated_at: str,
) -> Phase11QualityReport:
    case_number, expected_records, cases = load_evaluation_set(evaluation_path)
    if settings.case_id != case_number:
        raise RuntimeError(
            f"configured case {settings.case_id} does not match evaluation case {case_number}"
        )
    case = session.scalar(select(Case).where(Case.case_number == case_number))
    if case is None:
        raise RuntimeError(f"case {case_number} is not seeded")

    manifest_bytes = manifest_path.read_bytes()
    manifest: Any = json.loads(manifest_bytes)
    approved_versions = {
        record["official_version_ref"]: record["sha256"]
        for record in manifest["records"]
        if record.get("artifact_status") == "fetched"
    }
    persisted_versions = {
        row.id: (row.official_version_ref, row.sha256)
        for row in session.scalars(select(DocumentVersion)).all()
    }
    controlled_records = (
        session.scalar(
            select(func.count()).select_from(SourceRecord).where(SourceRecord.case_id == case.id)
        )
        or 0
    )
    source_before = _source_fingerprint(session, case.id)
    verification_before = _verification_fingerprint(session)

    provider = DeterministicExtractiveProvider()
    results: list[EvaluationResult] = []
    runs: list[AiRun] = []
    for evaluation in cases:
        run = AiResearchService(session, case, settings, provider=provider).create_run(
            evaluation.question, requested_by="phase11-quality-gate"
        )
        runs.append(run)
        flags = [str(item.get("code")) for item in run.validation_errors or []]
        categories = sorted({source.source_category for source in run.retrieval_sources})
        source_ids = {source.id for source in run.retrieval_sources}
        citation_correct = all(
            source.source_visibility in _PUBLIC
            and source.version_ref in approved_versions
            and source.document_version_id in persisted_versions
            and persisted_versions[source.document_version_id]
            == (source.version_ref, approved_versions[source.version_ref])
            and hashlib.sha256(source.excerpt.encode()).hexdigest() == source.excerpt_sha256
            for source in run.retrieval_sources
        ) and all(linked.id in source_ids for output in run.outputs for linked in output.sources)
        source_categories_correct = set(evaluation.expected_categories).issubset(categories)
        quoted = [output for output in run.outputs if output.content_type == "verbatim_quote"]
        quotes_accurate = all(
            any(_normalise(output.text) == _normalise(source.excerpt) for source in output.sources)
            for output in quoted
        )
        exact_navigation = all(
            bool(source.target_path)
            and any(
                coordinate is not None
                for coordinate in (source.page_from, source.para_from, source.line_from)
            )
            for source in run.retrieval_sources
        )
        abstention_correct = (
            not evaluation.should_answer
            and run.answer_withheld
            and not run.outputs
            and evaluation.expected_error in flags
        ) or evaluation.should_answer
        answered_correctly = (
            evaluation.should_answer
            and not run.answer_withheld
            and bool(run.outputs)
            and citation_correct
            and source_categories_correct
            and quotes_accurate
            and exact_navigation
            and not flags
        )
        passed = answered_correctly or (
            not evaluation.should_answer and abstention_correct and not run.retrieval_sources
        )
        results.append(
            EvaluationResult(
                id=evaluation.id,
                answer_withheld=run.answer_withheld,
                sources=len(run.retrieval_sources),
                answer_blocks=len(run.outputs),
                claim_source_links=sum(len(output.sources) for output in run.outputs),
                categories=categories,
                citation_correct=citation_correct,
                source_categories_correct=source_categories_correct,
                quotes_accurate=quotes_accurate,
                exact_source_navigation=exact_navigation,
                abstention_correct=abstention_correct,
                validation_flags=flags,
                passed=passed,
            )
        )

    source_unchanged = source_before == _source_fingerprint(session, case.id)
    verification_unchanged = verification_before == _verification_fingerprint(session)
    answered = [result for result, item in zip(results, cases, strict=True) if item.should_answer]
    abstained = [
        result for result, item in zip(results, cases, strict=True) if not item.should_answer
    ]
    trial_judgment_present = (
        session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.case_id == case.id, func.lower(Document.document_type) == "judgment")
        )
        or 0
    ) > 0
    report_passed = all(result.passed for result in results) and all(
        (controlled_records == expected_records, source_unchanged, verification_unchanged)
    )
    return Phase11QualityReport(
        phase=11,
        generated_at=generated_at,
        case_number=case_number,
        input_manifest=str(manifest_path),
        input_manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        evaluation_set=str(evaluation_path),
        evaluation_set_sha256=hashlib.sha256(evaluation_path.read_bytes()).hexdigest(),
        controlled_records=controlled_records,
        provider=provider.name,
        model=provider.model,
        prompt_version=runs[0].prompt_version.version if runs[0].prompt_version else 0,
        system_prompt_sha256=runs[0].system_prompt_sha256 or "",
        evaluation_cases=len(cases),
        grounded_answer_cases=len(answered),
        expected_abstention_cases=len(abstained),
        correctly_abstained_cases=sum(result.abstention_correct for result in abstained),
        persisted_audited_runs=len(runs),
        retrieved_sources=sum(len(run.retrieval_sources) for run in runs),
        validated_claim_source_links=sum(
            len(output.sources) for run in runs for output in run.outputs
        ),
        unsupported_claims_rendered=sum(
            bool(run.validation_errors) and bool(run.outputs) for run in runs
        ),
        citation_correctness_rate=_rate(answered, "citation_correct"),
        source_category_correctness_rate=_rate(answered, "source_categories_correct"),
        quote_accuracy_rate=_rate(answered, "quotes_accurate"),
        exact_source_navigation_rate=_rate(answered, "exact_source_navigation"),
        abstention_quality_rate=_rate(abstained, "abstention_correct"),
        source_records_unchanged=source_unchanged,
        human_verification_unchanged=verification_unchanged,
        trial_judgment_present=trial_judgment_present,
        missing_official_material=[
            "Public Trial Judgment for KSC-BC-2020-06",
            "Underlying public party filing F03743",
            "Underlying public party filing F03746",
        ],
        results=results,
        passed=report_passed,
    )


def write_phase11_report(report: Phase11QualityReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2) + "\n", encoding="utf-8")


def _normalise(value: str) -> str:
    return " ".join(value.split())


def _rate(results: list[EvaluationResult], field: str) -> float:
    if not results:
        return 1.0
    return sum(bool(getattr(result, field)) for result in results) / len(results)


def _source_fingerprint(session: Session, case_id: Any) -> str:
    rows: list[str] = []
    for model in (SourceRecord, Document, DocumentVersion):
        statement = select(model.id, model.updated_at).order_by(model.id)
        if model is SourceRecord or model is Document:
            statement = statement.where(model.case_id == case_id)
        rows.extend(
            f"{model.__tablename__}:{row.id}:{row.updated_at}" for row in session.execute(statement)
        )
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


def _verification_fingerprint(session: Session) -> str:
    rows: list[str] = []
    for model in _VERIFIED_MODELS:
        statement = select(
            model.id, model.verification_state, model.verified_by, model.verified_at
        ).order_by(model.id)
        rows.extend(
            f"{model.__tablename__}:{row.id}:{row.verification_state}:"
            f"{row.verified_by}:{row.verified_at}"
            for row in session.execute(statement)
        )
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()
