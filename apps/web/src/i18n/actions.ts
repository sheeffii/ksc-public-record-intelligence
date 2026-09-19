"use server";

import { revalidatePath } from "next/cache";
import { cookies } from "next/headers";
import { LOCALE_COOKIE, LOCALE_COOKIE_MAX_AGE, isLocale, type Locale } from "./config";

/** Persist the interface language. Document language is unaffected (ROUTE_MAP.md §6). */
export async function setLocale(locale: Locale): Promise<void> {
  if (!isLocale(locale)) return;
  const store = await cookies();
  store.set(LOCALE_COOKIE, locale, {
    path: "/",
    maxAge: LOCALE_COOKIE_MAX_AGE,
    sameSite: "lax",
  });
  revalidatePath("/", "layout");
}
