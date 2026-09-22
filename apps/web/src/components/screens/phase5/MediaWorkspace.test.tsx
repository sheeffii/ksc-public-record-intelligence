import "@/test/next-mocks";
import { screen } from "@testing-library/react";
import type { MediaWorkspaceView } from "@/data";
import { renderWithProviders } from "@/test/render";
import { MediaWorkspace } from "./MediaWorkspace";

const workspace: MediaWorkspaceView = {
  items: [
    {
      id: "media-1",
      title: "Public report",
      publisher: "Public publisher",
      canonicalUrl: "https://example.org/public-report",
      publishedAt: "2024-07-23T07:34:00+02:00",
      capturedAt: "2026-09-22T15:00:00+02:00",
      sourceType: "news_report",
      language: "en",
      courtStatuses: ["external_only"],
      verification: "verified",
    },
  ],
  comparisons: [
    {
      id: "comparison-1",
      key: "comparison-1",
      title: "Different contexts",
      classification: "not_comparable",
      statementA: "First exact public excerpt.",
      statementB: "Second exact public excerpt.",
      explanation: "The excerpts concern different subjects and dates.",
      verification: "verified",
    },
  ],
  coverage: {
    sources: 1,
    items: 1,
    statements: 1,
    courtLinks: 1,
    citationBackedCourtLinks: 0,
    comparisons: 0,
  },
  taxonomy: [
    "external_only",
    "mentioned",
    "tendered",
    "admitted",
    "rejected",
    "discussed",
    "relied_upon",
    "unknown",
  ],
  limitations: ["Small controlled sample; no comprehensive social-platform collection."],
};

it("labels external-only material and exposes all separate search modes", () => {
  renderWithProviders(<MediaWorkspace workspace={workspace} />);
  expect(screen.getAllByText("EXTERNAL PUBLIC SOURCE").length).toBeGreaterThan(0);
  expect(screen.getAllByText("EXTERNAL ONLY")).toHaveLength(2);
  expect(screen.getByRole("option", { name: "Court Record Only" })).toBeInTheDocument();
  expect(screen.getByRole("option", { name: "External Public Sources" })).toBeInTheDocument();
  expect(screen.getByRole("option", { name: "Both — clearly separated" })).toBeInTheDocument();
  expect(screen.getByText("NOT COMPARABLE")).toBeInTheDocument();
});

it("renders court and external results in different panels in combined mode", () => {
  renderWithProviders(
    <MediaWorkspace
      workspace={workspace}
      scope="both"
      courtResults={[
        {
          id: "F00001",
          category: "documents",
          title: "Court filing",
          context: "filing",
          href: "/documents/F00001",
        },
      ]}
    />,
  );
  expect(screen.getByText("External public sources")).toBeInTheDocument();
  expect(screen.getByText("Court-record results")).toBeInTheDocument();
  expect(screen.getByText("COURT RECORD")).toBeInTheDocument();
});
