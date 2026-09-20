import { SearchScreen } from "@/components/screens/phase5";
import { getRepository, resolveDataSource } from "@/data";

export default async function Page({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const { q } = await searchParams;
  const query = q ?? "";
  if (
    resolveDataSource({ NEXT_PUBLIC_DATA_SOURCE: process.env.NEXT_PUBLIC_DATA_SOURCE }) === "mock"
  ) {
    return <SearchScreen initialQuery={query} />;
  }
  const results = query ? await getRepository().search(query) : [];
  return <SearchScreen initialQuery={query} initialResults={results} />;
}
