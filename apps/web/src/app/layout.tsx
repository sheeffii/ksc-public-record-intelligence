import type { Metadata } from "next";
import { NextIntlClientProvider } from "next-intl";
import { getLocale, getTranslations } from "next-intl/server";
import { DM_Sans, Libre_Baskerville } from "next/font/google";
import type { ReactNode } from "react";
import { ThemeProvider } from "@/providers/ThemeProvider";
import "@/styles/globals.css";

/* Two families only (DESIGN_SYSTEM.md §3). Serif appears only for record text. */
const dmSans = DM_Sans({
  subsets: ["latin", "latin-ext"],
  variable: "--font-dm-sans",
  display: "swap",
});

const libreBaskerville = Libre_Baskerville({
  subsets: ["latin", "latin-ext"],
  weight: ["400", "700"],
  style: ["normal", "italic"],
  variable: "--font-libre-baskerville",
  display: "swap",
});

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("app");
  return {
    title: {
      default: t("name"),
      template: `%s · ${t("shortName")}`,
    },
    description: t("tagline"),
  };
}

export default async function RootLayout({ children }: { children: ReactNode }) {
  const locale = await getLocale();
  return (
    <html
      lang={locale}
      className={`${dmSans.variable} ${libreBaskerville.variable} dark`}
      suppressHydrationWarning
    >
      <body className="font-sans">
        <NextIntlClientProvider>
          <ThemeProvider>{children}</ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
