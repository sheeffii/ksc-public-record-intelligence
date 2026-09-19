import type { Citation } from "@ksc/shared";
import { SOURCE_TYPES, VERIFICATION_STATES } from "@ksc/shared";
import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { messagesEn, messagesSq, renderWithProviders } from "@/test/render";
import { CitationChip } from "./CitationChip";
import { ProvenanceBoundary } from "./ProvenanceBoundary";
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
