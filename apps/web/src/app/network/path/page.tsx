import { EvidencePathScreen } from "@/components/screens/phase5";
import { getRepository, resolveDataSource } from "@/data";

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ from?: string; to?: string; maxHops?: string }>;
}) {
  if (
    resolveDataSource({ NEXT_PUBLIC_DATA_SOURCE: process.env.NEXT_PUBLIC_DATA_SOURCE }) === "mock"
  )
    return <EvidencePathScreen />;
  const repository = getRepository();
  // Evidence Path traverses citation-backed edges only (ADR-014).
  const network = await repository.getNetwork(undefined, { evidenceKind: "citation" });
  const query = await searchParams;
  const from = query.from ?? network.edges[0]?.from ?? network.nodes[0]?.id ?? "";
  const to = query.to ?? network.edges[0]?.to ?? network.nodes[1]?.id ?? from;
  const maxHops = Math.min(8, Math.max(1, Number(query.maxHops) || 6));
  const hops = from && to ? await repository.getPath(from, to, maxHops) : [];
  return (
    <EvidencePathScreen
      initialNetwork={network}
      initialHops={hops}
      initialFrom={from}
      initialTo={to}
    />
  );
}
