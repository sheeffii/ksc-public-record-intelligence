import { cookies } from "next/headers";
import { getRequestConfig } from "next-intl/server";
import { LOCALE_COOKIE, resolveLocale } from "./config";
import { loadMessages } from "./messages";

/**
 * next-intl request configuration ("without i18n routing"). The locale is read
 * from a cookie so the interface language never appears in the URL.
 */
export default getRequestConfig(async () => {
  const store = await cookies();
  const locale = resolveLocale(store.get(LOCALE_COOKIE)?.value);
  return {
    locale,
    messages: await loadMessages(locale),
  };
});
