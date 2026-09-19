"use client";

import { ThemeProvider as NextThemesProvider } from "next-themes";
import type { ReactNode } from "react";

/**
 * User-preference theme infrastructure (next-themes, class strategy).
 *
 * Dark is the product default: it means "you are working over the record".
 * Light surfaces for the Document Reader and Public mode are applied per route
 * by <SurfaceTheme>, independent of this preference (DESIGN_DECISIONS.md §9).
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="dark"
      enableSystem={false}
      themes={["dark", "light"]}
      storageKey="ksc-theme"
      disableTransitionOnChange
    >
      {children}
    </NextThemesProvider>
  );
}
