import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { aiRunSummary } from "@/data/api/fixtures";

const state = vi.hoisted(() => ({ token: undefined as string | undefined }));
vi.mock("next/headers", () => ({
  cookies: async () => ({ get: () => (state.token ? { value: state.token } : undefined) }),
}));

import { aiResearchRepository, proxyAiRequest } from "./ai-access";

describe("AI Researcher web boundary", () => {
  beforeEach(() => vi.stubEnv("CANONICAL_URL", "https://app.test"));

  afterEach(() => {
    state.token = undefined;
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("does not proxy anonymous staging run reads or writes", async () => {
    vi.stubEnv("APP_ENV", "staging");
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    expect(await aiResearchRepository()).toBeNull();
    const listing = await proxyAiRequest(
      new Request("https://app.test/api/v1/ai/runs"),
      "/runs",
      "GET",
    );
    expect(listing.status).toBe(401);
    const creation = await proxyAiRequest(
      new Request("https://app.test/api/v1/ai/runs", {
        method: "POST",
        headers: { origin: "https://app.test" },
        body: JSON.stringify({ question: "What does the record say?" }),
      }),
      "/runs",
      "POST",
    );
    expect(creation.status).toBe(401);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("forwards a server-held token for authorized list, detail and writes", async () => {
    vi.stubEnv("APP_ENV", "staging");
    vi.stubEnv("API_INTERNAL_URL", "http://internal-api.test");
    state.token = "r".repeat(32);
    const fetchMock = vi.fn(async (input: string) =>
      Response.json(input.endsWith("/runs") ? [aiRunSummary] : { id: "run-1" }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const repository = await aiResearchRepository();
    expect((await repository?.listAiRuns())?.[0]?.id).toBe(aiRunSummary.id);
    const detail = await proxyAiRequest(
      new Request("https://app.test/api/v1/ai/runs/run-1"),
      "/runs/run-1",
      "GET",
    );
    expect(detail.status).toBe(200);
    const created = await proxyAiRequest(
      new Request("https://app.test/api/v1/ai/runs", {
        method: "POST",
        headers: { origin: "https://app.test" },
        body: JSON.stringify({ question: "What does the record say?" }),
      }),
      "/runs",
      "POST",
    );
    expect(created.status).toBe(200);
    const calls = fetchMock.mock.calls as unknown as [string, RequestInit][];
    expect(
      calls.every(
        ([, init]) => new Headers(init.headers).get("authorization") === `Bearer ${state.token}`,
      ),
    ).toBe(true);
    expect(calls.every(([, init]) => init.cache === "no-store")).toBe(true);
    expect(calls.every(([url]) => url.startsWith("http://internal-api.test/api/v1/ai/runs"))).toBe(
      true,
    );
  });

  it("rejects cross-origin mutation even with a Researcher cookie", async () => {
    vi.stubEnv("APP_ENV", "staging");
    state.token = "r".repeat(32);
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const response = await proxyAiRequest(
      new Request("https://app.test/api/v1/ai/runs", {
        method: "POST",
        headers: { origin: "https://other.test" },
        body: "{}",
      }),
      "/runs",
      "POST",
    );
    expect(response.status).toBe(403);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("preserves unauthenticated local development behavior", async () => {
    vi.stubEnv("APP_ENV", "development");
    const fetchMock = vi.fn(async () => Response.json([]));
    vi.stubGlobal("fetch", fetchMock);
    const response = await proxyAiRequest(
      new Request("http://localhost:3000/api/v1/ai/runs"),
      "/runs",
      "GET",
    );
    expect(response.status).toBe(200);
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(new Headers(init.headers).has("authorization")).toBe(false);
  });
});
