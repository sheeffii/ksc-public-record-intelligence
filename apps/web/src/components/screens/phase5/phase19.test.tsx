import "@/test/next-mocks";
import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { EntityMention } from "@/data";
import { edgePage, appearances, statusEvents } from "@/data/api/fixtures";
import {
  toEdgePage,
  toEntityMention,
  toExhibitStatusEvent,
  toWitnessAppearance,
} from "@/data/api/mappers";
import { renderWithProviders } from "@/test/render";
import { DocumentReaderScreen } from "./ReaderSearchScreens";
import { RealExhibitScreen, RealPersonScreen, RealWitnessScreen } from "./RealRecordScreens";

const counts = {
  documentMentions: 1,
  transcriptMentions: 1,
  exhibitRefs: 0,
  findings: 0,
  witnessesWhoReferred: 0,
  incidents: 0,
  citationsResolved: 0,
};

const apiMention = {
  id: "m-1",
  entity_kind: "witness" as const,
  match_class: "VERIFIED_MENTION" as const,
  rule_id: "witness.code.exact",
  rule_version: 1,
  occurrence_text: "W00016",
  document_ref: "KSC-BC-2020-06/F02661",
  document_title: "Public Redacted Version of Joint Defence Response",
  version_ref: "KSC-BC-2020-06/F02661/RED",
  version_superseded: false,
  language: "en",
  char_anchor: "document_page_text" as const,
  char_start: 1412,
  char_end: 1418,
  pdf_page_index: 6,
  page: 7,
  paragraph: 19,
  line_from: null,
  line_to: null,
  source_url: null,
  target_path: "/documents/F02661?version=KSC-BC-2020-06%2FF02661%2FRED&pdfPage=6&para=19&page=7",
};

function mention(overrides: Partial<EntityMention>): EntityMention {
  return { ...toEntityMention(apiMention), ...overrides };
}

describe("Phase 19A verified mentions", () => {
  it("maps a persisted mention to an exact, resolved court-record citation", () => {
    const mapped = toEntityMention(apiMention);
    expect(mapped.matchClass).toBe("VERIFIED_MENTION");
    // The Reader link carries the verbatim slice so the exact span is marked.
    expect(mapped.href).toBe(`${apiMention.target_path}&hl=W00016`);
    expect(mapped.citation).toMatchObject({
      sourceType: "court",
      ref: "KSC-BC-2020-06/F02661/RED",
      docId: "F02661",
      page: 7,
      paraFrom: 19,
      resolved: true,
    });
    expect(mapped.citation.display).toBe("KSC-BC-2020-06/F02661/RED · p. 7 · ¶19");
  });

  it("keeps verified mentions, review-required mentions and search matches separate", () => {
    renderWithProviders(
      <RealPersonScreen
        person={{
          slug: "counsel_or_participant-smith",
          displayName: "Smith",
          role: "counsel_or_participant",
          aliases: ["MR. SMITH"],
          counts,
        }}
        mentions={{
          total: 2,
          items: [
            mention({ id: "v", occurrenceText: "JUDGE SMITH", ruleId: "role" }),
            mention({
              id: "r",
              matchClass: "REVIEW_REQUIRED",
              occurrenceText: "MR. SMITH",
              ruleId: "person.speaker_label.shared_surname",
            }),
          ],
        }}
        occurrences={[
          {
            id: "F00001",
            category: "documents",
            title: "Lexical hit",
            context: "Smith said",
            href: "/documents/F00001?page=2",
            citation: {
              sourceType: "court",
              ref: "F00001",
              docId: "F00001",
              page: 2,
              resolved: true,
              display: "F00001 · p. 2",
            },
            matchKind: "keyword",
          },
        ]}
      />,
    );
    const verified = screen.getByText("Verified mentions").closest("section") ?? document.body;
    expect(within(verified as HTMLElement).getByText("JUDGE SMITH")).toBeInTheDocument();
    expect(within(verified as HTMLElement).queryByText("MR. SMITH")).toBeNull();
    const review = screen.getByText("Mentions requiring review").closest("section");
    expect(review).not.toBeNull();
    expect(within(review as HTMLElement).getByText("MR. SMITH")).toBeInTheDocument();
    expect(within(review as HTMLElement).getByText("REVIEW REQUIRED")).toBeInTheDocument();
    expect(screen.getByText("Search matches")).toBeInTheDocument();
    expect(screen.getByText("SEARCH MATCH")).toBeInTheDocument();
    expect(screen.getByText(/They are not verified mentions/)).toBeInTheDocument();
  });

  it("shows a protected witness's verified mentions as the code only", () => {
    renderWithProviders(
      <RealWitnessScreen
        dossier={{
          witness: { code: "W00016", protected: true, protectiveMeasures: [] },
          counts,
          relationshipCount: 0,
        }}
        mentions={{ total: 120, items: [mention({})] }}
      />,
    );
    expect(screen.getByText("VERIFIED MENTION")).toBeInTheDocument();
    expect(screen.getByText("Showing 1 of 120 recorded mentions")).toBeInTheDocument();
    expect(screen.queryByText("Search matches")).toBeNull();
  });
});

