import type { AnswerBlock, Citation, ReferenceCounts, Witness } from "@ksc/shared";
import type {
  MockDirectory,
  MockDirectoryRow,
  MockDocument,
  MockEvidenceRow,
  MockNetworkEdge,
  MockNetworkNode,
  MockPathHop,
  MockPerson,
  MockSearchResult,
  MockTimelineItem,
} from "./types";

export const courtCitation: Citation = {
  sourceType: "court",
  ref: "F01234",
  docId: "F01234",
  page: 12,
  paraFrom: 45,
  paraTo: 46,
  resolved: true,
  display: "F01234 · ¶45–46",
};

export const transcriptCitation: Citation = {
  sourceType: "witness",
  ref: "W01234",
  docId: "T-DEMO-01",
  page: 24,
  lineFrom: 12,
  lineTo: 19,
  resolved: true,
  display: "Transcript · demo session · p. 24 · lines 12–19",
};

export const exhibitCitation: Citation = {
  sourceType: "exhibit",
  ref: "P00123",
  docId: "P00123",
  page: 4,
  resolved: true,
  display: "Exhibit P00123 · p. 4",
};

const baseCounts: ReferenceCounts = {
  documentMentions: 14,
  transcriptMentions: 8,
  exhibitRefs: 5,
  findings: 3,
  witnessesWhoReferred: 2,
  incidents: 1,
  citationsResolved: 31,
};

export const mockPerson: MockPerson = {
  slug: "demo-research-subject",
  displayName: "Demo Research Subject",
  role: "Illustrative public-record entity",
  aliases: ["Sample entity"],
  counts: baseCounts,
};

export const mockProtectedWitness: Witness = {
  code: "W01234",
  protected: true,
  protectiveMeasures: ["Code-only display", "No identity attributes held"],
};

export const mockPublicWitness: Witness = {
  code: "W04567",
  protected: false,
  protectiveMeasures: [],
  public: {
    displayName: "Demo Public Witness",
    statedOccupation: "Illustrative role",
    calledBy: "spo",
  },
};

export const mockDocument: MockDocument = {
  id: "F01234",
  title: "Illustrative public filing",
  type: "Public filing",
  language: "English",
  page: 12,
  citation: courtCitation,
  paragraphs: [
    {
      number: 45,
      text: "This demonstrative paragraph shows how court text is presented with an addressable paragraph number.",
    },
    {
      number: 46,
      text: "The wording is generic sample content and does not state a finding about any real person or event.",
    },
    { number: 47, text: "Source references remain visible beside the material they support." },
  ],
};

const directoryRows: Record<MockDirectory, readonly MockDirectoryRow[]> = {
  people: [
    {
      id: "demo-research-subject",
      title: "Demo Research Subject",
      kind: "people",
      description: "Illustrative public-record entity",
      date: "Demo",
      references: 31,
      verification: "verified",
      href: "/people/demo-research-subject",
    },
  ],
  witnesses: [
    {
      id: "W01234",
      title: "W01234",
      kind: "witnesses",
      description: "Protected Witness",
      date: "Demo",
      references: 18,
      verification: "verified",
      href: "/witnesses/W01234",
      protected: true,
    },
    {
      id: "W04567",
      title: "Demo Public Witness",
      kind: "witnesses",
      description: "Public witness example",
      date: "Demo",
      references: 9,
      verification: "unreviewed",
      href: "/witnesses/W04567",
    },
  ],
  documents: [
    {
      id: "F01234",
      title: "Illustrative public filing",
      kind: "documents",
      description: "Mock document with paragraph anchors",
      date: "Demo",
      references: 7,
      verification: "verified",
      href: "/documents/F01234",
    },
    {
      id: "T-DEMO-01",
      title: "Illustrative transcript",
      kind: "documents",
      description: "Mock transcript with line references",
      date: "Demo",
      references: 5,
      verification: "verified",
      href: "/documents/T-DEMO-01",
    },
  ],
  findings: [
    {
      id: "F-DEMO-01",
      title: "Illustrative finding",
      kind: "findings",
      description: "Generic sample finding for interface demonstration",
      date: "Demo",
      references: 12,
      verification: "verified",
      href: "/findings/F-DEMO-01",
    },
  ],
  exhibits: [
    {
      id: "P00123",
      title: "Illustrative exhibit",
      kind: "exhibits",
      description: "Generic sample record",
      date: "Demo",
      references: 4,
      verification: "verified",
      href: "/documents/P00123?page=4",
    },
  ],
  incidents: [
    {
      id: "I-DEMO-01",
      title: "Illustrative recorded event",
      kind: "incidents",
      description: "Neutral sample event used only to demonstrate layout",
      date: "Demo",
      references: 6,
      verification: "unreviewed",
      href: "/incidents/I-DEMO-01",
    },
  ],
};

