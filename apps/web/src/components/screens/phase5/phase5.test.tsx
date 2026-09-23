import "@/test/next-mocks";
import { fireEvent, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { messagesEn, renderWithProviders } from "@/test/render";
import { exhibitCitation, mockRepository } from "@/mock";
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
    expect(screen.getByText(messagesEn.phase5.graphTextAlternative)).toBeInTheDocument();
    expect(screen.getByText("Exhibit P00123 · p. 4")).toBeInTheDocument();
  });

  it("supports network search, isolate, collapse, and reset controls", async () => {
    const user = userEvent.setup();
    renderWithProviders(<NetworkScreen />);
    const graph = screen.getByRole("region", { name: messagesEn.phase5.network });
    const search = screen.getByRole("textbox", { name: messagesEn.phase5.searchWithin });

    await user.type(search, "W01234");
    expect(search).toHaveValue("W01234");

    const isolate = screen.getByRole("button", { name: messagesEn.phase5.isolate });
    await user.click(isolate);
    expect(isolate).toHaveAttribute("aria-pressed", "true");

    await user.click(screen.getByRole("button", { name: messagesEn.phase5.collapseGraph }));
    expect(within(graph).queryByRole("button", { name: "Illustrative finding" })).toBeNull();

    await user.click(screen.getByRole("button", { name: messagesEn.phase5.reset }));
    expect(search).toHaveValue("");
    expect(isolate).toHaveAttribute("aria-pressed", "false");
    expect(within(graph).getByRole("button", { name: "Illustrative finding" })).toBeInTheDocument();

    const inspectorToggle = screen.getByRole("button", { name: "peek" });
    await user.click(inspectorToggle);
    expect(screen.getByRole("button", { name: "half" })).toBeInTheDocument();
  });

  it("filters real network edges by both date-range bounds", () => {
    const { container } = renderWithProviders(
      <NetworkScreen
        initialNetwork={{
          nodes: [
            { id: "a", label: "A", type: "court", x: 10, y: 10, entityKind: "document" },
            { id: "b", label: "B", type: "court", x: 40, y: 40, entityKind: "document" },
            { id: "c", label: "C", type: "court", x: 70, y: 70, entityKind: "document" },
          ],
          edges: [
            {
              id: "old",
              from: "a",
              to: "b",
              relation: "cited_in",
              sourceType: "court",
              citation: exhibitCitation,
              verification: "verified",
              relationshipDate: "2024-01-01",
            },
            {
              id: "new",
              from: "b",
              to: "c",
              relation: "cited_in",
              sourceType: "court",
              citation: exhibitCitation,
              verification: "verified",
              relationshipDate: "2025-01-01",
            },
          ],
        }}
      />,
    );
    expect(container.querySelectorAll("main svg line")).toHaveLength(2);
    fireEvent.change(screen.getByRole("slider", { name: messagesEn.phase5b.from }), {
      target: { value: "2025" },
    });
    expect(container.querySelectorAll("main svg line")).toHaveLength(1);
    fireEvent.change(screen.getByRole("slider", { name: messagesEn.phase5b.from }), {
      target: { value: "2024" },
    });
    expect(container.querySelectorAll("main svg line")).toHaveLength(2);
    fireEvent.change(screen.getByRole("slider", { name: messagesEn.phase5b.to }), {
      target: { value: "2024" },
    });
    expect(container.querySelectorAll("main svg line")).toHaveLength(1);
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
  renderWithProviders(
    <DirectoryScreen
      kind="people"
      screenTitle="People"
      initialRows={mockRepository.getDirectory("people")}
    />,
  );
  expect(screen.getByRole("table")).toBeInTheDocument();
  expect(screen.getByRole("searchbox")).toBeInTheDocument();
  expect(screen.getByRole("radiogroup", { name: messagesEn.table.density })).toBeInTheDocument();
});
