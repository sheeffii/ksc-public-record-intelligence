import { EvidenceExplorerScreen } from "@/components/screens/phase5";
import { loadServerDirectory } from "@/data/directory-page";

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { rows, server } = await loadServerDirectory("exhibits", await searchParams);
  return <EvidenceExplorerScreen initialRows={rows} server={server} />;
}
