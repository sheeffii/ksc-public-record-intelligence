import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { PRIMARY_NAV } from "@/lib/routes";
import { mockPathname, routerRefresh, setLocaleMock } from "@/test/next-mocks";
import { messagesEn, messagesSq, renderWithProviders } from "@/test/render";
import { GlobalNav } from "./GlobalNav";

describe("GlobalNav", () => {
  beforeEach(() => {
    mockPathname("/witnesses/W01234");
    setLocaleMock.mockClear();
    routerRefresh.mockClear();
  });

  it("links every primary section from the route registry", () => {
    renderWithProviders(<GlobalNav />);
    const nav = screen.getByRole("navigation", { name: messagesEn.nav.mainNavigation });
    for (const item of PRIMARY_NAV.filter((i) => !i.overflow)) {
      expect(within(nav).getByRole("link", { name: messagesEn.nav[item.key] })).toHaveAttribute(
        "href",
        item.href,
      );
    }
  });

  it("marks the current section with aria-current", () => {
    renderWithProviders(<GlobalNav />);
    expect(screen.getByRole("link", { name: messagesEn.nav.witnesses })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: messagesEn.nav.people })).not.toHaveAttribute(
      "aria-current",
    );
  });

  it("renders the AI link in the AI colour and never with the active pill", () => {
    mockPathname("/ai");
    renderWithProviders(<GlobalNav />);
    const ai = screen.getByRole("link", { name: messagesEn.nav.ai });
    expect(ai).toHaveClass("text-ai");
    expect(ai).not.toHaveClass("bg-surface-raised");
  });

  it("exposes the search affordance with the ⌘K hint", () => {
    renderWithProviders(<GlobalNav />);
    expect(screen.getByRole("link", { name: messagesEn.nav.openSearch })).toHaveAttribute(
      "href",
      "/search",
    );
    expect(screen.getByText("⌘K")).toBeInTheDocument();
  });

  it("renders labels in Albanian when the locale is sq", () => {
    renderWithProviders(<GlobalNav />, { locale: "sq" });
    expect(screen.getByRole("link", { name: messagesSq.nav.witnesses })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: messagesEn.nav.witnesses })).not.toBeInTheDocument();
  });

  it("language toggle offers English and Shqip and persists the choice", async () => {
    const user = userEvent.setup();
    renderWithProviders(<GlobalNav />);
    const toggle = screen.getByRole("button", { name: messagesEn.language.label });
    expect(toggle).toHaveAttribute("data-locale", "en");
    await user.click(toggle);
    const menu = await screen.findByRole("menu");
    expect(within(menu).getByText(messagesEn.language.english)).toBeInTheDocument();
    expect(within(menu).getByText(messagesEn.language.albanian)).toBeInTheDocument();
    expect(within(menu).getByText(messagesEn.language.note)).toBeInTheDocument();
    await user.click(within(menu).getByRole("menuitemradio", { name: /Shqip/ }));
    expect(setLocaleMock).toHaveBeenCalledWith("sq");
  });
});
