/**
 * Swap-ability proof: the same screen-level expectations hold for both
 * adapters, and `getRepository()` picks one from configuration only.
 */

import { describe, expect, it } from "vitest";
import { stubFetch } from "./api/fixtures";
import { createApiRepository } from "./api/repository";
import { REPOSITORY_METHODS, type ResearchRepository } from "./contract";
import { createRepository, resolveApiBaseUrl, resolveDataSource } from "./index";
import { createMockRepositoryAdapter } from "./mock-adapter";

const adapters: Record<string, ResearchRepository> = {
  mock: createMockRepositoryAdapter(),
  api: createApiRepository({ baseUrl: "http://api.test", fetch: stubFetch().fetchImpl }),
};

describe.each(Object.entries(adapters))("%s repository", (_name, repo) => {
  it("implements every contract method", () => {
    for (const method of REPOSITORY_METHODS) {
      expect(typeof repo[method]).toBe("function");
    }
  });

  it("serves every directory through the same boundary", async () => {
    for (const kind of [
      "people",
      "witnesses",
      "documents",
      "findings",
      "exhibits",
      "incidents",
    ] as const) {
      const rows = await repo.getDirectory(kind);
      expect(rows.length).toBeGreaterThan(0);
      expect(rows.every((row) => row.kind === kind && row.href.startsWith("/"))).toBe(true);
    }
  });

  it("keeps protected witnesses code-only and backs every edge with a resolved citation", async () => {
    const witnesses = await repo.getDirectory("witnesses");
    const protectedRow = witnesses.find((row) => row.protected);
    expect(protectedRow).toBeDefined();
    const witness = await repo.getWitness(protectedRow!.id);
    expect(witness?.protected).toBe(true);
    expect(witness && "public" in witness).toBe(false);

    const { nodes, edges } = await repo.getNetwork();
    expect(edges.every((edge) => edge.citation.resolved)).toBe(true);
    const ids = new Set(nodes.map((n) => n.id));
    expect(edges.every((edge) => ids.has(edge.from) && ids.has(edge.to))).toBe(true);
  });

  it("never returns an unresolved citation as evidence or as an AI block", async () => {
    expect((await repo.getEvidence()).every((row) => row.citation.resolved)).toBe(true);
    expect((await repo.getPath()).every((hop) => hop.citation.resolved)).toBe(true);
    const answer = await repo.getAnswer();
    expect(answer.every((block) => block.citations.every((c) => c.resolved))).toBe(true);
  });
});

describe("repository selection", () => {
  it("defaults to the real API and enables fixtures only when explicitly configured", () => {
    expect(resolveDataSource({})).toBe("api");
    expect(resolveDataSource({ NEXT_PUBLIC_DATA_SOURCE: "nonsense" })).toBe("api");
    expect(resolveDataSource({ NEXT_PUBLIC_DATA_SOURCE: "api" })).toBe("api");
    expect(resolveDataSource({ NEXT_PUBLIC_DATA_SOURCE: "mock" })).toBe("mock");
  });

  it("prefers the internal API URL on the server", () => {
    const env = {
      NEXT_PUBLIC_API_URL: "http://localhost:8000",
      API_INTERNAL_URL: "http://api:8000",
    };
    expect(resolveApiBaseUrl(env, true)).toBe("http://api:8000");
    expect(resolveApiBaseUrl(env, false)).toBe("http://localhost:8000");
    expect(resolveApiBaseUrl({}, true)).toBe("http://localhost:8000");
  });

  it("creates either adapter from the environment without touching screens", async () => {
    const mock = createRepository({ NEXT_PUBLIC_DATA_SOURCE: "mock" }, true);
    expect((await mock.getDirectory("witnesses")).length).toBeGreaterThan(0);
    const api = createRepository(
      { NEXT_PUBLIC_DATA_SOURCE: "api", API_INTERNAL_URL: "http://api.test" },
      true,
    );
    for (const method of REPOSITORY_METHODS) expect(typeof api[method]).toBe("function");
  });
});