export const mockSearchResults: readonly MockSearchResult[] = [
  {
    id: "demo-research-subject",
    category: "people",
    title: "Demo Research Subject",
    context: "Illustrative entity returned by a mock search.",
    href: "/people/demo-research-subject",
    citation: courtCitation,
  },
  {
    id: "W01234",
    category: "witnesses",
    title: "W01234",
    context: "Protected witness code; no identity attributes are held.",
    href: "/witnesses/W01234",
    citation: transcriptCitation,
  },
  {
    id: "F01234",
    category: "documents",
    title: "Illustrative public filing",
    context: "Mock result for a filing identifier.",
    href: "/documents/F01234?page=12&highlight=45-46",
    citation: courtCitation,
  },
  {
    id: "P00123",
    category: "exhibits",
    title: "Illustrative exhibit",
    context: "Mock result for an exhibit identifier.",
    href: "/documents/P00123?page=4",
    citation: exhibitCitation,
  },
  {
    id: "I-DEMO-01",
    category: "incidents",
    title: "Illustrative recorded event",
    context: "Generic event wording; no allegation about a real person.",
    href: "/incidents/I-DEMO-01",
  },
  {
    id: "F-DEMO-01",
    category: "findings",
    title: "Illustrative finding",
    context: "Generic finding wording for the approved interface.",
    href: "/findings/F-DEMO-01",
    citation: courtCitation,
  },
  {
    id: "LOC-DEMO",
    category: "locations",
    title: "Demo location",
    context: "Recorded variant matching is demonstrated without real case content.",
    href: "/search?q=demo+location",
  },
];

export const mockNetworkNodes: readonly MockNetworkNode[] = [
  { id: "demo-research-subject", label: "Demo Research Subject", type: "person", x: 18, y: 52 },
  { id: "P00123", label: "P00123", type: "exhibit", x: 42, y: 28 },
  { id: "I-DEMO-01", label: "Illustrative event", type: "incident", x: 62, y: 55 },
  { id: "W01234", label: "W01234", type: "protected", x: 82, y: 30 },
  { id: "F-DEMO-01", label: "Illustrative finding", type: "court", x: 86, y: 74 },
];

export const mockNetworkEdges: readonly MockNetworkEdge[] = [
  {
    id: "edge-1",
    from: "demo-research-subject",
    to: "P00123",
    relation: "Referenced in",
    sourceType: "exhibit",
    citation: exhibitCitation,
    verification: "verified",
  },
  {
    id: "edge-2",
    from: "P00123",
    to: "I-DEMO-01",
    relation: "Describes",
    sourceType: "exhibit",
    citation: exhibitCitation,
    verification: "verified",
  },
  {
    id: "edge-3",
    from: "I-DEMO-01",
    to: "W01234",
    relation: "Mentioned in testimony",
    sourceType: "witness",
    citation: transcriptCitation,
    verification: "verified",
  },
  {
    id: "edge-4",
    from: "W01234",
    to: "F-DEMO-01",
    relation: "Cited by",
    sourceType: "court",
    citation: courtCitation,
    verification: "verified",
  },
];

export const mockPath: readonly MockPathHop[] = mockNetworkEdges.map((edge, index) => ({
  ...edge,
  index: index + 1,
  date: "Demo date",
  dateType: index === 2 ? "testimony" : index === 3 ? "decision" : "document",
}));

export const mockTimeline: readonly MockTimelineItem[] = [
  {
    id: "event",
    label: "Illustrative historical event",
    date: "Demo event date",
    dateType: "event",
    href: "/incidents/I-DEMO-01",
  },
  {
    id: "document",
    label: "Illustrative document created",
    date: "Demo document date",
    dateType: "document",
    href: "/documents/P00123",
  },
  {
    id: "filing",
    label: "Illustrative document filed",
    date: "Demo filing date",
    dateType: "filing",
    href: "/documents/F01234",
  },
  {
    id: "testimony",
    label: "Illustrative testimony session",
    date: "Demo testimony date",
    dateType: "testimony",
    href: "/witnesses/W01234",
  },
  {
    id: "decision",
    label: "Illustrative decision",
    date: "Demo decision date",
    dateType: "decision",
    href: "/findings/F-DEMO-01",
  },
];

export const mockEvidence: readonly MockEvidenceRow[] = [
  {
    id: "e-1",
    claim: "The sample record contains a reference to the illustrative event.",
    direction: "supports",
    sourceType: "exhibit",
    citation: exhibitCitation,
    verification: "verified",
  },
  {
    id: "e-2",
    claim: "Another sample passage narrows the time described by the claim.",
    direction: "qualifies",
    sourceType: "witness",
    citation: transcriptCitation,
    verification: "unreviewed",
  },
  {
    id: "e-3",
    claim: "A separate sample passage points against the claim as stated.",
    direction: "contradicts",
    sourceType: "court",
    citation: courtCitation,
    verification: "needs-evidence",
  },
  {
    id: "e-4",
    claim: "This sample source addresses context without bearing on the claim.",
    direction: "neutral",
    sourceType: "defence",
    citation: courtCitation,
    verification: "unreviewed",
  },
];

export const mockAnswer: readonly AnswerBlock[] = [
  {
    kind: "court",
    text: "The sample finding records a narrowly framed conclusion for interface demonstration.",
    citations: [courtCitation],
  },
  {
    kind: "evidence",
    text: "The mock source set contains an exhibit and a transcript passage.",
    citations: [exhibitCitation],
  },
  {
    kind: "testimony",
    text: "The protected witness is displayed only by code.",
    citations: [transcriptCitation],
  },
  {
    kind: "spo",
    text: "The illustrative SPO position is shown as an argument, not a finding.",
    citations: [courtCitation],
  },
  {
    kind: "defence",
    text: "The illustrative Defence position is shown separately and with the same provenance treatment.",
    citations: [courtCitation],
  },
  {
    kind: "ai",
    text: "The mock analysis identifies where the sample sources address the question. It does not add facts or make a legal prediction.",
    citations: [courtCitation, exhibitCitation],
  },
];

export function getDirectoryRows(kind: MockDirectory): readonly MockDirectoryRow[] {
  return directoryRows[kind];
}
