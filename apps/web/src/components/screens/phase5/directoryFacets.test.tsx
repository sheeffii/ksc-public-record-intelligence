import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import "@/test/next-mocks";
import { routerPush } from "@/test/next-mocks";
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
