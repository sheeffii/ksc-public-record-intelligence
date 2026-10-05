import "@/test/next-mocks";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { aiRun, aiRunSummary, withheldAiRun } from "@/data/api/fixtures";
import { toAiRun, toAiRunSummary } from "@/data/api/mappers";
import { renderWithProviders } from "@/test/render";
import { AiResearchReal } from "./AiResearchReal";

describe("AiResearchReal", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("shows verified sources before distinct record and AI answer blocks", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <AiResearchReal initialRun={toAiRun(aiRun)} sessions={[toAiRunSummary(aiRunSummary)]} />,
    );
    expect(document.querySelector("[data-demo-flag]")).not.toBeInTheDocument();
    expect(screen.getByText("Retrieved sources")).toBeInTheDocument();
    expect(screen.getAllByText("COURT FINDING").length).toBeGreaterThan(0);
    expect(screen.getByText("AI ANALYSIS")).toBeInTheDocument();
    await user.click(screen.getAllByText("F-DEMO-001/RED · ¶12–14")[0]!);
    expect(screen.getByRole("link", { name: /Open exact source/ })).toHaveAttribute(
      "href",
      expect.stringContaining("para=12"),
    );
  });

  it("withholds the entire answer when the corpus is insufficient", () => {
    renderWithProviders(<AiResearchReal initialRun={toAiRun(withheldAiRun)} sessions={[]} />);
    expect(screen.getByText("Answer withheld")).toBeInTheDocument();
    expect(
      screen.getByText("The controlled corpus does not contain the public Trial Judgment."),
    ).toBeInTheDocument();
    expect(screen.queryByText("AI ANALYSIS")).not.toBeInTheDocument();
  });

  it("creates runs and saves notes through same-origin authenticated routes", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn(async (input: string) =>
      Response.json(
        input.endsWith("/notes") ? { id: "note-1", provenance: "ai_assisted" } : aiRun,
        { status: input.endsWith("/notes") ? 201 : 201 },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    renderWithProviders(<AiResearchReal initialRun={toAiRun(aiRun)} sessions={[]} />);
    await user.clear(screen.getByRole("textbox", { name: /Question/i }));
    await user.type(screen.getByRole("textbox", { name: /Question/i }), "What did the Panel find?");
    await user.click(screen.getByRole("button", { name: /Retrieve and answer/i }));
    await user.click(screen.getByRole("button", { name: /Save as research note/i }));
    const calls = fetchMock.mock.calls as unknown as [string, RequestInit][];
    expect(calls.map(([url]) => new URL(url).pathname)).toEqual([
      "/api/v1/ai/runs",
      `/api/v1/ai/runs/${aiRun.id}/notes`,
    ]);
    expect(calls.every(([, init]) => !new Headers(init.headers).has("authorization"))).toBe(true);
    expect(calls.every(([url]) => new URL(url).origin === window.location.origin)).toBe(true);
  });
});
