import { describe, expect, it } from "vitest";
import { ApiError } from "./client";
import { routes, stubFetch } from "./fixtures";
import { createApiRepository } from "./repository";

function repository() {
  const stub = stubFetch();
  return {
    repo: createApiRepository({ baseUrl: "http://api.test/", fetch: stub.fetchImpl }),
    stub,
  };
}

describe("ApiRepository", () => {
  it("reads directories through paginated list endpoints", async () => {
    const { repo, stub } = repository();
    const rows = await repo.getDirectory("witnesses");
    expect(rows.map((r) => r.id)).toEqual(["W-DEMO-001", "W-DEMO-002"]);
    expect(rows[0]?.protected).toBe(true);
    expect(stub.calls).toEqual(["/witnesses?limit=200&offset=0"]);
    for (const kind of ["people", "documents", "findings", "exhibits", "incidents"] as const) {
      expect((await repo.getDirectory(kind)).length).toBeGreaterThan(0);
    }
  });

  it("returns null for unknown records instead of inventing them", async () => {
    const { repo } = repository();
    expect(await repo.getPerson("nobody")).toBeNull();
    expect(await repo.getWitness("W-NONE")).toBeNull();
    expect(await repo.getIncident("none")).toBeNull();
    expect(await repo.getDocument("F-NONE")).toBeNull();
  });

  it("loads only the requested reader coordinate", async () => {
    const { repo, stub } = repository();
    await repo.getDocument("F-DEMO-001", undefined, 2);
    expect(stub.calls).toEqual([
      "/documents/F-DEMO-001",
      "/document-versions/F-DEMO-001/RED/chunks?limit=200&offset=0&page=2",
    ]);
  });

  it("never substitutes another version when the requested one is not held", async () => {
    const { repo, stub } = repository();
    expect(await repo.getDocument("F-DEMO-001", "F-DEMO-001/NOT-HELD")).toBeNull();
    expect(stub.calls).toEqual(["/documents/F-DEMO-001"]);
  });

  it("loads a document with the chunks of its newest public version", async () => {
    const { repo, stub } = repository();
    const document = await repo.getDocument("F-DEMO-001");
    expect(document?.paragraphs).toHaveLength(2);
    expect(stub.calls).toEqual([
      "/documents/F-DEMO-001",
      "/document-versions/F-DEMO-001/RED/chunks?limit=200&offset=0",
    ]);
  });

  it("loads a provenance-backed finding matrix without conflating party positions", async () => {
    const { repo, stub } = repository();
    const finding = await repo.getFinding("FD-DEMO-001");
    expect(finding?.evidence[0]?.courtCited).toBe(true);
    expect(finding?.evidence[0]?.source.targetPath).toContain("para=12");
    expect(finding?.arguments[0]?.party).toBe("spo");
    expect(finding?.arguments[0]?.sourceScope).toBe("court_summary");
    expect(finding?.audit.sourcesMissing).toBe(1);
    expect(stub.calls).toEqual(["/findings/FD-DEMO-001/matrix"]);
  });

  it("states a not-public document without fetching content", async () => {
    const { repo, stub } = repository();
    const document = await repo.getDocument("F-DEMO-004");
    expect(document?.visibility).toBe("not_public");
    expect(document?.paragraphs).toEqual([]);
    expect(stub.calls).toEqual(["/documents/F-DEMO-004"]);
  });

  it("reads one bounded page of typed evidence edges and only the nodes they touch", async () => {
    const { repo, stub } = repository();
    const view = await repo.getNetwork("W-DEMO-001", {
      relationshipType: "testified_at",
      evidenceKind: "witness_appearance",
    });
    expect(stub.calls).toEqual([
      "/network/edges?limit=100&focus_ref=W-DEMO-001&relationship_type=testified_at&evidence_kind=witness_appearance",
    ]);
    // A rejected edge never surfaces; the orphan node it touched is dropped.
    expect(view.edges.map((e) => e.id)).toEqual(["e-1", "e-2"]);
    expect(view.nodes.map((n) => n.id).sort()).toEqual([
      "n-hearing",
      "n-org",
      "n-person",
      "n-witness",
    ]);
    const witness = view.nodes.find((n) => n.id === "n-witness");
    expect(witness?.type).toBe("protected");
    expect(witness?.label).toBe("W-DEMO-001");
    expect(view.nodes.every((n) => Number.isFinite(n.x) && Number.isFinite(n.y))).toBe(true);
    const testified = view.edges[1]!;
    expect(testified.evidenceKind).toBe("witness_appearance");
    expect(testified.evidenceCount).toBe(2);
    expect(testified.provenance?.href).toBe(
      "/documents/transcript?document=T%2F2023-06-01&page=101&hl=Witness%3A%20W-DEMO-001%20(Open%20Session)",
    );
    expect(testified.citation.display).toBe("KSC-DEMO-0000/T/2023-06-01 · p. 101");
    expect(view.page).toEqual({
      total: 250,
      byType: { cited_in: 240, testified_at: 9, mentioned_in: 1 },
      nextCursor: "00000000-0000-4000-8000-0000000000e2",
      query: { relationshipType: "testified_at", evidenceKind: "witness_appearance" },
    });
  });

  it("reads header-backed appearances and court-record status history", async () => {
    const { repo, stub } = repository();
    const [appearance] = await repo.getAppearances("witness", "W-DEMO-001");
    expect(appearance?.examinations).toEqual([{ page: 101, text: "Examination by Demo Counsel" }]);
    expect(appearance?.provenance.kind).toBe("witness_appearance");
    expect(await repo.getAppearances("person", "nobody")).toEqual([]);
    const [event] = await repo.getExhibitStatusEvents("P-DEMO-001");
    expect(event?.eventType).toBe("admitted");
    expect(event?.provenance.text).toBe("P-DEMO-001 is admitted");
    expect(event?.provenance.citation.display).toBe("KSC-DEMO-0000/F-DEMO-001/RED · p. 4 · ¶12");
    expect(await repo.getExhibitStatusEvents("P-NONE")).toEqual([]);
    expect(stub.calls).toEqual([
      "/witnesses/W-DEMO-001/appearances",
      "/people/nobody/appearances",
      "/exhibits/P-DEMO-001/status-events",
      "/exhibits/P-NONE/status-events",
    ]);
  });

  it("maps timeline, evidence and search", async () => {
    const { repo } = repository();
    const timeline = await repo.getTimeline();
    expect(timeline.map((t) => t.dateType)).toEqual(["event", "decision"]);
    expect(timeline[1]?.href).toBe("/documents/F-DEMO-001");
    expect((await repo.getEvidence()).length).toBe(2);
    expect((await repo.search("demo")).map((r) => r.category)).toEqual([
      "documents",
      "witnesses",
      "people",
    ]);
  });

  it("serves nothing for the legacy answer placeholder", async () => {
    const { repo } = repository();
    expect(await repo.getPath()).toEqual([]);
    expect(await repo.getAnswer()).toEqual([]);
  });

  it("creates, reads and saves audited citation-first AI runs", async () => {
    const { repo } = repository();
    const created = await repo.createAiRun("What did the Panel find?");
    expect(created.sources[0]?.display).toBe("F-DEMO-001/RED · ¶12–14");
    expect(created.blocks.map((block) => block.kind)).toEqual(["court", "ai"]);
    expect((await repo.getAiRun(created.id))?.answerWithheld).toBe(false);
    expect((await repo.listAiRuns()).map((run) => run.id)).toEqual([created.id]);
    expect(await repo.saveAiRunAsNote(created.id, "Review note")).toMatchObject({
      provenance: "ai_assisted",
    });
  });

  it("loads independently cited evidence-path hops", async () => {
    const { repo, stub } = repository();
    const hops = await repo.getPath("n-person", "n-org", 4);
    expect(hops).toHaveLength(1);
    expect(hops[0]?.citation.resolved).toBe(true);
    expect(stub.calls).toEqual(["/network/path?from_node_id=n-person&to_node_id=n-org&max_hops=4"]);
  });

  it("surfaces non-404 failures as ApiError", async () => {
    const failing = createApiRepository({
      baseUrl: "http://api.test",
      fetch: async () => new Response("boom", { status: 500 }),
    });
    await expect(failing.getPerson("demo-person-a")).rejects.toBeInstanceOf(ApiError);
    expect(Object.keys(routes)).toContain("/case");
  });
});
