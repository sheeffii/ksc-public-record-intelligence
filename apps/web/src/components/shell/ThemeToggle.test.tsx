import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { messagesEn, renderWithProviders } from "@/test/render";
import { ThemeToggle } from "./ThemeToggle";

describe("ThemeToggle — theme infrastructure", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.className = "";
  });

  it("starts dark (the product default) and switches the html class to light and back", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ThemeToggle />);
    const button = await screen.findByRole("button", { name: messagesEn.theme.switchToLight });
    expect(document.documentElement).toHaveClass("dark");

    await user.click(button);
    expect(document.documentElement).toHaveClass("light");
    expect(document.documentElement).not.toHaveClass("dark");
    expect(screen.getByRole("button", { name: messagesEn.theme.switchToDark })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: messagesEn.theme.switchToDark }));
    expect(document.documentElement).toHaveClass("dark");
  });

  it("persists the preference", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ThemeToggle />);
    await user.click(await screen.findByRole("button", { name: messagesEn.theme.switchToLight }));
    expect(window.localStorage.getItem("ksc-theme")).toBe("light");
  });
});
