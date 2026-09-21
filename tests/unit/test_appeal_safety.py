from __future__ import annotations

from ksc_api.models import AppealIssue, RedTeamReview, StatementComparison
from ksc_api.services.ai_providers import ProviderClaim, ProviderResponse, ProviderSource
from ksc_api.services.ai_validation import validate_response


def _source() -> ProviderSource:
    return ProviderSource(
        id="source-1",
        category="court_finding",
        ref="F00001",
        citation="F00001 · ¶1",
        text="The Panel records this exact public passage.",
    )


def test_appeal_models_have_no_score_rank_probability_or_person_assessment_fields() -> None:
    prohibited = {
        "probability",
        "likelihood",
        "success_score",
        "strength",
        "rank",
        "priority",
        "credibility",
    }
    for model in (AppealIssue, RedTeamReview, StatementComparison):
        assert prohibited.isdisjoint(model.__table__.columns.keys())


def test_ai_attempts_to_declare_success_or_score_credibility_fail_closed() -> None:
    item = _source()
    response = ProviderResponse(
        claims=(
            ProviderClaim(
                kind="ai",
                text="This is a successful appeal ground with a credibility score of 90.",
                content_type="ai_analysis",
                source_ids=(item.id,),
            ),
        )
    )
    assert "UNSUPPORTED_CLAIM" in {error.code for error in validate_response(response, (item,))}
