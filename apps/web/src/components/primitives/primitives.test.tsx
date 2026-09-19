import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { messagesEn, renderWithProviders } from "@/test/render";
import { DataTable, DensityToggle, type Column } from "./DataTable";
import { Drawer } from "./Drawer";
import { ActiveFilters } from "./Filter";
import { Modal } from "./Modal";
import { Panel } from "./Panel";
import { EmptyState, ErrorState, GapNotice, SkeletonBlock } from "./States";

interface Row {
  id: string;
  label: string;
  refs: number;
}

const columns: Column<Row>[] = [
  { key: "id", header: "ID", identifier: true, sortable: true, cell: (r) => r.id },
  { key: "label", header: "Label", cell: (r) => r.label },
  { key: "refs", header: "Refs", numeric: true, sortable: true, cell: (r) => r.refs },
];

const rows: Row[] = [
  { id: "P00123", label: "Alpha", refs: 3 },
  { id: "P00441", label: "Beta", refs: 12 },
];

describe("DataTable", () => {
  it("renders headers and rows with density and selection", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    renderWithProviders(
      <DataTable
        columns={columns}
        rows={rows}
        rowKey={(r) => r.id}
        density="comfortable"
        selectedId="P00441"
        onSelect={onSelect}
        sortBy="-refs"
      />,
    );
    const table = screen.getByRole("table");
    expect(table).toHaveAttribute("data-density", "comfortable");
    expect(within(table).getAllByRole("row")).toHaveLength(3);
    expect(screen.getByRole("columnheader", { name: /Refs/ })).toHaveAttribute(
      "aria-sort",
      "descending",
    );
    const selected = table.querySelector('[data-row-id="P00441"]');
    expect(selected).toHaveAttribute("aria-selected", "true");
    await user.click(screen.getByText("Alpha"));
    expect(onSelect).toHaveBeenCalledWith(rows[0]);
  });

  it("shows the empty row label when there is nothing to list", () => {
    renderWithProviders(<DataTable columns={columns} rows={[]} rowKey={(r) => r.id} />);
    expect(screen.getByText(messagesEn.table.empty)).toBeInTheDocument();
  });

  it("density toggle is a radiogroup", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    renderWithProviders(<DensityToggle value="compact" onChange={onChange} />);
    await user.click(screen.getByRole("radio", { name: messagesEn.table.comfortable }));
    expect(onChange).toHaveBeenCalledWith("comfortable");
  });
});

describe("Panel", () => {
  it("renders label, title, body and footer", () => {
    renderWithProviders(
      <Panel label="Section" title="Title" footer="Footnote">
        body
      </Panel>,
    );
    expect(screen.getByRole("heading", { name: "Title" })).toBeInTheDocument();
    expect(screen.getByText("Section")).toBeInTheDocument();
    expect(screen.getByText("body")).toBeInTheDocument();
    expect(screen.getByText("Footnote")).toBeInTheDocument();
  });
});

describe("Filters", () => {
  it("renders active chips with individual remove controls", async () => {
    const user = userEvent.setup();
    const onRemove = vi.fn();
    renderWithProviders(
      <ActiveFilters
        filters={[
          { id: "party:spo", label: "SPO" },
          { id: "type:order", label: "Order" },
        ]}
        onRemove={onRemove}
      />,
    );
    await user.click(screen.getByRole("button", { name: "Remove filter: SPO" }));
    expect(onRemove).toHaveBeenCalledWith("party:spo");
  });

  it("states when no filter is applied", () => {
    renderWithProviders(<ActiveFilters filters={[]} onRemove={() => {}} />);
    expect(screen.getByText(messagesEn.filters.none)).toBeInTheDocument();
  });
});

describe("States", () => {
  it("loading is a polite status with skeleton lines", () => {
    renderWithProviders(<SkeletonBlock lines={3} label="findings" />);
    const status = screen.getByRole("status");
    expect(status).toHaveAttribute("aria-busy", "true");
    expect(status).toHaveTextContent("Loading findings");
    expect(status.querySelectorAll(".animate-pulse")).toHaveLength(3);
  });

  it("empty state carries the three required lines", () => {
    renderWithProviders(
      <EmptyState
        title="No exhibits match these filters"
        reason="Two filters narrow the set."
        action={<button>Clear</button>}
      />,
    );
    const empty = document.querySelector('[data-state="empty"]');
    expect(empty).toHaveTextContent("No exhibits match these filters");
    expect(empty).toHaveTextContent("Two filters narrow the set.");
    expect(within(empty as HTMLElement).getByRole("button", { name: "Clear" })).toBeInTheDocument();
  });

  it("error state names the failing scope, never a generic message", () => {
    renderWithProviders(<ErrorState scope="Witness testimony" partial />);
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("Witness testimony could not be loaded");
    expect(alert).toHaveTextContent(messagesEn.states.partial);
    expect(alert).not.toHaveTextContent(/something went wrong/i);
  });

  it("gap notice states the gap and its extent", () => {
    renderWithProviders(
      <GapNotice kind="closed-session" reference="T. 4,511–4,552" extent="41 pages" />,
    );
    const gap = document.querySelector("[data-gap]");
    expect(gap).toHaveAttribute("data-gap", "closed-session");
    expect(gap).toHaveTextContent(messagesEn.gap["closed-session"]);
    expect(gap).toHaveTextContent("41 pages");
    expect(gap).toHaveTextContent(messagesEn.gap.rule);
  });
});

describe("Modal and Drawer", () => {
  it("modal opens with a title and can be closed", async () => {
    const user = userEvent.setup();
    const onOpenChange = vi.fn();
    renderWithProviders(
      <Modal open title="Command palette" onOpenChange={onOpenChange} size="palette">
        palette body
      </Modal>,
    );
    expect(screen.getByRole("dialog", { name: "Command palette" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: messagesEn.dialog.close }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("drawer renders on the requested side", () => {
    renderWithProviders(
      <Drawer open title="Inspector" side="bottom" onOpenChange={() => {}}>
        sheet body
      </Drawer>,
    );
    const dialog = screen.getByRole("dialog", { name: "Inspector" });
    expect(dialog).toHaveAttribute("data-side", "bottom");
    expect(dialog).toHaveTextContent("sheet body");
  });
});
