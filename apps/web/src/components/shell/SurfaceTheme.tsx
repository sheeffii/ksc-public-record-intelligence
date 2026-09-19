import type { ReactNode } from "react";
import type { SurfaceMode } from "@/lib/routes";
import { cn } from "@/lib/utils";

/**
 * Applies the semantic surface theme for a route subtree.
 *
 * Light means "you are reading the record itself" (Document Reader, Public
 * mode); dark means "you are working over the record". The split is semantic,
 * not aesthetic (DESIGN_DECISIONS.md §9), so it is set by the route, not by
 * user preference.
 */
export function SurfaceTheme({
  mode,
  children,
  className,
}: {
  mode: SurfaceMode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      data-surface={mode}
      className={cn(
        mode === "light" ? "light" : "dark",
        "bg-bg text-fg-body flex min-h-0 flex-1 flex-col",
        className,
      )}
    >
      {children}
    </div>
  );
}
