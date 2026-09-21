import "@/test/next-mocks";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { aiRun, aiRunSummary, withheldAiRun } from "@/data/api/fixtures";
import { toAiRun, toAiRunSummary } from "@/data/api/mappers";
import { renderWithProviders } from "@/test/render";
import { AiResearchReal } from "./AiResearchReal";

describe("AiResearchReal", () => {
  it("shows verified sources before distinct record and AI answer blocks", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <AiResearchReal
        initialRun={toAiRun(aiRun)}
        sessions={[toAiRunSummary(aiRunSummary)]}
        apiBaseUrl="http://api.test/api/v1"
      />,
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
    renderWithProviders(
      <AiResearchReal initialRun={toAiRun(withheldAiRun)} sessions={[]} apiBaseUrl="" />,
    );
    expect(screen.getByText("Answer withheld")).toBeInTheDocument();
    expect(
      screen.getByText("The controlled corpus does not contain the public Trial Judgment."),
    ).toBeInTheDocument();
    expect(screen.queryByText("AI ANALYSIS")).not.toBeInTheDocument();
  });
});
