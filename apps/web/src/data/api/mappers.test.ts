import { describe, expect, it } from "vitest";
import * as fx from "./fixtures";
import {
  documentRouteId,
  findingRow,
  toCitation,
  toDocument,
  toEvidenceRows,
  toNetworkEdge,
  toSearchResult,
  toVerification,
  toWitness,
  witnessRow,
} from "./mappers";

describe("API → screen mapping", () => {
  it("maps resolved citations with the persisted display string", () => {
    const citation = toCitation(fx.resolvedCitation);
    expect(citation).toMatchObject({
      sourceType: "court",
      ref: "F-DEMO-001",
      docId: "F-DEMO-001",
      page: 2,
      paraFrom: 12,
      paraTo: 12,
      resolved: true,
      display: "F-DEMO-001 · ¶12",
    });
    expect(citation.lineFrom).toBeUndefined();
  });

  it("never renders a display string for an unresolved citation", () => {
    const citation = toCitation(fx.unresolvedCitation);
    expect(citation.resolved).toBe(false);
    expect(citation.display).toBe("UNRESOLVED");
    // Even a resolved flag with a non-resolved state fails closed.
    expect(toCitation({ ...fx.resolvedCitation, resolution_state: "ambiguous" }).resolved).toBe(
      false,
    );
  });

  it("strips the case prefix from document route ids", () => {
    expect(documentRouteId("KSC-DEMO-0000/F-DEMO-001")).toBe("F-DEMO-001");
    expect(documentRouteId("F-DEMO-001")).toBe("F-DEMO-001");
  });

  it("maps verification states and drops rejected facts", () => {
    expect(toVerification("human_verified")).toBe("verified");
    expect(toVerification("ai_flagged")).toBe("ai-flagged");
    expect(toVerification("needs_more_evidence")).toBe("needs-evidence");
    expect(toVerification("unresolved")).toBe("unresolved");
    expect(toVerification("unreviewed")).toBe("unreviewed");
    expect(toVerification("human_rejected")).toBeNull();
    expect(findingRow({ ...fx.finding, verification_state: "human_rejected" })).toBeNull();
  });

  it("keeps protected witnesses code-only", () => {
    const witness = toWitness(fx.protectedWitness);
    expect(witness.protected).toBe(true);
    expect("public" in witness).toBe(false);
    const row = witnessRow(fx.protectedWitness);
    expect(row.title).toBe("W-DEMO-001");
    expect(row.protected).toBe(true);
    expect(row.description).toBe("");
  });

  it("fails closed when a public block is incomplete", () => {
    expect(toWitness({ ...fx.publicWitness, public: undefined }).protected).toBe(true);
    expect(
      toWitness({ ...fx.publicWitness, public: { display_name: "X", called_by: null } }).protected,
    ).toBe(true);
    expect(toWitness({ ...fx.publicWitness, protected: true }).protected).toBe(true);
    const witness = toWitness(fx.publicWitness);
    expect(witness).toEqual({
      code: "W-DEMO-002",
      protected: false,
      protectiveMeasures: [],
      public: { displayName: "Demo Public Witness", calledBy: "defence" },
    });
  });

  it("maps a public document to paragraph spans and a not-public one to none", () => {
    const view = toDocument(fx.judgment, fx.chunks);
    expect(view.id).toBe("F-DEMO-001");
    expect(view.visibility).toBe("public_redacted");
    expect(view.paragraphs.map((p) => p.number)).toEqual([1, 10]);
    expect(view.citation).toMatchObject({
      sourceType: "court",
      docId: "F-DEMO-001",
      resolved: true,
    });

    const hidden = toDocument(fx.notPublicDocument, fx.chunks);
    expect(hidden.visibility).toBe("not_public");
    expect(hidden.paragraphs).toEqual([]);
    expect(hidden.citation.sourceType).toBe("spo");
  });

  it("withholds evidence rows on unresolved citations or non-design stances", () => {
    const rows = toEvidenceRows(fx.claim);
    expect(rows.map((r) => r.direction)).toEqual(["supports", "contradicts"]);
    expect(rows.every((r) => r.citation.resolved)).toBe(true);
    expect(rows[0]?.sourceType).toBe("witness");
  });

  it("withholds edges on unresolved citations", () => {
    expect(toNetworkEdge(fx.network.edges[2]!)).toBeNull();
    expect(toNetworkEdge(fx.network.edges[0]!)).toMatchObject({
      from: "n-person",
      to: "n-org",
      relation: "member_of",
      verification: "verified",
    });
  });

  it("maps search hits with route hrefs and code-only protected witnesses", () => {
    const [doc, witness] = fx.search.hits.map(toSearchResult);
    expect(doc).toMatchObject({ id: "F-DEMO-001", href: "/documents/F-DEMO-001" });
    expect(witness).toMatchObject({
      title: "W-DEMO-001",
      context: "",
      href: "/witnesses/W-DEMO-001",
    });
  });

  it("maps exact court search coordinates to a navigable citation", () => {
    const result = toSearchResult({
      ...fx.search.hits[0]!,
      version_ref: "F-DEMO-001/RED",
      page: 2,
      para_from: 12,
      para_to: 14,
      target_path: "/documents/F-DEMO-001?version=F-DEMO-001%2FRED&page=2&para=12",
    });

    expect(result.href).toContain("/documents/F-DEMO-001");
    expect(result.citation).toMatchObject({
      sourceType: "court",
      docId: "F-DEMO-001",
      page: 2,
      paraFrom: 12,
      paraTo: 14,
      resolved: true,
      display: "F-DEMO-001/RED · p. 2 · ¶12–14",
    });
  });
});
