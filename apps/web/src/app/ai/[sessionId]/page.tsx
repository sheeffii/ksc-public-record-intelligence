import { AiResearchReal, AiResearchScreen } from "@/components/screens/phase5";
import { AiResearchAccess } from "@/components/screens/phase5/AiResearchAccess";
import { resolveDataSource } from "@/data";
import { ApiError } from "@/data/api/client";
import { aiResearchRepository } from "@/lib/ai-access";

export const dynamic = "force-dynamic";

export default async function Page({ params }: { params: Promise<{ sessionId: string }> }) {
  const dataSource = resolveDataSource({
    NEXT_PUBLIC_DATA_SOURCE: process.env.NEXT_PUBLIC_DATA_SOURCE,
  });
  if (dataSource === "mock") return <AiResearchScreen />;
  const { sessionId } = await params;
  const repository = await aiResearchRepository();
  if (!repository) return <AiResearchAccess />;
  const result = await Promise.all([repository.getAiRun(sessionId), repository.listAiRuns()]).catch(
    (error: unknown) => {
      if (error instanceof ApiError && [401, 403].includes(error.status)) {
        return null;
      }
      throw error;
    },
  );
  if (!result) return <AiResearchAccess error="invalid" />;
  const [run, sessions] = result;
  return <AiResearchReal initialRun={run} sessions={sessions} />;
}
