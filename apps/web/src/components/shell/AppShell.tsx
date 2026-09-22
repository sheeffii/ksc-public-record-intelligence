import { useTranslations } from "next-intl";
import type { ReactNode } from "react";
import type { SurfaceMode } from "@/lib/routes";
import { CommandPalette } from "./CommandPalette";
import { CaseStripe, type Crumb } from "./CaseStripe";
import { GlobalNav } from "./GlobalNav";
import { GovernanceFooter } from "./GovernanceFooter";
import { MobileTabBar } from "./MobileTabBar";
import { SurfaceTheme } from "./SurfaceTheme";

export interface AppShellProps {
  children: ReactNode;
  /** Light for the Document Reader and Public mode; dark everywhere else. */
  mode?: SurfaceMode;
  crumbs?: Crumb[];
  showDemoFlag?: boolean;
  /** Screen-specific governance text; defaults to the general neutrality note. */
  footer?: ReactNode;
}

/**
 * Universal chrome: GlobalNav (52px) · CaseStripe (32px) · content ·
 * GovernanceFooter (26px), with the bottom tab bar on mobile. Every approved
 * route renders inside this shell (DESIGN_SYSTEM.md, "Universal chrome").
 */
export function AppShell({
  children,
  mode = "dark",
  crumbs,
  showDemoFlag = false,
  footer,
}: AppShellProps) {
  const t = useTranslations("app");
  return (
    <div className="flex min-h-dvh flex-col">
      <a
        href="#main"
        className="focus:rounded-control focus:bg-accent sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:px-3 focus:py-1.5 focus:text-white"
      >
        {t("skipToContent")}
      </a>
      <GlobalNav />
      <CommandPalette />
      <SurfaceTheme mode={mode}>
        <CaseStripe crumbs={crumbs} showDemoFlag={showDemoFlag} />
        <main id="main" className="flex min-w-0 flex-1 flex-col pb-14 md:pb-0">
          {children}
        </main>
        <GovernanceFooter>{footer}</GovernanceFooter>
      </SurfaceTheme>
      <MobileTabBar />
    </div>
  );
}
