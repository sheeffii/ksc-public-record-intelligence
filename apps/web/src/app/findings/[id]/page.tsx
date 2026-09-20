import { FindingDetailScreen, RealFindingDetailScreen } from "@/components/screens/phase5";
import { getRepository, resolveDataSource } from "@/data";
import { notFound } from "next/navigation";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const key = decodeURIComponent(id);
  if (
    resolveDataSource({ NEXT_PUBLIC_DATA_SOURCE: process.env.NEXT_PUBLIC_DATA_SOURCE }) === "mock"
  ) {
    return <FindingDetailScreen id={key} />;
  }
  const finding = await getRepository().getFinding(key);
  if (!finding) notFound();
  return <RealFindingDetailScreen finding={finding} />;
}
