/**
 * Repository selection. Mock remains the default in Phase 6; the API adapter
 * is opt-in through configuration so the swap is a deployment decision, not
 * a code change (ADR-009).
 *
 *   NEXT_PUBLIC_DATA_SOURCE=mock | api      (default: mock)
 *   NEXT_PUBLIC_API_URL=http://localhost:8000
 *   API_INTERNAL_URL=http://api:8000        (server-side only, inside Docker)
 */

import type { ResearchRepository } from "./contract";
import { createApiRepository } from "./api/repository";
import { createMockRepositoryAdapter } from "./mock-adapter";

export type DataSource = "mock" | "api";

export type RepositoryEnv = Partial<
  Record<"NEXT_PUBLIC_DATA_SOURCE" | "NEXT_PUBLIC_API_URL" | "API_INTERNAL_URL", string | undefined>
>;

export function resolveDataSource(env: RepositoryEnv): DataSource {
  return env.NEXT_PUBLIC_DATA_SOURCE === "api" ? "api" : "mock";
}

export function resolveApiBaseUrl(env: RepositoryEnv, isServer: boolean): string {
  const serverUrl = isServer ? env.API_INTERNAL_URL : undefined;
  return serverUrl || env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

export function createRepository(
  env: RepositoryEnv = process.env as RepositoryEnv,
  isServer: boolean = typeof window === "undefined",
): ResearchRepository {
  if (resolveDataSource(env) === "api") {
    return createApiRepository({ baseUrl: resolveApiBaseUrl(env, isServer) });
  }
  return createMockRepositoryAdapter();
}

let instance: ResearchRepository | undefined;

/** Process-wide repository chosen from the environment. */
export function getRepository(): ResearchRepository {
  instance ??= createRepository();
  return instance;
}

export { createApiRepository } from "./api/repository";
export { createMockRepositoryAdapter } from "./mock-adapter";
export type * from "./contract";
