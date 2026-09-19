import { describe, expect, it } from "vitest";
import { mockRepository } from "./repository";

describe("typed mock repository", () => {
  it("keeps protected witnesses code-only", () => {
    const witness = mockRepository.getWitness("W01234");
    expect(witness.protected).toBe(true);
    expect("public" in witness).toBe(false);
  });

  it("backs every graph edge and path hop with a resolved citation", () => {
    expect(mockRepository.getNetwork().edges.every((edge) => edge.citation.resolved)).toBe(true);
    expect(mockRepository.getPath().every((hop) => hop.citation.resolved)).toBe(true);
  });

  it("returns all directory domains through one replaceable boundary", () => {
    for (const kind of [
      "people",
      "witnesses",
      "documents",
      "findings",
      "exhibits",
      "incidents",
    ] as const) {
      expect(mockRepository.getDirectory(kind).length).toBeGreaterThan(0);
    }
  });

  it("keeps AI answer order with analysis last", () => {
    const answer = mockRepository.getAnswer();
    expect(answer.at(-1)?.kind).toBe("ai");
    expect(answer.every((block) => block.citations.every((citation) => citation.resolved))).toBe(
      true,
    );
  });
});
