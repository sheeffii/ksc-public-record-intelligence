import { screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { mockPathname } from "@/test/next-mocks";
import { messagesEn, messagesSq, renderWithProviders } from "@/test/render";
import { AppShell } from "./AppShell";

describe("AppShell — universal chrome", () => {
  beforeEach(() => mockPathname("/"));

  it("renders global nav, case stripe with the untranslated case id, content and governance footer", () => {
    renderWithProviders(
      <AppShell>
        <p>content</p>
      </AppShell>,
    );
    expect(document.querySelector("[data-global-nav]")).toBeInTheDocument();
    expect(screen.getByText("KSC-BC-2020-06")).toBeInTheDocument();
    expect(screen.getByRole("main")).toHaveTextContent("content");
    expect(screen.getByText(messagesEn.footer.neutrality)).toBeInTheDocument();
    expect(screen.getByText(messagesEn.footer.disclosure)).toBeInTheDocument();
  });

  it("hides the demo-data flag by default and shows it only when explicitly requested", () => {
    const { unmount } = renderWithProviders(<AppShell>x</AppShell>);
    expect(document.querySelector("[data-demo-flag]")).not.toBeInTheDocument();
    unmount();
    renderWithProviders(<AppShell showDemoFlag>x</AppShell>);
    expect(document.querySelector("[data-demo-flag]")).toBeInTheDocument();
  });

  it("applies the light surface only when asked (Document Reader / Public mode)", () => {
    const { unmount } = renderWithProviders(<AppShell>x</AppShell>);
    expect(document.querySelector("[data-surface]")).toHaveAttribute("data-surface", "dark");
    unmount();
    renderWithProviders(<AppShell mode="light">x</AppShell>);
    const surface = document.querySelector("[data-surface]");
    expect(surface).toHaveAttribute("data-surface", "light");
    expect(surface).toHaveClass("light");
  });

  it("renders the five-item mobile tab bar", () => {
    renderWithProviders(<AppShell>x</AppShell>);
    const bar = document.querySelector("[data-mobile-tab-bar]") as HTMLElement;
    expect(within(bar).getAllByRole("link")).toHaveLength(5);
  });

  it("renders the whole shell in Albanian without any English chrome string", () => {
    renderWithProviders(<AppShell>x</AppShell>, { locale: "sq" });
    expect(screen.getByText(messagesSq.footer.neutrality)).toBeInTheDocument();
    expect(screen.getByText(messagesSq.footer.disclosure)).toBeInTheDocument();
    expect(screen.queryByText(messagesEn.footer.neutrality)).not.toBeInTheDocument();
    expect(screen.getByText("KSC-BC-2020-06")).toBeInTheDocument();
  });
});
