from __future__ import annotations

import uuid

from sqlalchemy import func, select

from ksc_api.config import get_settings
from ksc_api.db.session import session_scope
from ksc_api.models import Case, Finding, ResearchNote
from ksc_api.services.ai_providers import ProviderClaim, ProviderResponse
from ksc_api.services.ai_research import AiResearchService


def test_demo_ai_run_is_audited_and_source_grounded(demo_client):
    response = demo_client.post(
        "/api/v1/ai/runs",
        json={"question": "What does the Panel find about the synthetic demo event?"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["answer_withheld"] is False
    assert body["sources"]
    assert body["blocks"][-1]["kind"] == "ai"
    assert all(block["sources"] for block in body["blocks"])
    whitelist = {source["id"] for source in body["sources"]}
    assert all(source["id"] in whitelist for block in body["blocks"] for source in block["sources"])
    assert body["citation_status"]["unresolved"] == 0
    assert demo_client.get(f"/api/v1/ai/runs/{body['id']}").json() == body


def test_missing_record_abstains_and_renders_no_partial_answer(demo_client):
    body = demo_client.post(
        "/api/v1/ai/runs", json={"question": "What does filing F99999 establish?"}
    ).json()
    assert body["answer_withheld"] is True
    assert body["insufficient_evidence"] is True
    assert body["blocks"] == []
    assert body["sources"] == []
    assert body["validation_errors"][0]["code"] == "DOCUMENT_NOT_FOUND"


class FabricatingProvider:
    name = "adversarial-test"
    model = "fabricator"

    def generate(self, request):
        return ProviderResponse(
            claims=(
                ProviderClaim(
                    kind="court",
                    text=request.sources[0].text,
                    content_type="verbatim_quote",
                    source_ids=("not-in-retrieval-whitelist",),
                ),
            )
        )


def test_fabricated_citation_is_persisted_as_withheld(demo_settings):
    with session_scope() as session:
        case = session.scalar(select(Case).where(Case.case_number == "KSC-DEMO-0000"))
        assert case is not None
        before = session.scalar(select(func.count()).select_from(Finding))
        run = AiResearchService(
            session, case, get_settings(), provider=FabricatingProvider()
        ).create_run("What does the Panel find about the synthetic demo event?")
        assert run.answer_withheld is True
        assert run.outputs == []
        assert {error["code"] for error in run.validation_errors or []} == {
            "CITATION_NOT_FOUND",
            "QUOTE_NOT_VERIFIED",
        }
        assert session.scalar(select(func.count()).select_from(Finding)) == before


def test_saved_output_remains_an_ai_assisted_research_note(demo_client, demo_settings):
    run = demo_client.post(
        "/api/v1/ai/runs",
        json={"question": "What does the Panel find about the synthetic demo event?"},
    ).json()
    response = demo_client.post(f"/api/v1/ai/runs/{run['id']}/notes", json={"title": "Review note"})
    assert response.status_code == 201
    assert response.json()["provenance"] == "ai_assisted"
    with session_scope() as session:
        note = session.scalar(select(ResearchNote).where(ResearchNote.id == response.json()["id"]))
        assert note is not None
        assert note.origin_ai_run_id == uuid.UUID(run["id"])
