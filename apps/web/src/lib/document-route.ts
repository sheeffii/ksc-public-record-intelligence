/** Browser and API-safe document route helpers. */
const CASE_PREFIX = /^KSC(?:-[A-Z0-9]+)+$/i;

export function documentRouteId(reference: string): string {
  const parts = reference.split("/");
  return parts.length > 1 && CASE_PREFIX.test(parts[0] ?? "")
    ? parts.slice(1).join("/")
    : reference;
}

export function documentHref(reference: string): string {
  return `/documents/${encodeURIComponent(documentRouteId(reference))}`;
}

export function documentApiPath(reference: string): string {
  return `/documents/${encodeURIComponent(reference)}`;
}
