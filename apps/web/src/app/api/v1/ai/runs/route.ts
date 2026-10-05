import { proxyAiRequest } from "@/lib/ai-access";

export const dynamic = "force-dynamic";

export function GET(request: Request) {
  return proxyAiRequest(request, "/runs", "GET");
}

export function POST(request: Request) {
  return proxyAiRequest(request, "/runs", "POST");
}
