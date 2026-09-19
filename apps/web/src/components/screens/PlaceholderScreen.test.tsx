import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { ROUTES } from "@/lib/routes";
import { mockPathname } from "@/test/next-mocks";
import { messagesEn, messagesSq, renderWithProviders } from "@/test/render";
import { PlaceholderScreen } from "./PlaceholderScreen";

describe("PlaceholderScreen — every approved route renders the shell", () => {
  beforeEach(() => mockPathname("/"));

  it.each(ROUTES.map((r) => [r.pattern, r.key] as const))(
    "%s renders the shell, its title and an honest empty state",
    (pattern, key) => {
      const { unmount } = renderWithProviders(<PlaceholderScreen screen={key} />);
      expect(document.querySelector("[data-global-nav]")).toBeInTheDocument();
      expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(messagesEn.screens[key]);
      expect(document.querySelector("dd.font-mono")).toHaveTextContent(pattern);
      expect(document.querySelector('[data-state="empty"]')).toHaveTextContent(
        messagesEn.placeholder.absent,
      );
      unmount();
    },
  );

  it("renders the record identifier verbatim in either language", () => {
    const { unmount } = renderWithProviders(
      <PlaceholderScreen screen="witnessDossier" identifier="W01234" />,
    );
    expect(screen.getByText("W01234")).toBeInTheDocument();
    unmount();
    renderWithProviders(<PlaceholderScreen screen="witnessDossier" identifier="W01234" />, {
      locale: "sq",
    });
    expect(screen.getByText("W01234")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      messagesSq.screens.witnessDossier,
    );
  });

  it("uses the light surface for the Document Reader and dark for Finding Detail", () => {
    const { unmount } = renderWithProviders(
      <PlaceholderScreen screen="documentReader" identifier="F00482" />,
    );
    expect(document.querySelector("[data-surface]")).toHaveAttribute("data-surface", "light");
    unmount();
    renderWithProviders(<PlaceholderScreen screen="findingDetail" identifier="F00482" />);
    expect(document.querySelector("[data-surface]")).toHaveAttribute("data-surface", "dark");
  });
});
