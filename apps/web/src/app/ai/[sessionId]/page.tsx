import { PlaceholderScreen } from "@/components/screens/PlaceholderScreen";

export default async function Page({ params }: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = await params;
  // Identifiers in routes are the record's own; rendered verbatim (ROUTE_MAP.md §1).
  return <PlaceholderScreen screen="aiSession" identifier={decodeURIComponent(sessionId)} />;
}
