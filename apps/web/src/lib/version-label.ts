/**
 * Human-readable facets of an official version reference. They are read from
 * the reference's own segments (the court's convention, which ingestion also
 * uses to derive them); nothing is inferred beyond those segments, and the
 * exact reference is always displayed alongside.
 *
 *   KSC-BC-2020-06/F00026/RED          → English · Public Redacted
 *   KSC-BC-2020-06/F00026/RED/sqi/COR  → Shqip · Public Redacted · Corrected
 */

export type VersionLanguage = "en" | "sq" | "sr";
export type VersionStatus =
  "public" | "publicRedacted" | "publicRedactedV2" | "corrected" | "reclassified";

const LANGUAGE_SEGMENTS: Record<string, VersionLanguage> = {
  eng: "en",
  sqi: "sq",
  alb: "sq",
  srp: "sr",
  srb: "sr",
};

const STATUS_SEGMENTS: Record<string, VersionStatus[]> = {
  RED: ["publicRedacted"],
  RED2: ["publicRedactedV2"],
  COR: ["corrected"],
  COR2: ["corrected"],
  CONF: ["reclassified"],
  CORRED: ["corrected", "publicRedacted"],
  REDCOR: ["publicRedacted", "corrected"],
};

export interface VersionFacets {
  /** Language of this version; the document's language when the reference
   * carries no translation segment. */
  language?: VersionLanguage;
  statuses: VersionStatus[];
}

export function versionFacets(
  versionRef: string,
  documentLanguage?: string,
  versionType?: string,
): VersionFacets {
  let language: VersionLanguage | undefined;
  const statuses: VersionStatus[] = [];
  for (const segment of versionRef.split("/")) {
    const lang = LANGUAGE_SEGMENTS[segment.toLowerCase()];
    if (lang && segment === segment.toLowerCase()) language = lang;
    for (const status of STATUS_SEGMENTS[segment] ?? []) {
      if (!statuses.includes(status)) statuses.push(status);
    }
  }
  if (versionType === "reclassified" && !statuses.includes("reclassified")) {
    statuses.push("reclassified");
  }
  if (!statuses.length) statuses.push("public");
  if (!language) {
    const doc = (documentLanguage ?? "").toLowerCase();
    language = doc.startsWith("sq") ? "sq" : doc.startsWith("sr") ? "sr" : doc ? "en" : undefined;
  }
  return { language, statuses };
}
