import { AiResearchReal, AiResearchScreen } from "@/components/screens/phase5";
import { getRepository, resolveApiBaseUrl, resolveDataSource } from "@/data";

export default async function Page({ params }: { params: Promise<{ sessionId: string }> }) {
  const dataSource = resolveDataSource({
    NEXT_PUBLIC_DATA_SOURCE: process.env.NEXT_PUBLIC_DATA_SOURCE,
  });
  if (dataSource === "mock") return <AiResearchScreen />;
  const { sessionId } = await params;
  const repository = getRepository();
  const [run, sessions] = await Promise.all([
    repository.getAiRun(sessionId),
    repository.listAiRuns(),
  ]);
  return (
    <AiResearchReal
      initialRun={run}
      sessions={sessions}
      apiBaseUrl={resolveApiBaseUrl(
        { NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL },
        false,
      )}
    />
  );
}
