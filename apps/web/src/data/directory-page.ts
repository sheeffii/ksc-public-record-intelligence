import type { ServerDirectoryState } from "@/components/screens/phase5/DirectoryScreen";
import type { DirectoryRow, ServerDirectoryKind } from "./contract";
import { getRepository } from "./index";

const PAGE_SIZES = [10, 25, 50];
const FACETS: Record<ServerDirectoryKind, readonly string[]> = {
  documents: ["type", "language", "party"],
  exhibits: ["status", "party"],
};
const SORTS = ["id", "title", "date", "references"];

type Params = Record<string, string | string[] | undefined>;

const first = (value: string | string[] | undefined) => (Array.isArray(value) ? value[0] : value);

/** One API page of a large directory for the state in the URL. */
export async function loadServerDirectory(
  kind: ServerDirectoryKind,
  params: Params,
): Promise<{ rows: readonly DirectoryRow[]; server: ServerDirectoryState }> {
  const q = first(params.q) ?? "";
  const requestedSort = first(params.sort) ?? "title";
  const sort = SORTS.includes(requestedSort.replace(/^-/, "")) ? requestedSort : "title";
  const size = Number(first(params.size));
  const pageSize = PAGE_SIZES.includes(size) ? size : 10;
  const page = Math.max(1, Math.floor(Number(first(params.page)) || 1));
  const facets = Object.fromEntries(
    FACETS[kind].flatMap((key) => {
      const value = params[key];
      const values = Array.isArray(value) ? value : value ? [value] : [];
      return values.length ? [[key, values]] : [];
    }),
  );
  const result = await getRepository().queryDirectory(kind, {
    q,
    sort,
    facets,
    limit: pageSize,
    offset: (page - 1) * pageSize,
  });
  return {
    rows: result.rows,
    server: {
      q,
      sort,
      page,
      pageSize,
      total: result.total,
      unfilteredTotal: result.unfilteredTotal,
      facets: result.facets,
    },
  };
}
