import type { Citation } from "@ksc/shared";
import { SOURCE_TYPES, VERIFICATION_STATES } from "@ksc/shared";
import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { messagesEn, messagesSq, renderWithProviders } from "@/test/render";
import { CitationChip } from "./CitationChip";
import { AiAnalysisBlock } from "./AiAnalysisBlock";
import { DirectionBadge, ScopeNote } from "./DirectionBadge";
import { ProtectionNotice } from "./ProtectionNotice";
import { ProvenanceBoundary } from "./ProvenanceBoundary";
import { RecordBlock } from "./RecordBlock";
import { ReferenceCountStrip } from "./ReferenceCountStrip";
import { SourceBadge } from "./SourceBadge";
import { VerificationBadge } from "./VerificationBadge";

describe("SourceBadge — the provenance vocabulary", () => {
  it.each(SOURCE_TYPES)(
    "renders the %s label from the string table with its token class",
    (type) => {
      renderWithProviders(<SourceBadge type={type} />);
      const badge = screen.getByText(messagesEn.source[type]).closest("[data-source]");
      expect(badge).toHaveAttribute("data-source", type);
      expect(badge?.className).toMatch(
        /text-(court|witness|spo|defence|doc|ai|incident|location|organisation)/,
      );
    },
  );

  it("renders Albanian labels without truncation classes", () => {
    renderWithProviders(<SourceBadge type="spo" />, { locale: "sq" });
    const badge = screen.getByText(messagesSq.source.spo).closest("[data-source]");
    expect(badge?.className).toContain("whitespace-normal");
    expect(badge?.className).not.toContain("truncate");
  });
});

describe("VerificationBadge — five glyph-differentiated states", () => {
  it.each(VERIFICATION_STATES)("renders %s with a glyph and label", (state) => {
    renderWithProviders(<VerificationBadge state={state} />);
    const badge = screen.getByText(messagesEn.verification[state]).closest("[data-verification]");
    expect(badge).toHaveAttribute("data-verification", state);
    expect(badge?.querySelector("svg")).toBeInTheDocument();
  });
});

const resolved: Citation = {
  sourceType: "court",
  ref: "Judgment",
  docId: "F00482",
  page: 894,
  paraFrom: 8421,
  paraTo: 8427,
  resolved: true,
  display: "Judgment · ¶8421–8427",
};

describe("CitationChip — resolves or does not render", () => {
  it("renders a navigable chip deep-linking to the reader at page and paragraph", () => {
    renderWithProviders(<CitationChip citation={resolved} />);
    const link = screen.getByRole("link");
    expect(link).toHaveTextContent("Judgment · ¶8421–8427");
    expect(link).toHaveAttribute("href", "/documents/F00482?page=894&highlight=8421-8427");
    expect(link).toHaveClass("text-court");
  });

  it("renders nothing at all for an unresolved citation", () => {
    const { container } = renderWithProviders(
      <CitationChip citation={{ ...resolved, resolved: false }} />,
    );
    expect(container.querySelector("[data-citation]")).toBeNull();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(container).not.toHaveTextContent("Judgment");
  });

  it("can render as a non-navigable span", () => {
    renderWithProviders(<CitationChip citation={resolved} navigable={false} />);
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(screen.getByText("Judgment · ¶8421–8427")).toBeInTheDocument();
  });
});

describe("ProvenanceBoundary", () => {
  it("is a labelled separator carrying the required sentence", () => {
    renderWithProviders(<ProvenanceBoundary />);
    const sep = screen.getByRole("separator");
    expect(sep).toHaveAttribute("aria-label", messagesEn.provenance.boundary);
    expect(sep).toHaveTextContent(messagesEn.provenance.boundary);
  });
});

describe("record and AI block boundary", () => {
  it("renders record material in a solid source block", () => {
    renderWithProviders(
      <RecordBlock sourceType="court" citations={[resolved]}>
        Record words
      </RecordBlock>,
    );
    const block = screen.getByText("Record words").closest("[data-record-block]");
    expect(block).toHaveClass("border");
    expect(block).not.toHaveClass("border-dashed");
    expect(block).toHaveAttribute("data-source", "court");
  });

  it("labels software output and uses a dashed AI-only container", () => {
    renderWithProviders(
      <AiAnalysisBlock citations={[resolved]}>Generated analysis</AiAnalysisBlock>,
    );
    const block = screen.getByText("Generated analysis").closest("[data-ai-analysis-block]");
    expect(block).toHaveClass("border-dashed", "bg-ai-surface");
    expect(block).toHaveTextContent(messagesEn.provenance.aiHeader);
    expect(block).toHaveTextContent(messagesEn.source.ai);
  });
});

describe("protected witness and scoped direction", () => {
  it("states the code-only protection rule", () => {
    renderWithProviders(<ProtectionNotice />);
    expect(screen.getByRole("complementary")).toHaveTextContent(messagesEn.protection.title);
    expect(screen.getByRole("complementary")).toHaveTextContent("only the public witness code");
  });

  it("keeps direction paired with its claim scope note", () => {
    renderWithProviders(
      <>
        <DirectionBadge direction="qualifies" />
        <ScopeNote />
      </>,
    );
    expect(screen.getByText(messagesEn.direction.qualifies)).toBeInTheDocument();
    expect(screen.getByText(messagesEn.direction.scopeNote)).toBeInTheDocument();
  });
});

it("ReferenceCountStrip owns its neutrality disclaimer", () => {
  renderWithProviders(
    <ReferenceCountStrip
      counts={{
        documentMentions: 1,
        transcriptMentions: 2,
        exhibitRefs: 3,
        findings: 4,
        witnessesWhoReferred: 5,
        incidents: 6,
        citationsResolved: 7,
      }}
    />,
  );
  const strip = screen
    .getByText(messagesEn.referenceCounts.title)
    .closest("[data-reference-counts]");
  expect(strip).toHaveTextContent(messagesEn.referenceCounts.disclaimer);
});
