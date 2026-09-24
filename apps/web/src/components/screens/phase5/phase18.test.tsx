import "@/test/next-mocks";
import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderWithProviders } from "@/test/render";
import { DirectoryScreen } from "./DirectoryScreen";
import { RealWitnessScreen } from "./RealRecordScreens";
import { NetworkScreen } from "./ResearchScreens";

const counts = {
  documentMentions: 6,
  transcriptMentions: 10,
  exhibitRefs: 0,
  findings: 1,
  witnessesWhoReferred: 0,
  incidents: 0,
  citationsResolved: 6,
};

describe("Phase 18 research presentation", () => {
  it("shows separate source-backed activity counts for people", () => {
    renderWithProviders(
      <DirectoryScreen
        kind="people"
        screenTitle="People"
        initialRows={[
          {
            id: "public-person",
            title: "Public Person",
            kind: "people",
            description: "public role",
            date: "—",
            references: 22,
            verification: "unreviewed",
            href: "/people/public-person",
            counts,
            relationshipCount: 4,
          },
        ]}
      />,
    );
    expect(screen.getAllByText("Documents").length).toBeGreaterThan(0);
    expect(screen.getByText("Transcript occurrences")).toBeInTheDocument();
    expect(screen.getByText("Relationships")).toBeInTheDocument();
  });

  it("renders UNKNOWN exhibit status as explicit uncertainty", () => {
    renderWithProviders(
      <DirectoryScreen
        kind="exhibits"
        screenTitle="Evidence Explorer"
        initialRows={[
          {
            id: "P00001",
            title: "Exhibit P00001",
            kind: "exhibits",
            description: "Public exhibit projection",
            date: "—",
            references: 1,
            verification: "unreviewed",
            href: "/exhibits",
            status: "unknown",
            counts,
          },
        ]}
      />,
    );
    expect(screen.getAllByText("UNKNOWN").length).toBeGreaterThan(0);
    expect(screen.getByText(/no admission, rejection, or tender status/i)).toBeInTheDocument();
  });

  it("keeps protected witness research code-only while exposing record activity", () => {
    renderWithProviders(
      <RealWitnessScreen
        dossier={{
          witness: { code: "W00016", protected: true, protectiveMeasures: [] },
          counts,
          relationshipCount: 6,
        }}
      />,
    );
    expect(screen.getAllByText("W00016").length).toBeGreaterThan(0);
    expect(screen.getByText("Exact source navigation")).toBeInTheDocument();
    expect(screen.getByText(/No private identity is inferred/i)).toBeInTheDocument();
  });

  it("bounds dense network lists to a progressive working window", () => {
    const nodes = Array.from({ length: 150 }, (_, index) => ({
      id: `node-${index}`,
      label: `Record ${index}`,
      type: "court" as const,
      entityKind: "document",
      x: 50,
      y: 50,
    }));
    renderWithProviders(
      <NetworkScreen
        initialNetwork={{
          nodes,
          edges: [
            {
              id: "edge-1",
              from: "node-0",
              to: "node-1",
              relation: "cited_in",
              sourceType: "court",
              verification: "verified",
              citation: {
                sourceType: "court",
                ref: "F00001",
                docId: "F00001",
                resolved: true,
                display: "F00001 · p. 1",
              },
            },
          ],
        }}
      />,
    );
    expect(screen.getAllByText("Record 0").length).toBeGreaterThan(0);
    expect(screen.queryByText("Record 149")).not.toBeInTheDocument();
  });
});