describe("Phase 19C intelligence consumption", () => {
  const exhibit = {
    id: "P-DEMO-001",
    title: "P-DEMO-001",
    status: "unknown",
    visibility: "public",
    counts,
    relationshipCount: 0,
  };

  it("shows header-backed appearances with exact source and code-only identity", () => {
    renderWithProviders(
      <RealWitnessScreen
        dossier={{
          witness: { code: "W-DEMO-001", protected: true, protectiveMeasures: [] },
          counts,
          relationshipCount: 2,
        }}
        appearances={appearances.map(toWitnessAppearance)}
        network={toEdgePage(edgePage, {})}
      />,
    );
    const panel = screen.getByText("Hearings with a recorded public appearance").closest("section");
    expect(panel).not.toBeNull();
    const scope = within(panel as HTMLElement);
    expect(scope.getByText("1 hearing · 1 transcript version")).toBeInTheDocument();
    expect(scope.getByText("VERIFIED")).toBeInTheDocument();
    expect(scope.getByText(/open 30 · private 10 · closed 0/)).toBeInTheDocument();
    expect(scope.getByText("Witness: W-DEMO-001 (Open Session)")).toBeInTheDocument();
    expect(scope.getByRole("link", { name: "Open exact source" })).toHaveAttribute(
      "href",
      "/documents/transcript?document=T%2F2023-06-01&page=101&hl=Witness%3A%20W-DEMO-001%20(Open%20Session)",
    );
    // The fallback note is replaced only when stored appearances exist.
    expect(screen.queryByText(/No hearing with a recorded public appearance/)).toBeNull();
    // Typed relationships carry their evidence kind, count and the page total.
    expect(screen.getByText("Transcript appearance header · 2 source anchors")).toBeInTheDocument();
    expect(screen.getByText(/Showing 1 of 250 relationships/)).toBeInTheDocument();
  });

  it("keeps a witness without stored appearances on the no-estimate note", () => {
    renderWithProviders(
      <RealWitnessScreen
        dossier={{
          witness: { code: "W-DEMO-009", protected: true, protectiveMeasures: [] },
          counts,
          relationshipCount: 0,
        }}
      />,
    );
    expect(screen.getByText(/No hearing with a recorded public appearance/)).toBeInTheDocument();
    expect(screen.queryByText("Hearings with a recorded public appearance")).toBeNull();
  });

  it("shows UNKNOWN status with no inferred history", () => {
    renderWithProviders(
      <RealExhibitScreen exhibit={exhibit} occurrences={[]} network={{ nodes: [], edges: [] }} />,
    );
    expect(screen.getAllByText("UNKNOWN").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText(/The status is not inferred/)).toBeInTheDocument();
  });

  it("lists each status event with the court statement that establishes it", () => {
    renderWithProviders(
      <RealExhibitScreen
        exhibit={{ ...exhibit, status: "admitted" }}
        occurrences={[]}
        network={{ nodes: [], edges: [] }}
        statusEvents={statusEvents.map(toExhibitStatusEvent)}
      />,
    );
    const panel = screen.getByText("Status history").closest("section");
    const scope = within(panel as HTMLElement);
    expect(scope.getByText("Admitted")).toBeInTheDocument();
    expect(scope.getByText("stated 2023-06-01")).toBeInTheDocument();
    expect(scope.getByText("P-DEMO-001 is admitted")).toBeInTheDocument();
    expect(scope.getByText("exhibit.bench_statement.admitted")).toBeInTheDocument();
    expect(screen.queryByText("UNKNOWN")).toBeNull();
  });
});

