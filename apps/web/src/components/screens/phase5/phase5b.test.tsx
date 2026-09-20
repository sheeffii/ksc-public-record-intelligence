import "@/test/next-mocks";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { messagesEn, renderWithProviders } from "@/test/render";
import { DirectoryScreen } from "./DirectoryScreen";
import { PersonDossierScreen, WitnessDossierScreen } from "./DossierScreens";
import {
  DocumentReaderScreen,
  SearchScreen,
  StatementComparisonScreen,
} from "./ReaderSearchScreens";
import {
  AppealScreen,
  ArgumentLabScreen,
  FindingDetailScreen,
  IncidentScreen,
  PublicScreen,
  TimelineScreen,
} from "./ResearchScreens";

const tb = messagesEn.phase5b;

describe("Phase 5B visual-parity remediation", () => {
  it("directory filters, sorts, paginates and exports the demo volume", async () => {
    const user = userEvent.setup();
    renderWithProviders(<DirectoryScreen kind="witnesses" screenTitle="Witnesses" />);
    const table = screen.getByRole("table");
    expect(within(table).getAllByRole("row").length).toBe(11); // header + 10 rows
    expect(screen.getAllByText("1–10 of 26").length).toBe(2);
    await user.click(screen.getByRole("button", { name: tb.nextPage }));
    expect(screen.getAllByText("11–20 of 26").length).toBe(2);
    await user.click(screen.getByRole("checkbox", { name: /Protected only/ }));
    expect(screen.getAllByText(/1–10 of 17/).length).toBe(2);
    await user.click(screen.getByRole("button", { name: /Remove filter: Protected only/ }));
    await user.type(screen.getByRole("searchbox"), "W02003");
    expect(within(screen.getByRole("table")).getAllByRole("row").length).toBe(2);
    expect(screen.getByRole("link", { name: tb.exportCsv })).toHaveAttribute("download");
    await user.clear(screen.getByRole("searchbox"));
    await user.type(screen.getByRole("searchbox"), "zzz-none");
    expect(screen.getByText(tb.noMatch)).toBeInTheDocument();
  }, 10_000);

  it("search groups results with category counts, filters and a query interpretation", async () => {
    const user = userEvent.setup();
    const { unmount } = renderWithProviders(<SearchScreen initialQuery="W01234" />);
    expect(screen.getByText(`${tb.identifier} W#####`)).toBeInTheDocument();
    unmount();
    renderWithProviders(<SearchScreen initialQuery="demo" />);
    expect(screen.getAllByText(tb.freeText).length).toBeGreaterThan(0);
    expect(screen.getByText(tb.rankingDisclaimer)).toBeInTheDocument();
    await user.click(screen.getByRole("checkbox", { name: /^court/ }));
    expect(screen.getByRole("heading", { name: tb.people })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: tb.witnesses })).toBeNull();
  });

  it("person dossier has the designed header, quick actions, ten tabs and no score", () => {
    renderWithProviders(<PersonDossierScreen slug="demo-research-subject" />);
    for (const name of ["View Network", "View Timeline", "Find Record Connection", "Ask AI"]) {
      expect(screen.getByRole("link", { name })).toBeInTheDocument();
    }
    expect(screen.getAllByRole("tab").length).toBe(10);
    expect(screen.getByText(tb.recordReferences)).toBeInTheDocument();
    expect(screen.getByText(tb.noScore)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: tb.sortJudgmentOrder })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("witness dossier renders both header states without identity for a protected code", () => {
    const { container } = renderWithProviders(<WitnessDossierScreen code="W01234" />);
    expect(screen.getByRole("region", { name: tb.headerProtected })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: tb.headerPublic })).toBeInTheDocument();
    expect(container).not.toHaveTextContent("Demo Public Witness");
    expect(screen.getAllByText(tb.chronology).length).toBeGreaterThan(0);
    expect(screen.getByText(tb.noPriorStatement)).toBeInTheDocument();
  });

  it("statement comparison keeps three columns, a label picker and the Chamber attribution", async () => {
    const user = userEvent.setup();
    renderWithProviders(<StatementComparisonScreen code="W01234" />);
    for (const col of [tb.columnA, tb.columnB, tb.columnC])
      expect(screen.getByText(col)).toBeInTheDocument();
    expect(screen.getByText(tb.chamberAssessment)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: tb.markReviewed }));
    expect(screen.getByRole("button", { name: tb.reviewed })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await user.click(screen.getByRole("button", { name: "Next" }));
    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.getByText(tb.silent)).toBeInTheDocument();
  });

  it("timeline draws seven toggleable lanes, keeps empty lanes visible and opens card detail", async () => {
    const user = userEvent.setup();
    renderWithProviders(<TimelineScreen />);
    const lanes = Object.values(tb.lanes);
    for (const lane of lanes)
      expect(screen.getByRole("button", { name: lane })).toBeInTheDocument();
    expect(screen.getAllByText(tb.emptyLane).length).toBeGreaterThan(0);
    await user.click(screen.getByRole("button", { name: tb.lanes.judgment }));
    expect(screen.getByRole("button", { name: tb.lanes.judgment })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    expect(screen.getAllByText(tb.dateMergeNote).length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText(tb.attachedDates)).toBeInTheDocument();
  });

  it("incident matrix filters by direction and court-cited and carries the required notes", async () => {
    const user = userEvent.setup();
    renderWithProviders(<IncidentScreen id="I-DEMO-01" />);
    expect(screen.getAllByText(tb.matrixNote).length).toBeGreaterThan(0);
    expect(screen.getByText(messagesEn.phase5.chargeNote)).toBeInTheDocument();
    const before = screen.getAllByRole("row").length;
    await user.click(screen.getByRole("radio", { name: tb.contradicts }));
    expect(screen.getAllByRole("row").length).toBeLessThan(before);
  });

  it("finding detail renders the nine-step chain in order with a scroll-spy rail", () => {
    renderWithProviders(<FindingDetailScreen id="F-DEMO-01" />);
    const rail = screen.getByRole("navigation", { name: tb.chainIndex });
    expect(rail.querySelectorAll("ol > li").length).toBe(9);
    const headings = screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent ?? "");
    const order = [
      "Court Finding",
      "Evidence Relied Upon",
      "What Those Sources Say",
      "Source Audit",
    ].map((label) => headings.findIndex((h) => h.includes(label)));
    expect(order).toEqual([...order].sort((a, b) => a - b));
    expect(screen.getByRole("link", { name: "Send to Argument Lab" })).toBeInTheDocument();
  });

  it("appeal issues expand, take a review state and keep the will-not-do card", async () => {
    const user = userEvent.setup();
    renderWithProviders(<AppealScreen />);
    expect(screen.getByText(tb.willNotDo)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: tb.markReviewedIssue }));
    expect(screen.getAllByText(tb.reviewStates.kept).length).toBeGreaterThan(0);
    await user.selectOptions(screen.getByRole("combobox"), "sentencing");
    expect(screen.getByText(tb.emptyCategory)).toBeInTheDocument();
  });

  it("argument lab flags uncited sentences and applies suggested citations", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ArgumentLabScreen id="new" />);
    expect(screen.getAllByText(tb.unsupportedSpan).length).toBe(1);
    await user.click(screen.getByRole("button", { name: tb.generateNeutral }));
    await user.click(screen.getAllByRole("button", { name: tb.apply })[0]!);
    const editor = screen.getByRole("textbox", {
      name: messagesEn.phase5.argumentEditor,
    }) as HTMLTextAreaElement;
    expect(editor.value).toContain("lines 12–19");
    expect(screen.getByText(messagesEn.phase5.legalDecline)).toBeInTheDocument();
  });

  it("document reader has the sidebar, pager, research tabs and cited banner", async () => {
    const user = userEvent.setup();
    renderWithProviders(<DocumentReaderScreen id="F01234" />);
    expect(screen.getByText("Page 12 of 52")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.getByText("Page 13 of 52")).toBeInTheDocument();
    expect(screen.getAllByRole("tab").length).toBe(6);
    await user.click(screen.getByRole("tab", { name: tb.researchTabs.citations }));
    expect(screen.getByText(tb.citationCounts.produced)).toBeInTheDocument();
    expect(screen.getByText(/cited by finding F-DEMO-01/)).toBeInTheDocument();
  });

  it("public mode has a dedicated composition with terms, does-not-mean and the other side", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PublicScreen topic="findings" />);
    expect(screen.getByRole("radiogroup", { name: tb.modeToggle })).toBeInTheDocument();
    expect(screen.getByText(tb.beforeBegin2)).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /^\D+\d+$/ }).length).toBeGreaterThanOrEqual(6);
    await user.click(screen.getByRole("button", { name: "finding" }));
    expect(screen.getByRole("dialog", { name: tb.termTooltip })).toBeInTheDocument();
    expect(screen.getByText(messagesEn.phase5.doesNotMean)).toBeInTheDocument();
    expect(screen.getByText(tb.otherSide)).toBeInTheDocument();
    expect(screen.getByText(messagesEn.phase5.originalText)).toBeInTheDocument();
  });
});
