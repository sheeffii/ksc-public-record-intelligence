import { proxyAiRequest } from "@/lib/ai-access";

export const dynamic = "force-dynamic";

export async function GET(request: Request, { params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  return proxyAiRequest(request, `/runs/${encodeURIComponent(runId)}`, "GET");
}
