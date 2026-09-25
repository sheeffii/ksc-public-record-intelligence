import { NetworkScreen } from "@/components/screens/phase5";
import {
  getRepository,
  resolveDataSource,
  type NetworkEvidenceFilter,
  type NetworkQuery,
  type NetworkRelationFilter,
} from "@/data";

const RELATIONS: readonly NetworkRelationFilter[] = ["cited_in", "mentioned_in", "testified_at"];
const EVIDENCE: readonly NetworkEvidenceFilter[] = [
  "citation",
  "entity_occurrence",
  "witness_appearance",
];
const CURSOR = /^[0-9a-f-]{36}$/;

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ focus?: string; type?: string; evidence?: string; cursor?: string }>;
}) {
  const { focus, type, evidence, cursor } = await searchParams;
  if (
    resolveDataSource({ NEXT_PUBLIC_DATA_SOURCE: process.env.NEXT_PUBLIC_DATA_SOURCE }) === "mock"
  )
    return <NetworkScreen />;
  // Unknown filter values are dropped, never guessed.
  const query: NetworkQuery = {
    relationshipType: RELATIONS.find((relation) => relation === type),
    evidenceKind: EVIDENCE.find((kind) => kind === evidence),
    cursor: cursor && CURSOR.test(cursor) ? cursor : undefined,
  };
  return (
    <NetworkScreen
      initialNetwork={await getRepository().getNetwork(focus, query)}
      initialFocus={focus}
    />
  );
}
