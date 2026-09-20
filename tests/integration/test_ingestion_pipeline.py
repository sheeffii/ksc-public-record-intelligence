"""End-to-end ingestion of synthetic capture bundles into the demo case:
persistence, provenance, hashing, object storage, versions, public-only
enforcement, duplicate handling, idempotent re-runs, resume after a crash,
metadata-only records and visible failures.

Everything ingested here is the synthetic `KSC-DEMO-0000` corpus from
tests/support/synthetic.py — no real KSC record is involved.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from pathlib import Path

import httpx
import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ksc_api.models import (
    ArtifactStatus,
    AuditLog,
    Case,
    Document,
    DocumentIngestionState,
    DocumentVersion,
    DocumentVersionType,
    Hearing,
    IngestionItemStatus,
    IngestionJob,
    IngestionJobItem,
    IngestionJobStatus,
    Party,
    SourceRecord,
    SourceSystem,
    Transcript,
    Visibility,
)
from ksc_ingestion.capture import load_bundle
from ksc_ingestion.fetch import HttpFetcher
from ksc_ingestion.pipeline import CaseNotSeededError, Ingestor
from ksc_ingestion.probe import JOB_TYPE_LIVE_PROBE, probe, record_probe
from ksc_ingestion.storage import InMemoryObjectStore, MinioObjectStore, ObjectStore
from support.synthetic import (
    DEMO_CASE,
    BundleBuilder,
    artifact_url,
    make_pdf,
    metadata,
    standard_bundle,
)

pytestmark = pytest.mark.integration

TEST_BUCKET = "ksc-documents-test"


def _clean(session: Session) -> None:
    case = session.scalar(select(Case).where(Case.case_number == DEMO_CASE))
    if case is None:
        return
    session.execute(delete(IngestionJob).where(IngestionJob.case_id == case.id))
    session.execute(
        delete(SourceRecord).where(
            SourceRecord.case_id == case.id, SourceRecord.external_record_id.notlike("DEMO-%")
        )
    )
    docs = session.scalars(
        select(Document).where(
            Document.case_id == case.id,
            Document.official_ref.notlike(f"{DEMO_CASE}/%-DEMO-%"),
        )
    ).all()
    version_ids = [v.id for d in docs for v in d.versions]
    if version_ids:
        session.execute(delete(Transcript).where(Transcript.document_version_id.in_(version_ids)))
    for d in docs:
        session.delete(d)
    session.execute(
        delete(Hearing).where(Hearing.case_id == case.id, Hearing.hearing_date >= date(2024, 1, 1))
    )
    session.commit()


@pytest.fixture
def sessions(demo_settings):
    from ksc_api.db.session import get_sessionmaker

    factory = get_sessionmaker()
    with factory() as session:
        _clean(session)
    yield factory
    with factory() as session:
        _clean(session)


@pytest.fixture
def store(demo_settings) -> ObjectStore:
    minio = MinioObjectStore(demo_settings, bucket=TEST_BUCKET)
    minio.ensure_bucket()
    return minio


@pytest.fixture
def ingestor(sessions, store: ObjectStore) -> Ingestor:
    return Ingestor(sessions, store, case_number=DEMO_CASE)


@pytest.fixture
def session(sessions) -> Iterator[Session]:
    with sessions() as s:
        yield s


def _doc(session: Session, ref: str) -> Document:
    doc = session.scalar(select(Document).where(Document.official_ref == f"{DEMO_CASE}/{ref}"))
    assert doc is not None, ref
    return doc


def _versions(session: Session, ref: str) -> dict[str, DocumentVersion]:
    return {v.official_version_ref: v for v in _doc(session, ref).versions}


def _items(session: Session, job_id: str) -> dict[str, IngestionJobItem]:
    items = session.scalars(select(IngestionJobItem).where(IngestionJobItem.job_id == job_id)).all()
    return {i.item_key.split(":")[-1]: i for i in items}


# ------------------------------------------------------------------ core --
def test_standard_bundle_persists_records_provenance_hashes_and_failures(
    tmp_path: Path, ingestor: Ingestor, session: Session, store: ObjectStore
) -> None:
    outcome = ingestor.run_bundle(load_bundle(standard_bundle(tmp_path)))

    assert outcome.status is IngestionJobStatus.COMPLETED
    assert not outcome.resumed
    by_key = {i.item_key.split(":")[-1]: i for i in outcome.items}
    assert by_key["00000000000000a1"].status is IngestionItemStatus.DOWNLOADED
    assert by_key["00000000000000a2"].status is IngestionItemStatus.DOWNLOADED
    assert by_key["00000000000000a3"].status is IngestionItemStatus.METADATA_ONLY
    assert by_key["00000000000000a4"].status is IngestionItemStatus.DOWNLOADED
    assert by_key["00000000000000a5"].status is IngestionItemStatus.NOT_PUBLIC
    assert by_key["00000000000000a6"].status is IngestionItemStatus.UNSUPPORTED_ARTIFACT
    assert by_key["00000000000000a7"].status is IngestionItemStatus.DOWNLOADED
    assert outcome.downloaded_artifacts == 5

    # job row and items
    job = session.get(IngestionJob, outcome.job_id)
    assert job is not None
    assert job.status is IngestionJobStatus.COMPLETED
    assert job.job_type == "capture_bundle"
    assert job.cursor["bundle_id"] == "synthetic-demo-01"
    assert (job.discovered_count, job.downloaded_count, job.processed_count, job.failed_count) == (
        7,
        5,
        7,
        1,
    )
    assert job.checkpoint["last_item_key"].endswith("00000000000000a7")
    assert job.error_summary and "00000000000000a6: unsupported_artifact" in job.error_summary
    items = _items(session, outcome.job_id)
    assert items["00000000000000a6"].reason == "not a PDF (magic bytes)"
    assert (
        items["00000000000000a5"].reason and "nothing fetched" in items["00000000000000a5"].reason
    )
    assert items["00000000000000a1"].detail["versions"][1]["status"] == "downloaded"

    # a1: original + public redacted version, both held, linked, distinct
    doc = _doc(session, "F00001")
    assert doc.filing_number == "F00001"
    assert doc.filing_party is Party.SPO
    assert doc.filing_date == date(2020, 5, 28) and doc.document_date is None
    assert doc.visibility is Visibility.PUBLIC
    assert doc.ingestion_state is DocumentIngestionState.DOWNLOADED
    assert doc.source_url.startswith(
        "https://repository.scp-ks.org/details.php?doc_id=00000000000000a1"
    )
    versions = _versions(session, "F00001")
    orig, red = versions[f"{DEMO_CASE}/F00001"], versions[f"{DEMO_CASE}/F00001/RED"]
    assert (
        orig.version_type is DocumentVersionType.ORIGINAL and orig.visibility is Visibility.PUBLIC
    )
    assert red.version_type is DocumentVersionType.PUBLIC_REDACTED
    assert red.visibility is Visibility.PUBLIC_REDACTED and red.version_label == "RED"
    for v in (orig, red):
        assert v.artifact_status is ArtifactStatus.FETCHED
        assert v.sha256 and len(v.sha256) == 64
        assert (
            v.storage_key
            == f"documents/{DEMO_CASE}/{DEMO_CASE}_F00001{'_RED' if v is red else ''}/{v.sha256}.pdf"
        )
        assert store.exists(v.storage_key)
        assert v.mime_type == "application/pdf" and v.page_count == 1 and v.byte_size
        assert v.fetch_method == "operator_browser_capture"
        assert v.fetched_at is not None and v.fetched_at.year == 2026
        assert v.source_url == artifact_url(
            "Filing", "F00001.pdf" if v is orig else "F00001-RED.pdf"
        )
    assert orig.sha256 != red.sha256

    # a3: metadata-only version — official URLs, no bytes
    (meta_only,) = _versions(session, "F00003").values()
    assert meta_only.artifact_status is ArtifactStatus.NOT_FETCHED
    assert meta_only.sha256 is None and meta_only.storage_key is None
    assert meta_only.source_url == artifact_url("Filing", "F00003.pdf")
    assert _doc(session, "F00003").ingestion_state is DocumentIngestionState.DISCOVERED
    assert _doc(session, "F00003").filing_party is Party.COURT

    # a4: transcript → hearing + transcript linked to the held version
    hearing = session.scalar(select(Hearing).where(Hearing.hearing_date == date(2024, 11, 25)))
    assert hearing is not None and hearing.hearing_type == "trial"
    (t_version,) = _versions(session, "T/2024-11-25").values()
    transcript = session.scalar(
        select(Transcript).where(Transcript.document_version_id == t_version.id)
    )
    assert transcript is not None and transcript.hearing_id == hearing.id
    assert transcript.visibility is Visibility.PUBLIC_REDACTED

    # a5: confidential → stated, never fetched
    conf = _doc(session, "F00005")
    assert conf.visibility is Visibility.NOT_PUBLIC and conf.versions == []

    # a6: unsupported bytes → version FAILED, nothing stored
    (failed,) = _versions(session, "F00006").values()
    assert failed.artifact_status is ArtifactStatus.FAILED and failed.sha256 is None

    # a7: Albanian translation is a second version of F00002
    versions = _versions(session, "F00002")
    assert set(versions) == {f"{DEMO_CASE}/F00002", f"{DEMO_CASE}/F00002/ALB"}
    assert versions[f"{DEMO_CASE}/F00002/ALB"].version_type is DocumentVersionType.TRANSLATION

    # source records: discovery provenance separate from the entity
    sources = session.scalars(
        select(SourceRecord).where(SourceRecord.external_record_id.like("00000000000000a%"))
    ).all()
    assert len(sources) == 7
    a1_source = next(s for s in sources if s.external_record_id == "00000000000000a1")
    assert a1_source.source_system is SourceSystem.KSC_PUBLIC_COURT_RECORDS
    assert a1_source.discovery_url.startswith("https://repository.scp-ks.org/?icc_filters")
    assert a1_source.canonical_source_url == doc.source_url
    assert a1_source.document_id == doc.id and a1_source.document_version_id in {orig.id, red.id}
    assert a1_source.raw_metadata["capture"]["captured_by"] == "test operator"
    assert a1_source.raw_metadata["metadata_source"] == "synthetic_fixture"
    assert a1_source.visibility is Visibility.PUBLIC
    a4_source = next(s for s in sources if s.external_record_id == "00000000000000a4")
    assert a4_source.hearing_id == hearing.id and a4_source.transcript_id == transcript.id

    # audit trail carries identifiers, never text
    actions = session.scalars(
        select(AuditLog.action).where(AuditLog.detail["job_id"].astext == outcome.job_id)
    ).all()
    assert actions.count("ingestion.item.downloaded") == 4
    assert "ingestion.item.unsupported_artifact" in actions
    assert "ingestion.item.not_public" in actions


def test_rerun_is_idempotent(tmp_path: Path, ingestor: Ingestor, session: Session) -> None:
    bundle = load_bundle(standard_bundle(tmp_path))
    first = ingestor.run_bundle(bundle)
    second = ingestor.run_bundle(bundle)

    assert second.job_id != first.job_id  # the first job completed; a new one records the re-run
    assert not second.resumed
    statuses = {i.item_key.split(":")[-1]: i.status for i in second.items}
    assert statuses["00000000000000a1"] is IngestionItemStatus.SKIPPED_DUPLICATE
    assert statuses["00000000000000a2"] is IngestionItemStatus.SKIPPED_DUPLICATE
    assert statuses["00000000000000a3"] is IngestionItemStatus.METADATA_ONLY
    assert statuses["00000000000000a4"] is IngestionItemStatus.SKIPPED_DUPLICATE
    assert statuses["00000000000000a5"] is IngestionItemStatus.NOT_PUBLIC
    assert statuses["00000000000000a6"] is IngestionItemStatus.UNSUPPORTED_ARTIFACT
    assert second.downloaded_artifacts == 0

    docs = session.scalars(
        select(Document).where(Document.official_ref.like(f"{DEMO_CASE}/F0000%"))
    ).all()
    assert len(docs) == 5
    assert sum(len(d.versions) for d in docs) == 6
    assert (
        session.scalar(
            select(SourceRecord).where(SourceRecord.external_record_id == "00000000000000a1")
        )
        is not None
    )
    assert (
        len(
            session.scalars(
                select(SourceRecord).where(SourceRecord.external_record_id.like("00000000000000a%"))
            ).all()
        )
        == 7
    )
    assert session.get(IngestionJob, second.job_id).downloaded_count == 0


class ExplodingStore:
    """Wraps a store and fails on the Nth put — simulates a crash mid-run."""

    def __init__(self, inner: ObjectStore, explode_on_put: int) -> None:
        self.inner, self.explode_on, self.puts = inner, explode_on_put, 0

    def exists(self, key: str) -> bool:
        return self.inner.exists(key)

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self.puts += 1
        if self.puts == self.explode_on:
            raise RuntimeError("simulated storage outage")
        self.inner.put(key, data, content_type)


def test_crash_leaves_a_resumable_job(
    tmp_path: Path, sessions, store: ObjectStore, session: Session
) -> None:
    bundle = load_bundle(standard_bundle(tmp_path))
    crashing = Ingestor(sessions, ExplodingStore(store, explode_on_put=3), case_number=DEMO_CASE)
    with pytest.raises(RuntimeError, match="simulated"):
        crashing.run_bundle(bundle)

    job = session.scalar(
        select(IngestionJob).where(IngestionJob.cursor["bundle_id"].astext == "synthetic-demo-01")
    )
    assert job is not None and job.status is IngestionJobStatus.FAILED
    assert "unexpected error" in (job.error_summary or "")
    items = _items(session, str(job.id))
    assert items["00000000000000a1"].status is IngestionItemStatus.DOWNLOADED
    assert items["00000000000000a2"].status is IngestionItemStatus.PENDING  # rolled back
    assert all(
        items[k].status is IngestionItemStatus.PENDING
        for k in ("00000000000000a3", "00000000000000a7")
    )
    assert (
        session.scalar(select(Document).where(Document.official_ref == f"{DEMO_CASE}/F00002"))
        is None
    )
    session.expire_all()

    resumed = Ingestor(sessions, store, case_number=DEMO_CASE).run_bundle(bundle)
    assert resumed.job_id == str(job.id)
    assert resumed.resumed
    first = next(i for i in resumed.items if i.item_key.endswith("a1"))
    assert first.skipped_as_done and first.status is IngestionItemStatus.DOWNLOADED
    second = next(i for i in resumed.items if i.item_key.endswith("a2"))
    assert not second.skipped_as_done and second.status is IngestionItemStatus.DOWNLOADED
    session.expire_all()
    job = session.get(IngestionJob, job.id)
    assert job.status is IngestionJobStatus.COMPLETED
    assert (job.processed_count, job.downloaded_count, job.failed_count) == (7, 5, 1)
    assert len(_versions(session, "F00002")) == 2


def test_metadata_only_version_is_filled_by_a_later_capture(
    tmp_path: Path, ingestor: Ingestor, session: Session
) -> None:
    md = metadata(
        record_type="decision", official_ref=f"{DEMO_CASE}/F00010", title="Synthetic decision"
    )
    first = (
        BundleBuilder(tmp_path / "one", "meta-only")
        .add_record("00000000000000b1", md, [{"url": artifact_url("Filing", "F00010.pdf")}])
        .write()
    )
    ingestor.run_bundle(load_bundle(first))
    (v,) = _versions(session, "F00010").values()
    assert v.artifact_status is ArtifactStatus.NOT_FETCHED and v.source_url == artifact_url(
        "Filing", "F00010.pdf"
    )
    version_id = v.id
    session.expire_all()

    b = BundleBuilder(tmp_path / "two", "with-file")
    f = b.file("F00010.pdf", make_pdf([f"{DEMO_CASE}/F00010", "now captured"]))
    b.add_record(
        "00000000000000b1", md, [{"url": artifact_url("Filing", "F00010.pdf"), "file": f}]
    ).write()
    outcome = ingestor.run_bundle(load_bundle(b.root))
    assert outcome.items[0].status is IngestionItemStatus.DOWNLOADED
    (v,) = _versions(session, "F00010").values()
    assert v.id == version_id  # filled in place, not duplicated
    assert v.artifact_status is ArtifactStatus.FETCHED and v.sha256 and v.storage_key
    assert _doc(session, "F00010").ingestion_state is DocumentIngestionState.DOWNLOADED


def test_different_bytes_for_a_held_version_are_never_overwritten(
    tmp_path: Path, ingestor: Ingestor, session: Session
) -> None:
    md = metadata(
        record_type="filing", official_ref=f"{DEMO_CASE}/F00011", title="Synthetic filing"
    )
    b = BundleBuilder(tmp_path / "one", "bytes-a")
    f = b.file("a.pdf", make_pdf([f"{DEMO_CASE}/F00011", "version as first captured"]))
    b.add_record(
        "00000000000000c1", md, [{"url": artifact_url("Filing", "F00011.pdf"), "file": f}]
    ).write()
    ingestor.run_bundle(load_bundle(b.root))
    (held,) = _versions(session, "F00011").values()
    held_sha = held.sha256
    session.expire_all()

    b2 = BundleBuilder(tmp_path / "two", "bytes-b")
    f2 = b2.file("b.pdf", make_pdf([f"{DEMO_CASE}/F00011", "different bytes, same reference"]))
    b2.add_record(
        "00000000000000c1", md, [{"url": artifact_url("Filing", "F00011.pdf"), "file": f2}]
    ).write()
    outcome = ingestor.run_bundle(load_bundle(b2.root))
    (item,) = outcome.items
    assert item.status is IngestionItemStatus.AMBIGUOUS_MAPPING
    assert item.versions[0].detail["held_sha256"] == held_sha
    (held,) = _versions(session, "F00011").values()
    assert held.sha256 == held_sha
    assert session.get(IngestionJob, outcome.job_id).failed_count == 1


def test_identical_bytes_under_a_second_reference_are_a_duplicate_not_a_version(
    tmp_path: Path, ingestor: Ingestor, session: Session
) -> None:
    data = make_pdf([f"{DEMO_CASE}/F00012", "same bytes"])
    b = BundleBuilder(tmp_path, "dupes")
    f1 = b.file("one.pdf", data)
    f2 = b.file("two.pdf", data)
    b.add_record(
        "00000000000000d1",
        metadata(record_type="filing", official_ref=f"{DEMO_CASE}/F00012", title="first"),
        [{"url": artifact_url("Filing", "F00012.pdf"), "file": f1}],
    )
    b.add_record(
        "00000000000000d2",
        metadata(
            record_type="filing",
            official_ref=f"{DEMO_CASE}/F00013",
            title="second listing, same file",
        ),
        [{"url": artifact_url("Filing", "F00013.pdf"), "file": f2}],
    )
    b.write()
    outcome = ingestor.run_bundle(load_bundle(b.root))
    first, second = outcome.items
    assert first.status is IngestionItemStatus.DOWNLOADED
    assert second.status is IngestionItemStatus.SKIPPED_DUPLICATE
    assert second.versions[0].detail["duplicate_of"]["official_ref"] == f"{DEMO_CASE}/F00012"
    (dup,) = _versions(session, "F00013").values()
    assert dup.artifact_status is ArtifactStatus.NOT_FETCHED and dup.sha256 is None
    assert dup.source_url == artifact_url("Filing", "F00013.pdf")


def test_unknown_visibility_fails_closed(
    tmp_path: Path, ingestor: Ingestor, session: Session
) -> None:
    b = BundleBuilder(tmp_path, "unknown-vis")
    f = b.file("x.pdf", make_pdf([f"{DEMO_CASE}/F00014"]))
    b.add_record(
        "00000000000000e1",
        metadata(
            record_type="filing",
            official_ref=f"{DEMO_CASE}/F00014",
            title="no classification",
            classification=None,
        ),
        [{"url": artifact_url("Filing", "F00014.pdf"), "file": f}],
    ).write()
    (item,) = ingestor.run_bundle(load_bundle(b.root)).items
    assert item.status is IngestionItemStatus.NOT_PUBLIC
    doc = _doc(session, "F00014")
    assert doc.visibility is Visibility.UNKNOWN and doc.versions == []


def test_wrong_case_in_metadata_or_on_first_page_is_invalid(
    tmp_path: Path, ingestor: Ingestor, session: Session
) -> None:
    b = BundleBuilder(tmp_path, "wrong-case")
    other = b.file("other.pdf", make_pdf(["KSC-BC-2020-06/F00001", "names a different case"]))
    b.add_record(
        "00000000000000f1",
        metadata(
            record_type="filing",
            official_ref="KSC-BC-2020-06/F00001",
            title="t",
            case_number="KSC-BC-2020-06",
        ),
        [],
    )
    b.add_record(
        "00000000000000f2",
        metadata(record_type="filing", official_ref=f"{DEMO_CASE}/F00015", title="t"),
        [{"url": artifact_url("Filing", "F00015.pdf"), "file": other}],
    )
    b.write()
    first, second = ingestor.run_bundle(load_bundle(b.root)).items
    assert first.status is IngestionItemStatus.INVALID_METADATA and "scoped to" in (
        first.reason or ""
    )
    assert (
        second.status is IngestionItemStatus.INVALID_METADATA
        and "first page names KSC-BC-2020-06" in (second.reason or "")
    )
    assert (
        session.scalar(select(Document).where(Document.official_ref == "KSC-BC-2020-06/F00001"))
        is None
    )
    assert _versions(session, "F00015") == {}
    # discovery provenance is still kept for both
    assert (
        session.scalar(
            select(SourceRecord).where(SourceRecord.external_record_id == "00000000000000f1")
        )
        is not None
    )


def test_bundle_for_another_case_is_refused(tmp_path: Path, ingestor: Ingestor) -> None:
    b = BundleBuilder(tmp_path, "other-case")
    b.write(case_number="KSC-BC-2020-06")
    with pytest.raises(CaseNotSeededError, match="scoped to"):
        ingestor.run_bundle(load_bundle(b.root))


def test_dry_run_persists_nothing(tmp_path: Path, sessions, session: Session) -> None:
    bundle = load_bundle(standard_bundle(tmp_path))
    store = InMemoryObjectStore()
    outcome = Ingestor(sessions, store, case_number=DEMO_CASE).run_bundle(bundle, dry_run=True)
    assert outcome.dry_run and outcome.downloaded_artifacts == 5
    assert store.objects  # bytes were hashed and would have been stored
    assert (
        session.scalar(
            select(IngestionJob).where(
                IngestionJob.cursor["bundle_id"].astext == "synthetic-demo-01"
            )
        )
        is None
    )
    assert (
        session.scalar(select(Document).where(Document.official_ref == f"{DEMO_CASE}/F00001"))
        is None
    )
    assert (
        session.scalar(
            select(SourceRecord).where(SourceRecord.external_record_id == "00000000000000a1")
        )
        is None
    )


def test_blocked_probe_is_recorded_as_a_visible_failure(
    ingestor: Ingestor, session: Session
) -> None:
    url = "https://repository.scp-ks.org/details.php?doc_id=00000000000000a1&doc_type=stl_filing&lang=eng"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            content=b"<html>Just a moment...</html>",
            headers={"cf-mitigated": "challenge", "content-type": "text/html"},
        )

    with HttpFetcher(transport=httpx.MockTransport(handler), min_interval=0) as fetcher:
        result = probe(url, fetcher)
    job_id = record_probe(ingestor, result)
    assert job_id is not None
    job = session.get(IngestionJob, job_id)
    assert job is not None and job.job_type == JOB_TYPE_LIVE_PROBE
    assert job.status is IngestionJobStatus.COMPLETED and job.failed_count == 1
    (item,) = job.items
    assert item.status is IngestionItemStatus.BLOCKED_BY_ACCESS_CONTROL
    assert "cf-mitigated" in (item.reason or "")
    assert item.detail["url"] == url


def test_status_endpoint_shows_held_refused_and_failed(
    tmp_path: Path, ingestor: Ingestor, demo_client
) -> None:
    ingestor.run_bundle(load_bundle(standard_bundle(tmp_path)))
    body = demo_client.get("/api/v1/ingestion/status").json()
    assert body["case_number"] == DEMO_CASE
    counts = body["counts"]
    assert counts["jobs"] >= 1 and counts["items_failed"] >= 1
    assert counts["versions_not_fetched"] >= 1 and counts["versions_failed"] >= 1
    assert counts["documents_not_public"] >= 1
    job = body["jobs"][0]
    assert job["job_type"] == "capture_bundle" and job["status"] == "completed"
    statuses = {i["item_key"].split(":")[-1]: i["status"] for i in job["items"]}
    assert statuses["00000000000000a5"] == "not_public"
    assert statuses["00000000000000a6"] == "unsupported_artifact"
    held = {(h["official_ref"], h["official_version_ref"]): h for h in body["held"]}
    red = held[(f"{DEMO_CASE}/F00001", f"{DEMO_CASE}/F00001/RED")]
    assert (
        red["artifact_status"] == "fetched"
        and red["sha256"]
        and red["fetch_method"] == "operator_browser_capture"
    )
    assert red["detail_page_url"].startswith(
        "https://repository.scp-ks.org/details.php?doc_id=00000000000000a1"
    )
    assert red["metadata_source"] == "synthetic_fixture"
    meta_only = held[(f"{DEMO_CASE}/F00003", f"{DEMO_CASE}/F00003")]
    assert meta_only["artifact_status"] == "not_fetched" and meta_only["sha256"] is None
    assert meta_only["source_url"] == artifact_url("Filing", "F00003.pdf")

    # the public read API still hides the refused record and exposes artifact status
    listed = {
        d["official_ref"] for d in demo_client.get("/api/v1/documents?limit=100").json()["items"]
    }
    assert f"{DEMO_CASE}/F00001" in listed and f"{DEMO_CASE}/F00005" not in listed
    detail = demo_client.get(f"/api/v1/documents/{DEMO_CASE}/F00003").json()
    assert detail["versions"][0]["artifact_status"] == "not_fetched"
