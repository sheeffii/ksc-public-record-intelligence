import {
  getDirectoryRows,
  mockAnswer,
  mockDocument,
  mockEvidence,
  mockNetworkEdges,
  mockNetworkNodes,
  mockPath,
  mockPerson,
  mockProtectedWitness,
  mockPublicWitness,
  mockSearchResults,
  mockTimeline,
} from "./data";
import type { MockRepository } from "./types";

/** Phase 5 adapter. Screens depend on this contract, not scattered mock objects. */
export const mockRepository: MockRepository = {
  getDirectory: getDirectoryRows,
  getPerson: (slug) => ({ ...mockPerson, slug }),
  getWitness: (code) =>
    code === mockProtectedWitness.code ? mockProtectedWitness : { ...mockPublicWitness, code },
  getDocument: (id) => ({ ...mockDocument, id }),
  search: (query) => {
    const needle = query.trim().toLocaleLowerCase();
    if (!needle) return mockSearchResults;
    const matched = mockSearchResults.filter((item) =>
      `${item.id} ${item.title} ${item.context}`.toLocaleLowerCase().includes(needle),
    );
    return matched.length ? matched : mockSearchResults;
  },
  getNetwork: () => ({ nodes: mockNetworkNodes, edges: mockNetworkEdges }),
  getPath: () => mockPath,
  getTimeline: () => mockTimeline,
  getEvidence: () => mockEvidence,
  getAnswer: () => mockAnswer,
};
