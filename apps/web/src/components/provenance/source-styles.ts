import type { SourceType } from "@ksc/shared";

/**
 * Token-only styling per source type. A component that hardcodes a hex will
 * not survive a palette change and may silently break provenance semantics
 * (HANDOFF.md §10.7).
 */
export const SOURCE_TEXT: Record<SourceType, string> = {
  court: "text-court",
  witness: "text-witness",
  spo: "text-spo",
  defence: "text-defence",
  exhibit: "text-doc",
  ai: "text-ai",
  incident: "text-incident",
  location: "text-location",
  organisation: "text-organisation",
};

export const SOURCE_BG: Record<SourceType, string> = {
  court: "bg-court-bg",
  witness: "bg-witness-bg",
  spo: "bg-spo-bg",
  defence: "bg-defence-bg",
  exhibit: "bg-doc-bg",
  ai: "bg-ai-bg",
  incident: "bg-incident-bg",
  location: "bg-location-bg",
  organisation: "bg-organisation-bg",
};

export const SOURCE_BORDER: Record<SourceType, string> = {
  court: "border-court",
  witness: "border-witness",
  spo: "border-spo",
  defence: "border-defence",
  exhibit: "border-doc",
  ai: "border-ai",
  incident: "border-incident",
  location: "border-location",
  organisation: "border-organisation",
};

export const SOURCE_DOT: Record<SourceType, string> = {
  court: "bg-court",
  witness: "bg-witness",
  spo: "bg-spo",
  defence: "bg-defence",
  exhibit: "bg-doc",
  ai: "bg-ai",
  incident: "bg-incident",
  location: "bg-location",
  organisation: "bg-organisation",
};
