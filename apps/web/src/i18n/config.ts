import { DEFAULT_LOCALE, LOCALES, type Locale } from "@ksc/shared";

export { DEFAULT_LOCALE, LOCALES };
export type { Locale };

/** Language is a user setting, never a route prefix (ROUTE_MAP.md §6). */
export const LOCALE_COOKIE = "ksc_locale";
export const LOCALE_COOKIE_MAX_AGE = 60 * 60 * 24 * 365;

export function isLocale(value: unknown): value is Locale {
  return typeof value === "string" && (LOCALES as readonly string[]).includes(value);
}

export function resolveLocale(value: unknown): Locale {
  return isLocale(value) ? value : DEFAULT_LOCALE;
}
