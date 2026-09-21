import { AiResearchReal, AiResearchScreen } from "@/components/screens/phase5";
import { getRepository, resolveApiBaseUrl, resolveDataSource } from "@/data";

export default async function Page() {
  const dataSource = resolveDataSource({
    NEXT_PUBLIC_DATA_SOURCE: process.env.NEXT_PUBLIC_DATA_SOURCE,
  });
  if (dataSource === "mock") return <AiResearchScreen />;
  const sessions = await getRepository().listAiRuns();
  return (
    <AiResearchReal
      initialRun={null}
      sessions={sessions}
      apiBaseUrl={resolveApiBaseUrl(
        { NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL },
        false,
      )}
    />
  );
}
