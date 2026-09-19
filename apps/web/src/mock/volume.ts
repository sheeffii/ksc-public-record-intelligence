/**
 * Generated demo volume for directory tables (Phase 5B). Rows are visibly
 * generic — "Demo record 07" — and carry no court material. They exist only so
 * pagination, sorting, density and filters have something to act on.
 */

import type { VerificationState } from "@ksc/shared";
import type { MockDirectory, MockDirectoryRow } from "./types";

const STATES: readonly VerificationState[] = [
  "verified",
  "unreviewed",
  "needs-evidence",
  "ai-flagged",
  "verified",
];
const PREFIX: Record<MockDirectory, string> = {
  people: "demo-person-",
  witnesses: "W0",
  documents: "F0",
  findings: "FD-DEMO-",
  exhibits: "P0",
  incidents: "I-DEMO-",
};
const ROUTE: Record<MockDirectory, (id: string) => string> = {
  people: (id) => `/people/${id}`,
  witnesses: (id) => `/witnesses/${id}`,
  documents: (id) => `/documents/${id}`,
  findings: (id) => `/findings/${id}`,
  exhibits: (id) => `/documents/${id}?page=1`,
  incidents: (id) => `/incidents/${id}`,
};

export const DEMO_VOLUME = 24;

export function generatedRows(kind: MockDirectory, count = DEMO_VOLUME): MockDirectoryRow[] {
  return Array.from({ length: count }, (_, i) => {
    const n = i + 1;
    const id = `${PREFIX[kind]}${String(n + 2000).padStart(4, "0")}`;
    const isProtected = kind === "witnesses" && n % 3 !== 0;
    return {
      id,
      title: isProtected ? id : `Demo record ${String(n).padStart(2, "0")}`,
      kind,
      description: `Generic sample ${kind} row generated for layout density.`,
      date: `2024-${String((n % 12) + 1).padStart(2, "0")}-${String((n % 27) + 1).padStart(2, "0")}`,
      references: (n * 7) % 23,
      verification: STATES[n % STATES.length]!,
      href: ROUTE[kind](id),
      ...(isProtected ? { protected: true } : {}),
    };
  });
}
