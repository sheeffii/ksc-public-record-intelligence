import { PlaceholderScreen } from "@/components/screens/PlaceholderScreen";

export default async function Page({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  // Identifiers in routes are the record's own; rendered verbatim (ROUTE_MAP.md §1).
  return <PlaceholderScreen screen="witnessDossier" identifier={decodeURIComponent(code)} />;
}
