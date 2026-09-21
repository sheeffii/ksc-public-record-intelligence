import {
  RealStatementComparisonScreen,
  StatementComparisonScreen,
} from "@/components/screens/phase5";
import { getRepository, resolveDataSource } from "@/data";
import { notFound } from "next/navigation";

export default async function Page({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  const key = decodeURIComponent(code);
  if (
    resolveDataSource({ NEXT_PUBLIC_DATA_SOURCE: process.env.NEXT_PUBLIC_DATA_SOURCE }) === "mock"
  ) {
    return <StatementComparisonScreen code={key} />;
  }
  const comparisons = await getRepository().listStatementComparisons();
  const comparison = comparisons.find((item) => item.key === key) ?? comparisons[0];
  if (!comparison) notFound();
  return <RealStatementComparisonScreen comparison={comparison} />;
}
