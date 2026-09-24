import "@/test/next-mocks";
import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { EntityMention } from "@/data";
import { toEntityMention } from "@/data/api/mappers";
import { renderWithProviders } from "@/test/render";
import { RealPersonScreen, RealWitnessScreen } from "./RealRecordScreens";

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
    expect(mapped.href).toBe(apiMention.target_path);
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
