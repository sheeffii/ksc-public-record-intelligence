/**
 * `ApiRepository` — the read API behind the screen-facing contract.
 *
 * Every method maps API records through `mappers.ts`; nothing is fabricated
 * for surfaces the API does not serve yet (`getPath`, `getAnswer` return
 * empty until Phase 9 / Phase 11).
 */

import type { AnswerBlock } from "@ksc/shared";
import type {
  DirectoryKind,
  DirectoryRow,
  DocumentView,
  EvidenceRow,
  NetworkView,
  PathHop,
  PersonDossier,
  ResearchRepository,
  SearchResult,
  TimelineItem,
  WitnessDossier,
} from "../contract";
import { ApiClient, type ApiClientOptions } from "./client";
import * as map from "./mappers";
import type {
  ApiClaim,
  ApiAppealIssue,
  ApiAppealWorkspace,
  ApiArgumentLab,
  ApiAiRun,
  ApiAiRunSummary,
  ApiDocumentChunk,
  ApiDocumentDetail,
  ApiDocumentSummary,
  ApiEvent,
  ApiEvidencePath,
  ApiExhibit,
  ApiFindingDetail,
  ApiFindingSummary,
  ApiIncident,
  ApiMediaWorkspace,
  ApiNetwork,
  ApiPage,
  ApiPerson,
  ApiSearch,
  ApiStatementComparison,
  ApiWitness,
} from "./types";

const PAGE = { limit: 200, offset: 0 } as const;

