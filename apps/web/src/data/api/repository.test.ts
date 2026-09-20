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
    expect(await repo.getDocument("F-NONE")).toBeNull();
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

  it("builds a network of provenance-backed edges and only the nodes they touch", async () => {
    const { repo } = repository();
    const { nodes, edges } = await repo.getNetwork();
    expect(edges.map((e) => e.id)).toEqual(["r-1", "r-2"]);
    expect(nodes.map((n) => n.id).sort()).toEqual(["n-hearing", "n-org", "n-person", "n-witness"]);
    const witness = nodes.find((n) => n.id === "n-witness");
    expect(witness?.type).toBe("protected");
    expect(witness?.label).toBe("W-DEMO-001");
    expect(nodes.every((n) => Number.isFinite(n.x) && Number.isFinite(n.y))).toBe(true);
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

  it("serves nothing for surfaces without a backend yet", async () => {
    const { repo } = repository();
    expect(await repo.getPath()).toEqual([]);
    expect(await repo.getAnswer()).toEqual([]);
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
