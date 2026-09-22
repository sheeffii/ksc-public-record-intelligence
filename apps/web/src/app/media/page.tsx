import { MediaWorkspace } from "@/components/screens/phase5";
import type { CourtMediaStatus } from "@/data/contract";
import { getRepository } from "@/data";

const SCOPES = new Set(["court", "external", "both"]);
const STATUSES = new Set([
  "external_only",
  "mentioned",
  "tendered",
  "admitted",
  "rejected",
  "discussed",
  "relied_upon",
  "unknown",
]);

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; scope?: string; status?: string }>;
}) {
  const params = await searchParams;
  const query = params.q ?? "";
  const scope = SCOPES.has(params.scope ?? "")
    ? (params.scope as "court" | "external" | "both")
    : "external";
  const status = STATUSES.has(params.status ?? "")
    ? (params.status as CourtMediaStatus)
    : undefined;
  const repository = getRepository();
  const [workspace, courtResults] = await Promise.all([
    repository.getMediaWorkspace(query || undefined, status),
    scope === "external" || !query ? Promise.resolve([]) : repository.search(query),
  ]);
  return (
    <MediaWorkspace workspace={workspace} courtResults={courtResults} query={query} scope={scope} />
  );
}
