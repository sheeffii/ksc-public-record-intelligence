import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import "@/test/next-mocks";
import { routerPush, routerReplace } from "@/test/next-mocks";
import { renderWithProviders } from "@/test/render";
import type { DirectoryRow } from "@/data";

import { DirectoryScreen } from "./DirectoryScreen";

function person(slug: string, title: string, role: string): DirectoryRow {
  return {
    id: slug,
    title,
    kind: "people",
    description: role,
    date: "—",
    references: 0,
    verification: "unreviewed",
    href: `/people/${slug}`,
    facets: { role },
  };
}

const ROWS = [
  person("accused-thaci", "Accused Thaçi", "accused"),
  person("accused-veseli", "Accused Veseli", "accused"),
  person("witness-zyrapi", "Bislim Zyrapi", "witness"),
  person("counsel-capin", "Capin", "counsel_or_participant"),
];

describe("directory facet filters", () => {
  it("counts each role and narrows the list to the chosen one", async () => {
    const user = userEvent.setup();
    renderWithProviders(<DirectoryScreen kind="people" screenTitle="People" initialRows={ROWS} />);
    const roles = screen.getAllByRole("group", { name: "Role" })[0]!;
    const accused = within(roles).getByRole("button", { name: /Accused\s*2/ });
    await user.click(accused);
    expect(accused).toHaveAttribute("aria-pressed", "true");
    expect(screen.getAllByText("Accused Thaçi").length).toBeGreaterThan(0);
    expect(screen.queryByText("Bislim Zyrapi")).toBeNull();
    expect(screen.queryByText("Capin")).toBeNull();
  });

  it("filters from a role badge without opening the row", async () => {
    const user = userEvent.setup();
    routerPush.mockClear();
    renderWithProviders(<DirectoryScreen kind="people" screenTitle="People" initialRows={ROWS} />);
    const row = document.querySelector("tr[data-row-id='witness-zyrapi']") as HTMLElement;
    await user.click(within(row).getByRole("button", { name: "Witness" }));
    expect(routerPush).not.toHaveBeenCalled();
    expect(screen.queryByText("Accused Veseli")).toBeNull();
    expect(screen.getAllByText("Bislim Zyrapi").length).toBeGreaterThan(0);
  });

  it("opens the record when the row itself is clicked", async () => {
    const user = userEvent.setup();
    routerPush.mockClear();
    renderWithProviders(<DirectoryScreen kind="people" screenTitle="People" initialRows={ROWS} />);
    await user.click(document.querySelector("tr[data-row-id='counsel-capin'] td") as HTMLElement);
    expect(routerPush).toHaveBeenCalledWith("/people/counsel-capin");
  });
});

describe("server-paged directories", () => {
  function doc(id: string, type: string): DirectoryRow {
    return {
      id,
      title: `Filing ${id}`,
      kind: "documents",
      description: type,
      date: "2024-01-01",
      references: 0,
      verification: "unreviewed",
      href: `/documents/${id}`,
      facets: { type },
    };
  }
  const server = {
    q: "",
    sort: "title",
    page: 2,
    pageSize: 10,
    total: 3516,
    unfilteredTotal: 3516,
    facets: {
      type: [
        ["filing", 3000],
        ["decision", 516],
      ] as const,
    },
  };

  it("shows the API page and totals instead of filtering in the browser", () => {
    renderWithProviders(
      <DirectoryScreen
        kind="documents"
        screenTitle="Documents"
        initialRows={[doc("F00011", "filing"), doc("F00012", "decision")]}
        server={server}
      />,
    );
    expect(screen.getAllByText("Filing F00011").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Filing F00012").length).toBeGreaterThan(0);
    const types = screen.getAllByRole("group", { name: "Type" })[0]!;
    expect(within(types).getByRole("button", { name: /Filing\s*3000/ })).toBeInTheDocument();
    expect(document.body.textContent).toMatch(/3,?516/);
  });

  it("writes facet, search and sort changes to the URL for the server", async () => {
    const user = userEvent.setup();
    routerReplace.mockClear();
    renderWithProviders(
      <DirectoryScreen
        kind="documents"
        screenTitle="Documents"
        initialRows={[doc("F00011", "filing")]}
        server={server}
      />,
    );
    const types = screen.getAllByRole("group", { name: "Type" })[0]!;
    await user.click(within(types).getByRole("button", { name: /Decision\s*516/ }));
    // The decision row is not hidden locally; the server answers the new URL.
    expect(screen.getAllByText("Filing F00011").length).toBeGreaterThan(0);
    await vi.waitFor(() => expect(routerReplace).toHaveBeenCalled());
    const url = String(routerReplace.mock.calls.at(-1)?.[0]);
    expect(url).toContain("type=decision");
    expect(url).toContain("sort=title");
    expect(url).not.toContain("page=");
  });
});