export function createApiRepository(options: ApiClientOptions): ResearchRepository {
  const client = new ApiClient(options);

  async function page<T>(path: string): Promise<T[]> {
    const items: T[] = [];
    let offset = 0;
    for (;;) {
      const result = await client.get<ApiPage<T>>(path, { ...PAGE, offset });
      if (!result) return items;
      items.push(...result.items);
      offset += result.items.length;
      if (result.items.length === 0 || offset >= result.total) return items;
    }
  }

  const directories: Record<DirectoryKind, () => Promise<DirectoryRow[]>> = {
    documents: async () => (await page<ApiDocumentSummary>("/documents")).map(map.documentRow),
    people: async () => (await page<ApiPerson>("/people")).map(map.personRow),
    witnesses: async () => (await page<ApiWitness>("/witnesses")).map(map.witnessRow),
    exhibits: async () => (await page<ApiExhibit>("/exhibits")).map(map.exhibitRow),
    incidents: async () => (await page<ApiIncident>("/incidents")).map(map.incidentRow),
    findings: async () =>
      (await page<ApiFindingSummary>("/findings"))
        .map(map.findingRow)
        .filter((row): row is DirectoryRow => row !== null),
  };

  return {
    getDirectory: (kind) => directories[kind](),

    async getPerson(slug: string): Promise<PersonDossier | null> {
      const person = await client.get<ApiPerson>(`/people/${encodeURIComponent(slug)}`);
      return person ? map.toPerson(person) : null;
    },

    async getWitness(code: string): Promise<WitnessDossier | null> {
      const witness = await client.get<ApiWitness>(`/witnesses/${encodeURIComponent(code)}`);
      return witness ? map.toWitnessDossier(witness) : null;
    },

    async getIncident(slug: string) {
      const incident = await client.get<ApiIncident>(`/incidents/${encodeURIComponent(slug)}`);
      return incident ? map.toIncident(incident) : null;
    },

    async getDocument(
      id: string,
      versionRef?: string,
      sourcePage?: number,
      pdfPageIndex?: number,
    ): Promise<DocumentView | null> {
      const document = await client.get<ApiDocumentDetail>(`/documents/${id}`);
      if (!document) return null;
      const version = versionRef
        ? document.versions.find((candidate) => candidate.official_version_ref === versionRef)
        : document.versions.at(-1);
      const chunks = version
        ? ((
            await client.get<ApiPage<ApiDocumentChunk>>(
              `/document-versions/${version.official_version_ref}/chunks`,
              { limit: 200, offset: 0, page: sourcePage, pdf_page_index: pdfPageIndex },
            )
          )?.items ?? [])
        : [];
      return map.toDocument(document, chunks, version);
    },

    async getFinding(key: string) {
      const finding = await client.get<ApiFindingDetail>(
        `/findings/${encodeURIComponent(key)}/matrix`,
      );
      return finding ? map.toFinding(finding) : null;
    },

    async search(query: string): Promise<readonly SearchResult[]> {
      const result = await client.get<ApiSearch>("/search", { q: query });
      return (result?.hits ?? []).map(map.toSearchResult);
    },

    async getNetwork(): Promise<NetworkView> {
      const network = await client.get<ApiNetwork>("/network");
      if (!network) return { nodes: [], edges: [] };
      const edges = network.edges
        .map(map.toNetworkEdge)
        .filter((edge): edge is NonNullable<typeof edge> => edge !== null);
      const used = new Set(edges.flatMap((edge) => [edge.from, edge.to]));
      const nodes = network.nodes.filter((node) => used.has(node.id));
      return {
        nodes: nodes.map((node, index) => map.toNetworkNode(node, index, nodes.length)),
        edges,
      };
    },

    async getPath(
      fromNodeId?: string,
      toNodeId?: string,
      maxHops = 6,
    ): Promise<readonly PathHop[]> {
      if (!fromNodeId || !toNodeId) return [];
      const result = await client.get<ApiEvidencePath>("/network/path", {
        from_node_id: fromNodeId,
        to_node_id: toNodeId,
        max_hops: maxHops,
      });
      if (!result?.found) return [];
      return result.hops.flatMap((hop, index) => {
        const edge = map.toNetworkEdge(hop);
        return edge
          ? [
              {
                ...edge,
                index: index + 1,
                date: hop.relationship_date ?? "",
                dateType: "document" as const,
              },
            ]
          : [];
      });
    },

    async getTimeline(): Promise<readonly TimelineItem[]> {
      return (await page<ApiEvent>("/events")).map(map.toTimelineItem);
    },

    async getEvidence(): Promise<readonly EvidenceRow[]> {
      return (await page<ApiClaim>("/claims")).flatMap(map.toEvidenceRows);
    },

    // Legacy Phase 5 placeholder. Phase 11 uses audited run methods below.
    async getAnswer(): Promise<readonly AnswerBlock[]> {
      return map.NO_ANSWER;
    },

    async createAiRun(question: string) {
      return map.toAiRun(await client.post<ApiAiRun>("/ai/runs", { question }));
    },

    async getAiRun(id: string) {
      const run = await client.get<ApiAiRun>(`/ai/runs/${encodeURIComponent(id)}`);
      return run ? map.toAiRun(run) : null;
    },

    async listAiRuns() {
      const runs = await client.get<ApiAiRunSummary[]>("/ai/runs");
      return (runs ?? []).map(map.toAiRunSummary);
    },

    async saveAiRunAsNote(id: string, title: string) {
      return client.post<{ id: string; provenance: string }>(
        `/ai/runs/${encodeURIComponent(id)}/notes`,
        { title },
      );
    },

    async listAppealIssues() {
      const workspace = await client.get<ApiAppealWorkspace>("/appeal/issues");
      if (!workspace) throw new Error("Appeal workspace is unavailable");
      return map.toAppealWorkspace(workspace);
    },

    async getAppealIssue(key: string) {
      const issue = await client.get<ApiAppealIssue>(`/appeal/issues/${encodeURIComponent(key)}`);
      return issue ? map.toAppealIssue(issue) : null;
    },

    async getArgumentLab(key: string) {
      const lab = await client.get<ApiArgumentLab>(
        `/appeal/issues/${encodeURIComponent(key)}/argument-lab`,
      );
      return lab ? map.toArgumentLab(lab) : null;
    },

    async listStatementComparisons(issueKey?: string) {
      const comparisons = await client.get<ApiStatementComparison[]>("/statement-comparisons", {
        issue_key: issueKey,
      });
      return (comparisons ?? []).map(map.toStatementComparison);
    },

    async getMediaWorkspace(query?: string, courtStatus?: import("../contract").CourtMediaStatus) {
      const workspace = await client.get<ApiMediaWorkspace>("/media", {
        q: query,
        court_status: courtStatus,
      });
      if (!workspace) throw new Error("External public sources are unavailable");
      return {
        items: workspace.items.map((item) => ({
          id: item.id,
          title: item.title,
          publisher: item.publisher,
          canonicalUrl: item.canonical_url,
          publishedAt: item.published_at ?? undefined,
          capturedAt: item.captured_at,
          sourceType: item.source_type,
          language: item.language,
          courtStatuses: item.court_statuses,
          verification: map.toVerification(item.verification_state) ?? "unreviewed",
        })),
        comparisons: workspace.comparisons.map((comparison) => ({
          id: comparison.id,
          key: comparison.comparison_key,
          title: comparison.title,
          classification: comparison.classification,
          statementA: comparison.statement_a.text,
          statementB: comparison.statement_b?.text,
          explanation: comparison.explanation,
          verification: map.toVerification(comparison.verification_state) ?? "unreviewed",
        })),
        coverage: {
          sources: workspace.coverage.sources,
          items: workspace.coverage.items,
          statements: workspace.coverage.statements,
          courtLinks: workspace.coverage.court_links,
          citationBackedCourtLinks: workspace.coverage.citation_backed_court_links,
          comparisons: workspace.coverage.comparisons,
        },
        taxonomy: workspace.court_status_taxonomy,
        limitations: workspace.limitations,
      };
    },
  };
}
