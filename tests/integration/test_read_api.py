"""Read API against the synthetic fixture: pagination, filtering,
serialisation, and fail-closed behaviour."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

V1 = "/api/v1"


def test_case_is_the_configured_case(demo_client):
    body = demo_client.get(f"{V1}/case").json()
    assert body["case_number"] == "KSC-DEMO-0000"


def test_document_listing_excludes_not_public_and_paginates(demo_client):
    body = demo_client.get(f"{V1}/documents").json()
    refs = {item["official_ref"] for item in body["items"]}
    assert "KSC-DEMO-0000/F-DEMO-004" not in refs
    assert body["total"] == 4 and len(body["items"]) == 4
    page = demo_client.get(f"{V1}/documents?limit=2&offset=2").json()
    assert page["total"] == 4 and len(page["items"]) == 2
    assert page["limit"] == 2 and page["offset"] == 2
    filtered = demo_client.get(f"{V1}/documents?document_type=judgment").json()
    assert [i["official_ref"] for i in filtered["items"]] == ["KSC-DEMO-0000/F-DEMO-001"]
    searched = demo_client.get(f"{V1}/documents?q=defence").json()
    assert searched["total"] == 1


def test_not_public_document_is_stated_not_404(demo_client):
    body = demo_client.get(f"{V1}/documents/F-DEMO-004").json()
    assert body["visibility"] == "not_public"
    assert body["versions"] == []
    assert demo_client.get(f"{V1}/documents/F-DEMO-999").status_code == 404


def test_non_public_version_and_its_pages_are_withheld(demo_client):
    detail = demo_client.get(f"{V1}/documents/KSC-DEMO-0000/F-DEMO-001").json()
    assert [v["official_version_ref"] for v in detail["versions"]] == ["F-DEMO-001/RED"]
    assert detail["versions"][0]["supersedes_version_ref"] == "F-DEMO-001"
    assert demo_client.get(f"{V1}/document-versions/F-DEMO-001/pages").status_code == 404
    pages = demo_client.get(f"{V1}/document-versions/F-DEMO-001/RED/pages?limit=2").json()
    assert pages["total"] == 3 and [p["page_number"] for p in pages["items"]] == [1, 2]
    assert pages["items"][1]["has_redactions"] is True
    chunks = demo_client.get(f"{V1}/document-versions/F-DEMO-001/RED/chunks").json()
    assert [(c["para_from"], c["para_to"]) for c in chunks["items"]] == [(1, 9), (10, 20), (21, 40)]
    page_two = demo_client.get(f"{V1}/document-versions/F-DEMO-001/RED/chunks?page=2").json()
    assert [(c["para_from"], c["para_to"]) for c in page_two["items"]] == [
        (10, 20),
        (21, 40),
    ]
    assert demo_client.get(f"{V1}/document-versions/F-DEMO-001/chunks").status_code == 404


def test_protected_witness_has_no_public_block(demo_client):
    protected = demo_client.get(f"{V1}/witnesses/W-DEMO-001").json()
    assert protected["protected"] is True
    assert "public" not in protected
    assert set(protected) == {"code", "protected", "protective_measures", "counts"}
    public = demo_client.get(f"{V1}/witnesses/W-DEMO-002").json()
    assert public["protected"] is False
    assert public["public"] == {"display_name": "Demo Public Witness", "called_by": "defence"}
    listing = demo_client.get(f"{V1}/witnesses").json()
    assert {w["code"]: "public" in w for w in listing["items"]} == {
        "W-DEMO-001": False,
        "W-DEMO-002": True,
    }


def test_person_exhibit_incident_details(demo_client):
    person = demo_client.get(f"{V1}/people/demo-person-a").json()
    assert person["aliases"] == ["D. Person A"]
    # Counts only, and only over public provenance-backed edges: the rejected
    # and unresolved edges on Demo Person A do not count.
    assert person["counts"] == {
        "relationships": 2,
        "document_mentions": 0,
        "transcript_mentions": 0,
        "exhibit_refs": 0,
        "findings": 1,
        "witnesses_who_referred": 0,
        "incidents": 0,
        "citations_resolved": 0,
    }
    witness = demo_client.get(f"{V1}/witnesses/W-DEMO-001").json()
    assert witness["counts"]["transcript_mentions"] == 3  # 2 public segments + 1 hearing edge
    assert witness["counts"]["incidents"] == 1
    assert witness["counts"]["citations_resolved"] == 1
    exhibit = demo_client.get(f"{V1}/exhibits/P-DEMO-001").json()
    assert exhibit["status"] == "unknown"
    assert exhibit["through_witness_code"] == "W-DEMO-002"
    assert exhibit["document_version_ref"] == "F-DEMO-002"
    incident = demo_client.get(f"{V1}/incidents/demo-incident-001").json()
    assert incident["location"] == "Demo Village"
    assert incident["date_precision"] == "range"
    assert demo_client.get(f"{V1}/people/nobody").status_code == 404
    organization = demo_client.get(f"{V1}/organizations/demo-unit").json()
    assert organization["name"] == "Demo Unit"
    assert organization["name_variants"] == ["Demo Unit", "Njësia Demo"]


def test_finding_detail_exposes_structured_matrix_and_source_audit(demo_client):
    body = demo_client.get(f"{V1}/findings/FD-DEMO-001").json()
    assert body["judgment_ref"] == "KSC-DEMO-0000/F-DEMO-001"
    assert body["citation"]["display"] == "F-DEMO-001 · ¶12\u201314"  # canonical EN DASH
    assert body["citation"]["source_type"] == "court"
    assert len(body["evidence_links"]) == 3
    assert all(link["citation"]["resolved"] for link in body["evidence_links"])
    court_cited = [link for link in body["evidence_links"] if link["court_cited"]]
    assert all(link["court_cited_para"] == 13 for link in court_cited)
    assert all(link["relationship_basis"] == "explicit_court_citation" for link in court_cited)
    parties = {a["party"] for a in body["arguments"]}
    assert parties == {"spo", "defence", "court"}
    assert body["judgment"]["version_ref"] == "F-DEMO-001/RED"
    assert body["judgment"]["sections"]
    assert len(body["court_responses"]) == 2
    assert all(item["argument"]["party"] == "court" for item in body["court_responses"])
    assert body["source_audit"]["citations_total"] >= 4
    assert body["source_audit"]["citations_unresolved"] == 0
    assert body["corroboration_note"].startswith("No additional corroborating source")
    matrix = demo_client.get(f"{V1}/findings/FD-DEMO-001/matrix")
    assert matrix.status_code == 200 and matrix.json() == body
    listing = demo_client.get(f"{V1}/findings").json()
    assert listing["total"] == 1 and "evidence_links" not in listing["items"][0]


def test_claim_mentions_withhold_unresolved_citations(demo_client):
    body = demo_client.get(f"{V1}/claims/CL-DEMO-001").json()
    assert len(body["mentions"]) == 4
    assert all(m["citation"]["resolved"] for m in body["mentions"])
    stances = sorted(m["stance"] for m in body["mentions"])
    assert stances == ["contradicts", "neutral", "supports", "supports"]
    source_types = {m["citation"]["source_type"] for m in body["mentions"]}
    assert source_types == {"witness", "spo", "defence", "exhibit"}


def test_network_withholds_rejected_and_unresolved_edges(demo_client):
    body = demo_client.get(f"{V1}/network").json()
    assert len(body["edges"]) == 10
    assert all(edge["citation"]["resolved"] for edge in body["edges"])
    assert all(edge["verification_state"] != "human_rejected" for edge in body["edges"])
    node_ids = {n["id"] for n in body["nodes"]}
    assert all(e["from_node_id"] in node_ids and e["to_node_id"] in node_ids for e in body["edges"])
    witness_nodes = {n["label"]: n for n in body["nodes"] if n["entity_kind"] == "witness"}
    assert witness_nodes["W-DEMO-001"]["protected"] is True
    assert witness_nodes["W-DEMO-001"]["ref"] == "W-DEMO-001"
    assert witness_nodes["W-DEMO-002"]["protected"] is False
    person_node = next(n for n in body["nodes"] if n["entity_kind"] == "person")
    rels = demo_client.get(f"{V1}/relationships?node_id={person_node['id']}").json()
    assert rels["total"] == 2


def test_evidence_path_uses_only_cited_edges_and_invents_no_hops(demo_client):
    network = demo_client.get(f"{V1}/network").json()
    edge = network["edges"][0]
    path = demo_client.get(
        f"{V1}/network/path",
        params={"from_node_id": edge["from_node_id"], "to_node_id": edge["to_node_id"]},
    ).json()
    assert path["found"] is True
    assert path["hops"]
    assert all(hop["citation"]["resolved"] for hop in path["hops"])
    assert all(hop["citation"]["source_document_version_ref"] for hop in path["hops"])
    assert all(hop["citation"]["source_path"] for hop in path["hops"])
    assert all(hop["extraction_origin"] != "analytical" for hop in path["hops"])

    missing = demo_client.get(
        f"{V1}/network/path",
        params={
            "from_node_id": "00000000-0000-0000-0000-000000000001",
            "to_node_id": "00000000-0000-0000-0000-000000000002",
        },
    ).json()
    assert missing == {"found": False, "nodes": [], "hops": []}


def test_events_keep_the_five_date_types(demo_client):
    body = demo_client.get(f"{V1}/events").json()
    assert {e["date_type"] for e in body["items"]} == {
        "event",
        "document",
        "filing",
        "testimony",
        "decision",
    }
    assert all(e["citation"] is None or e["citation"]["resolved"] for e in body["items"])
    assert all(
        e["date_precision"]
        in {"exact", "range", "approximate", "month_only", "year_only", "unknown"}
        for e in body["items"]
    )


def test_transcript_segments_closed_session_has_no_text(demo_client):
    body = demo_client.get(f"{V1}/transcripts/T-DEMO-001").json()
    segments = body["segments"]
    assert [s["sequence"] for s in segments] == [0, 1, 2, 3]
    closed = segments[3]
    assert closed["closed_session"] is True and closed["text"] is None
    assert segments[1]["witness_code"] == "W-DEMO-001"
    assert segments[1]["examination_type"] == "direct"


def test_identifier_resolution_states(demo_client):
    resolved = demo_client.get(f"{V1}/citations/resolve?ref= f-demo-001 ").json()
    assert resolved["state"] == "resolved" and resolved["normalized"] == "F-DEMO-001"
    assert resolved["matches"][0]["entity_kind"] == "document"
    assert demo_client.get(f"{V1}/citations/resolve?ref=DEMO-AMBIG").json()["state"] == "ambiguous"
    assert demo_client.get(f"{V1}/citations/resolve?ref=F-DEMO-999").json()["state"] == "unresolved"
    assert demo_client.get(f"{V1}/citations/resolve").status_code == 422


def test_citation_by_id_round_trips(demo_client):
    finding = demo_client.get(f"{V1}/findings/FD-DEMO-001").json()
    citation_id = finding["citation"]["id"]
    body = demo_client.get(f"{V1}/citations/{citation_id}").json()
    assert body["id"] == citation_id and body["doc_id"] == "KSC-DEMO-0000/F-DEMO-001"
    assert (
        demo_client.get(f"{V1}/citations/00000000-0000-0000-0000-000000000000").status_code == 404
    )


def test_search_groups_public_hits_only(demo_client):
    body = demo_client.get(f"{V1}/search?q=demo").json()
    categories = {hit["category"] for hit in body["hits"]}
    assert {
        "documents",
        "people",
        "witnesses",
        "exhibits",
        "incidents",
        "findings",
        "locations",
    } <= categories
    refs = {hit["ref"] for hit in body["hits"]}
    assert "KSC-DEMO-0000/F-DEMO-004" not in refs
    witness_hits = {h["ref"]: h["protected"] for h in body["hits"] if h["category"] == "witnesses"}
    assert witness_hits == {"W-DEMO-001": True, "W-DEMO-002": False}
    assert demo_client.get(f"{V1}/search?q=").json()["hits"] == []


def test_phase8_search_modes_filters_and_source_navigation(demo_client):
    exact = demo_client.get(f"{V1}/search?q=F-DEMO-001&mode=exact").json()["hits"]
    assert exact[0]["match_kind"] == "exact_identifier"
    assert exact[0]["target_path"].startswith("/documents/F-DEMO-001")

    phrase = demo_client.get(f"{V1}/search?q=solemn declaration&mode=phrase").json()["hits"]
    assert any(hit["category"] == "transcripts" for hit in phrase)
    assert all(hit["match_kind"] == "phrase" for hit in phrase)

    filtered = demo_client.get(
        f"{V1}/search?q=demo&document_type=judgment&source_type=document"
    ).json()["hits"]
    assert filtered
    assert {hit["category"] for hit in filtered} == {"documents"}
    assert {hit["ref"] for hit in filtered} == {"KSC-DEMO-0000/F-DEMO-001"}

    transcript = demo_client.get(f"{V1}/search?q=testimony&source_type=transcript").json()["hits"]
    assert transcript
    assert all(hit["category"] == "transcripts" for hit in transcript)
    assert all(
        "page=" in hit["target_path"] and "line=" in hit["target_path"] for hit in transcript
    )
