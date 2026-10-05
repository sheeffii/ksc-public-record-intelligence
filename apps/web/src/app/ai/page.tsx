import { AiResearchReal, AiResearchScreen } from "@/components/screens/phase5";
import { AiResearchAccess } from "@/components/screens/phase5/AiResearchAccess";
import { resolveDataSource } from "@/data";
import { ApiError } from "@/data/api/client";
import { aiResearchRepository } from "@/lib/ai-access";

export const dynamic = "force-dynamic";

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ access?: string }>;
}) {
  const dataSource = resolveDataSource({
    NEXT_PUBLIC_DATA_SOURCE: process.env.NEXT_PUBLIC_DATA_SOURCE,
  });
  if (dataSource === "mock") return <AiResearchScreen />;
  const repository = await aiResearchRepository();
  if (!repository) return <AiResearchAccess error={(await searchParams).access} />;
  const sessions = await repository.listAiRuns().catch((error: unknown) => {
    if (error instanceof ApiError && [401, 403].includes(error.status)) {
      return null;
    }
    throw error;
  });
  if (!sessions) return <AiResearchAccess error="invalid" />;
  return <AiResearchReal initialRun={null} sessions={sessions} />;
}
