import { cookies } from "next/headers";
import { createApiRepository } from "@/data/api/repository";
import { resolveApiBaseUrl } from "@/data";

export const AI_ACCESS_COOKIE = "ksc_researcher_access";

/** The web tier never embeds a Researcher token in client JavaScript or page props. */
export function aiAccessRequired(): boolean {
  return (
    process.env.NODE_ENV === "production" ||
    process.env.APP_ENV === "staging" ||
    process.env.APP_ENV === "production"
  );
}

export async function researchToken(): Promise<string | undefined> {
  return (await cookies()).get(AI_ACCESS_COOKIE)?.value;
}

function internalApiBase(): string {
  return resolveApiBaseUrl(
    {
      API_INTERNAL_URL: process.env.API_INTERNAL_URL,
      NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    },
    true,
  ).replace(/\/+$/, "");
}

export async function aiApiRequest(
  path: string,
  token: string | undefined,
  options: { method?: "GET" | "POST"; body?: string } = {},
): Promise<Response> {
  if (aiAccessRequired() && !token) {
    return Response.json({ detail: "Researcher access required" }, { status: 401 });
  }
  return fetch(`${internalApiBase()}/api/v1/ai${path}`, {
    method: options.method ?? "GET",
    body: options.body,
    cache: "no-store",
    headers: {
      accept: "application/json",
      ...(options.body === undefined ? {} : { "content-type": "application/json" }),
      ...(token ? { authorization: `Bearer ${token}` } : {}),
    },
  });
}

export async function aiResearchRepository() {
  const token = await researchToken();
  if (aiAccessRequired() && !token) return null;
  return createApiRepository({
    baseUrl: internalApiBase(),
    fetch: (input, init) =>
      fetch(input, {
        ...init,
        cache: "no-store",
        headers: {
          ...init?.headers,
          ...(token ? { authorization: `Bearer ${token}` } : {}),
        },
      }),
  });
}

export function sameOriginMutation(request: Request): boolean {
  if (!aiAccessRequired()) return true;
  return request.headers.get("origin") === aiWebOrigin(request);
}

export function aiWebOrigin(request: Request): string {
  const configured = process.env.CANONICAL_URL;
  return configured ? new URL(configured).origin : new URL(request.url).origin;
}

export async function proxyAiRequest(
  request: Request,
  path: string,
  method: "GET" | "POST",
): Promise<Response> {
  if (method === "POST" && !sameOriginMutation(request)) {
    return Response.json({ detail: "Origin rejected" }, { status: 403 });
  }
  const token = await researchToken();
  if (aiAccessRequired() && !token) {
    return Response.json({ detail: "Researcher access required" }, { status: 401 });
  }
  let body: string | undefined;
  if (method === "POST") {
    body = await request.text();
    if (body.length > 4096) {
      return Response.json({ detail: "Request too large" }, { status: 413 });
    }
  }
  try {
    const upstream = await aiApiRequest(path, token, { method, body });
    return new Response(upstream.body, {
      status: upstream.status,
      headers: { "content-type": "application/json", "cache-control": "no-store" },
    });
  } catch {
    return Response.json(
      { detail: "AI service unavailable" },
      { status: 503, headers: { "cache-control": "no-store" } },
    );
  }
}
