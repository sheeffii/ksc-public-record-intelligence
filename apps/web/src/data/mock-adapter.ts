import type { MockRepository } from "@/mock/types";
import { mockRepository } from "@/mock/repository";
import type { ResearchRepository } from "./contract";

/** The Phase 5 mock behind the asynchronous contract. Default in Phase 6. */
export function createMockRepositoryAdapter(
  source: MockRepository = mockRepository,
): ResearchRepository {
  return {
    getDirectory: async (kind) => source.getDirectory(kind),
    getPerson: async (slug) => source.getPerson(slug),
    getWitness: async (code) => source.getWitness(code),
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
  };
}
