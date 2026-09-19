import { StatementComparisonScreen } from "@/components/screens/phase5";

export default async function Page({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  return <StatementComparisonScreen code={decodeURIComponent(code)} />;
}
