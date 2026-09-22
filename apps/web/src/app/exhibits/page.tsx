import { EvidenceExplorerScreen } from "@/components/screens/phase5";
import { getRepository } from "@/data";

export default async function Page() {
  const rows = await getRepository().getDirectory("exhibits");
  return <EvidenceExplorerScreen initialRows={rows} />;
}
