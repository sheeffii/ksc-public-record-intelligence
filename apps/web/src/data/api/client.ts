/** Minimal JSON client. `fetch` is injected so tests never touch a network. */

export type FetchLike = (input: string, init?: RequestInit) => Promise<Response>;

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly path: string,
    message?: string,
  ) {
    super(message ?? `API ${status} for ${path}`);
    this.name = "ApiError";
  }
}

export interface ApiClientOptions {
  baseUrl: string;
  fetch?: FetchLike;
}

export class ApiClient {
  private readonly baseUrl: string;
  private readonly fetchImpl: FetchLike;

  constructor(options: ApiClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/+$/, "");
    this.fetchImpl = options.fetch ?? ((input, init) => fetch(input, init));
  }

  /** GET and decode JSON; `null` on 404, `ApiError` on any other failure. */
  async get<T>(
    path: string,
    params?: Record<string, string | number | undefined>,
  ): Promise<T | null> {
    const url = new URL(`${this.baseUrl}/api/v1${path}`);
    for (const [key, value] of Object.entries(params ?? {})) {
      if (value !== undefined && value !== "") url.searchParams.set(key, String(value));
    }
    const response = await this.fetchImpl(url.toString(), {
      headers: { accept: "application/json" },
    });
    if (response.status === 404) return null;
    if (!response.ok) throw new ApiError(response.status, path);
    return (await response.json()) as T;
  }

  async post<T>(path: string, body: unknown): Promise<T> {
    const response = await this.fetchImpl(`${this.baseUrl}/api/v1${path}`, {
      method: "POST",
      headers: { accept: "application/json", "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) throw new ApiError(response.status, path);
    return (await response.json()) as T;
  }
}
