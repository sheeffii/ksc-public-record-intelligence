import "@/test/next-mocks";
import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { findingDetail } from "@/data/api/fixtures";
import { toFinding } from "@/data/api/mappers";
import { renderWithProviders } from "@/test/render";
import { RealFindingDetailScreen } from "./FindingDetailReal";

describe("RealFindingDetailScreen", () => {
  it("keeps Court, party, human and AI provenance categories distinct", () => {
    renderWithProviders(<RealFindingDetailScreen finding={toFinding(findingDetail)} />);
    expect(screen.getByRole("heading", { name: /COURT FINDING/ })).toBeInTheDocument();
    expect(screen.getByText("SPO / DEFENCE ARGUMENTS")).toBeInTheDocument();
    expect(screen.getByText("HUMAN NOTE")).toBeInTheDocument();
    expect(screen.getByText("AI ANALYSIS")).toBeInTheDocument();
    expect(screen.getByText("No AI analysis is generated in Phase 10.")).toBeInTheDocument();
    expect(screen.getByText(/Underlying public filing F-DEMO-MISSING/)).toBeInTheDocument();
  });

  it("renders exact source navigation and the neutral corroboration limitation", () => {
    renderWithProviders(<RealFindingDetailScreen finding={toFinding(findingDetail)} />);
    const sourceLinks = screen.getAllByRole("link", { name: "Open exact source" });
    expect(sourceLinks[0]).toHaveAttribute("href", expect.stringContaining("anchor="));
    expect(screen.getByRole("link", { name: "View Evidence Path" })).toHaveAttribute(
      "href",
      expect.stringContaining("/network/path?from="),
    );
    expect(
      screen.getByText(
        "No additional corroborating source has been identified in the indexed public record.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/there was no evidence/i)).not.toBeInTheDocument();
  });
});
