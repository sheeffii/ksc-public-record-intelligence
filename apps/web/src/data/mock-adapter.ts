import type { MockRepository } from "@/mock/types";
import { mockRepository } from "@/mock/repository";
import type { ResearchRepository } from "./contract";

/** Explicit test/story/visual-QA adapter. Never the production default. */
export function createMockRepositoryAdapter(
  source: MockRepository = mockRepository,
): ResearchRepository {
  return {
    getDirectory: async (kind) => source.getDirectory(kind),
    getPerson: async (slug) => source.getPerson(slug),
    getWitness: async (code) => source.getWitness(code),
    getIncident: async (slug) => {
      const row = source.getDirectory("incidents").find((item) => item.id === slug);
      if (!row) return null;
      return {
        slug,
        title: row.title,
        summary: row.description,
        datePrecision: "unknown",
        charges: [],
        counts: {
          documentMentions: 0,
          transcriptMentions: 0,
          exhibitRefs: 0,
          findings: 0,
          witnessesWhoReferred: 0,
          incidents: 0,
          citationsResolved: 0,
        },
      };
    },
    getDocument: async (id) => source.getDocument(id),
    getFinding: async () => null,
    search: async (query) => source.search(query),
    getNetwork: async () => source.getNetwork(),
    getPath: async () => source.getPath(),
    getTimeline: async () => source.getTimeline(),
    getEvidence: async () => source.getEvidence(),
    getAnswer: async () => source.getAnswer(),
    createAiRun: async () => {
      throw new Error("AI runs are unavailable in demo mode");
    },
    getAiRun: async () => null,
    listAiRuns: async () => [],
    saveAiRunAsNote: async () => {
      throw new Error("AI research notes are unavailable in demo mode");
    },
    listAppealIssues: async () => ({
      issues: [],
      coverage: {
        issues: 0,
        sourceBackedLinks: 0,
        comparisons: 0,
        redTeamReviews: 0,
        citationsResolved: 0,
        citationsUnresolved: 0,
        humanVerifiedRelationships: 0,
        needsMoreEvidence: 0,
      },
      limitations: [],
    }),
    getAppealIssue: async () => null,
    getArgumentLab: async () => null,
    listStatementComparisons: async () => [],
    getMediaWorkspace: async () => ({
      items: [],
      comparisons: [],
      coverage: {
        sources: 0,
        items: 0,
        statements: 0,
        courtLinks: 0,
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
      limitations: [],
    }),
  };
}
