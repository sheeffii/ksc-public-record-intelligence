import { SearchScreen } from "@/components/screens/phase5";
import { getRepository, resolveDataSource } from "@/data";

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; scope?: string }>;
}) {
  const { q, scope: requestedScope } = await searchParams;
  const query = q ?? "";
  const scope =
    requestedScope === "external" || requestedScope === "both" ? requestedScope : "court";
  if (
    resolveDataSource({ NEXT_PUBLIC_DATA_SOURCE: process.env.NEXT_PUBLIC_DATA_SOURCE }) === "mock"
  ) {
    return <SearchScreen initialQuery={query} sourceScope={scope} />;
  }
  const repository = getRepository();
  const [courtResults, media] = await Promise.all([
    query && scope !== "external" ? repository.search(query) : Promise.resolve([]),
    query && scope !== "court" ? repository.getMediaWorkspace(query) : Promise.resolve(null),
  ]);
  const externalResults =
    media?.items.map((item) => ({
      id: item.id,
      category: "external" as const,
      title: item.title,
      context: `${item.publisher} · ${item.publishedAt ?? item.capturedAt}`,
      href: item.canonicalUrl,
    })) ?? [];
  return (
    <SearchScreen
      initialQuery={query}
      initialResults={[...courtResults, ...externalResults]}
      sourceScope={scope}
    />
  );
}