describe("Phase 19C exact-source Reader", () => {
  it("marks the verbatim slice only inside the targeted paragraph", () => {
    const { container } = renderWithProviders(
      <DocumentReaderScreen
        id="F00001"
        initialPage={2}
        initialPara={13}
        highlight={"Hashim\nThaçi"}
        initialDocument={{
          id: "F00001",
          title: "Public filing",
          type: "decision",
          language: "en",
          page: 2,
          paragraphs: [
            { number: 12, page: 2, pdfPageIndex: 1, text: "Hashim Thaçi in another paragraph." },
            { number: 13, page: 2, pdfPageIndex: 1, text: "Counsel for Hashim Thaçi and Thaçit." },
          ],
          citation: {
            sourceType: "court",
            ref: "F00001",
            docId: "F00001",
            resolved: true,
            display: "F00001 · ¶13",
          },
          visibility: "public",
          pageCount: 3,
          versionRef: "F00001",
          artifactStatus: "fetched",
        }}
      />,
    );
    const marks = container.querySelectorAll("mark[data-exact-source]");
    expect([...marks].map((mark) => mark.textContent)).toEqual(["Hashim Thaçi"]);
    expect(marks[0]?.closest("p")?.id).toBe("para-13");
  });

  it("navigates by PDF index when a link carries both pdfPage and printed page", () => {
    const { container } = renderWithProviders(
      <DocumentReaderScreen
        id="F00002/A01"
        initialPage={5}
        initialPdfPage={4}
        initialPara={10}
        highlight="Jakup KRASNIQI"
        initialDocument={{
          id: "F00002/A01",
          title: "Annex",
          type: "filing_annex",
          language: "en",
          page: 5,
          paragraphs: [
            { number: 10, page: 5, pdfPageIndex: 4, text: "Jakup KRASNIQI, born 1951." },
            {
              number: 13,
              page: 5,
              pageTo: 6,
              pdfPageIndex: 4,
              pdfPageIndexTo: 5,
              text: "In 1989.",
            },
            { number: 14, page: 6, pdfPageIndex: 5, text: "Jakup KRASNIQI later." },
          ],
          citation: {
            sourceType: "court",
            ref: "F00002/A01",
            docId: "F00002/A01",
            resolved: true,
            display: "F00002/A01 · ¶10",
          },
          visibility: "public_redacted",
          pageCount: 8,
          versionRef: "F00002/RED/A01",
          artifactStatus: "fetched",
        }}
      />,
    );
    expect(container.querySelector("#para-10 mark[data-exact-source]")).not.toBeNull();
    expect(container.querySelector("#para-14")).toBeNull();
    expect(container.querySelector("[data-exact-source-outside]")).toBeNull();
  });

  it("states when the exact span is outside the rendered paragraphs", () => {
    const { container } = renderWithProviders(
      <DocumentReaderScreen
        id="T/2024-04-29"
        initialPage={14987}
        highlight="Witness: W03877 (Open Session)"
        initialDocument={{
          id: "T/2024-04-29",
          title: "Transcript",
          type: "transcript",
          language: "en",
          page: 14987,
          paragraphs: [{ page: 14987, pdfPageIndex: 3, text: "Q. Good morning." }],
          citation: {
            sourceType: "court",
            ref: "T/2024-04-29",
            docId: "T/2024-04-29",
            resolved: true,
            display: "T/2024-04-29 · p. 14987",
          },
          visibility: "public_redacted",
          pageCount: 139,
          versionRef: "T/2024-04-29",
          artifactStatus: "fetched",
        }}
      />,
    );
    expect(container.querySelector("mark[data-exact-source]")).toBeNull();
    expect(container.querySelector("[data-exact-source-outside]")?.textContent).toContain(
      "Witness: W03877 (Open Session)",
    );
  });
});
