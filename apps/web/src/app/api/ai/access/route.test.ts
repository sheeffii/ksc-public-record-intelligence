import { afterEach, describe, expect, it, vi } from "vitest";

const state = vi.hoisted(() => ({ verified: true }));
vi.mock("@/lib/ai-access", () => ({
  AI_ACCESS_COOKIE: "ksc_researcher_access",
  aiAccessRequired: () => true,
  aiWebOrigin: () => "https://app.test",
  sameOriginMutation: () => true,
  aiApiRequest: async () => new Response(null, { status: state.verified ? 200 : 401 }),
}));

import { POST } from "./route";

describe("Researcher access form", () => {
  afterEach(() => {
    state.verified = true;
  });

  it("stores a validated bearer only in a secure HttpOnly session cookie", async () => {
    const response = await POST(
      new Request("https://app.test/api/ai/access", {
        method: "POST",
        body: new URLSearchParams({ token: "r".repeat(32) }),
      }),
    );
    expect(response.status).toBe(303);
    expect(response.headers.get("location")).toBe("https://app.test/ai");
    expect(response.headers.get("set-cookie")).toContain("HttpOnly");
    expect(response.headers.get("set-cookie")).toContain("Secure");
    expect(response.headers.get("set-cookie")).toContain("SameSite=strict");
    expect(response.headers.get("set-cookie")).toContain("ksc_researcher_access=");
  });

  it("never stores an invalid token", async () => {
    state.verified = false;
    const response = await POST(
      new Request("https://app.test/api/ai/access", {
        method: "POST",
        body: new URLSearchParams({ token: "bad" }),
      }),
    );
    expect(response.status).toBe(303);
    expect(response.headers.get("set-cookie")).toBeNull();
    expect(response.headers.get("location")).toContain("access=invalid");
  });

  it("expires Researcher access after eight hours", async () => {
    const response = await POST(
      new Request("https://app.test/api/ai/access", {
        method: "POST",
        body: new URLSearchParams({ token: "r".repeat(32) }),
      }),
    );
    expect(response.headers.get("set-cookie")).toContain("Max-Age=28800");
  });
});
