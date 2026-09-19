import type { Locale } from "./config";
import en from "./messages/en.json";

export type Messages = typeof en;

/** Centralised loader so every consumer (server, client, tests) shares one table. */
export async function loadMessages(locale: Locale): Promise<Messages> {
  switch (locale) {
    case "sq":
      return (await import("./messages/sq.json")).default as Messages;
    case "en":
    default:
      return en;
  }
}

export { en as defaultMessages };
