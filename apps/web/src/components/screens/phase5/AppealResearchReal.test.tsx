import "@/test/next-mocks";
import { screen } from "@testing-library/react";
import type { AppealIssueView, AppealWorkspaceView, ArgumentLabView } from "@/data";
import { renderWithProviders } from "@/test/render";
import { RealAppealScreen, RealArgumentLabScreen } from "./AppealResearchReal";

const source = {
  citation: {
    sourceType: "court" as const,
    ref: "KSC-BC-2020-06/F03752",
    docId: "F03752",
    paraFrom: 12,
    paraTo: 16,
    resolved: true,
    display: "F03752 · ¶¶12-16",
  },
  targetPath: "/documents/F03752?para=12",
  rawText: "F03752, paras 12-16",
  resolutionState: "resolved" as const,
};

const summary = {
  id: "issue-id",
  key: "PIR-F03752-AMENDMENTS-RECORD",
  category: "procedural_fairness",
  context: "procedural",
  title: "Completeness of the public record",
  description: "Potential Issue for Review: record incomplete and requires human review.",
  findingKey: "FD-F03752-P12-16",
  paraFrom: 12,
  paraTo: 16,
  courtTreatment: "addressed",
  courtTreatmentNote: "Court treatment is located; addressed does not assess correctness.",
  redTeamResult: "insufficient_record",
  verification: "needs-evidence" as const,
};

const workspace: AppealWorkspaceView = {
  issues: [summary],
  coverage: {
    issues: 1,
    sourceBackedLinks: 1,
    comparisons: 0,
    redTeamReviews: 1,
    citationsResolved: 1,
    citationsUnresolved: 0,
    humanVerifiedRelationships: 1,
    needsMoreEvidence: 1,
  },
  limitations: ["The public Trial Judgment is not held."],
};

const issue: AppealIssueView = {
  ...summary,
  sources: [
    {
      id: "source-id",
      sequence: 1,
      role: "court_reasoning",
      category: "court_finding",
      excerpt: "Exact Court passage.",
      verification: "verified",
      source,
    },
  ],
  missingMaterial: [
    {
      reference: "F03743",
      kind: "underlying filing",
      reason: "Source unavailable in controlled corpus.",
      state: "source_unavailable",
    },
  ],
  comparisons: [],
  redTeam: [],
  audit: {
    citationsTotal: 1,
    citationsResolved: 1,
    quotesVerified: 1,
    sourcesHumanVerified: 1,
    unresolved: 0,
    unsupportedRelationships: 0,
    readyForHumanReview: false,
    issues: ["Missing source: F03743"],
  },
};

it("renders real potential-issue provenance and explicit record gaps", () => {
  renderWithProviders(<RealAppealScreen workspace={workspace} issue={issue} />);
  expect(screen.getByText("Potential Issues for Review")).toBeInTheDocument();
  expect(screen.getByText("Exact Court passage.")).toBeInTheDocument();
  expect(screen.getByText("F03743")).toBeInTheDocument();
  expect(screen.getByText(/Not ready for human legal review/)).toBeInTheDocument();
  expect(screen.getByText("Insufficient record")).toBeInTheDocument();
});

it("keeps all three red-team perspectives visible without declaring a winner", () => {
  const lab: ArgumentLabView = {
    issue: summary,
    title: summary.title,
    draft: "Exact Defence passage.",
    citations: [source],
    unsupportedSentences: [],
    stages: [
      {
        sequence: 1,
        perspective: "defence_analyst",
        category: "well_supported",
        text: "Source-backed formulation.",
        verification: "verified",
        source,
      },
      {
        sequence: 2,
        perspective: "spo_red_team",
        category: "counter_material",
        text: "Court reasoning located.",
        verification: "verified",
        source,
      },
      {
        sequence: 3,
        perspective: "neutral_reviewer",
        category: "source_limitation",
        text: "Underlying filing missing.",
        verification: "verified",
      },
    ],
    result: "insufficient_record",
    notice: "The neutral reviewer does not declare a winner.",
  };
  renderWithProviders(<RealArgumentLabScreen lab={lab} />);
  expect(screen.getByText("Defence Analyst")).toBeInTheDocument();
  expect(screen.getByText("SPO Red Team")).toBeInTheDocument();
  expect(screen.getByText("Neutral Reviewer")).toBeInTheDocument();
  expect(screen.getAllByText(/does not declare a winner/).length).toBeGreaterThan(0);
});
