import { render, type RenderOptions } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import type { ReactElement, ReactNode } from "react";
import type { Locale } from "@/i18n/config";
import en from "@/i18n/messages/en.json";
import sq from "@/i18n/messages/sq.json";
import { ThemeProvider } from "@/providers/ThemeProvider";

const MESSAGES = { en, sq } as const;

export function Providers({ children, locale = "en" }: { children: ReactNode; locale?: Locale }) {
  return (
    <NextIntlClientProvider locale={locale} messages={MESSAGES[locale]} timeZone="Europe/Amsterdam">
      <ThemeProvider>{children}</ThemeProvider>
    </NextIntlClientProvider>
  );
}

/** Render inside the i18n + theme providers the app layout supplies. */
export function renderWithProviders(
  ui: ReactElement,
  { locale = "en", ...options }: RenderOptions & { locale?: Locale } = {},
) {
  return render(ui, {
    wrapper: ({ children }) => <Providers locale={locale}>{children}</Providers>,
    ...options,
  });
}

export { en as messagesEn, sq as messagesSq };
