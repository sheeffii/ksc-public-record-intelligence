import "@/test/next-mocks";
import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { messagesEn, renderWithProviders } from "@/test/render";
import { DirectoryScreen } from "./DirectoryScreen";
import { WitnessDossierScreen } from "./DossierScreens";
import {
  AiResearchScreen,
  AppealScreen,
  EvidencePathScreen,
  NetworkScreen,
} from "./ResearchScreens";

describe("Phase 5 safety contracts", () => {
  it("renders a protected witness by code without identity-bearing fields", () => {
    const { container } = renderWithProviders(<WitnessDossierScreen code="W01234" />);
    expect(screen.getAllByText("W01234").length).toBeGreaterThan(0);
    expect(screen.getByText(messagesEn.protection.title)).toBeInTheDocument();
    expect(container).not.toHaveTextContent("Demo Public Witness");
    expect(container.querySelector("img")).toBeNull();
  });

  it("renders the network neutrality disclaimer and cited edge inspector", () => {
    renderWithProviders(<NetworkScreen />);
    expect(screen.getAllByText(messagesEn.footer.network).length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText(messagesEn.phase5.whyConnection)).toBeInTheDocument();
    expect(screen.getByText("Exhibit P00123 · p. 4")).toBeInTheDocument();
  });

  it("renders the evidence path constraint and non-inference card", () => {
    renderWithProviders(<EvidencePathScreen />);
    expect(screen.getByText(messagesEn.phase5.pathBanner)).toBeInTheDocument();
    expect(screen.getByText(messagesEn.phase5.cannotTell)).toBeInTheDocument();
    expect(screen.getByText(messagesEn.phase5.pathLimit)).toBeInTheDocument();
  });

  it("keeps record blocks above the AI boundary", () => {
    const { container } = renderWithProviders(<AiResearchScreen />);
    const record = container.querySelector("[data-record-block]");
    const boundary = container.querySelector("[data-provenance-boundary]");
    const ai = container.querySelector("[data-ai-analysis-block]");
    expect(record?.compareDocumentPosition(boundary!)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
    expect(boundary?.compareDocumentPosition(ai!)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
  });

  it("contains no predictive appeal controls", () => {
    const { container } = renderWithProviders(<AppealScreen />);
    expect(container).not.toHaveTextContent(/success probability|appeal risk|strength score/i);
    expect(container).toHaveTextContent(messagesEn.phase5.noPrediction);
  });
});

it("directory screens render the approved table controls", () => {
  renderWithProviders(<DirectoryScreen kind="people" screenTitle="People" />);
  expect(screen.getByRole("table")).toBeInTheDocument();
  expect(screen.getByRole("searchbox")).toBeInTheDocument();
  expect(screen.getByRole("radiogroup", { name: messagesEn.table.density })).toBeInTheDocument();
});
