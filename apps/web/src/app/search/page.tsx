import { SearchScreen } from "@/components/screens/phase5";

export default async function Page({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const { q } = await searchParams;
  return <SearchScreen initialQuery={q ?? ""} />;
}
