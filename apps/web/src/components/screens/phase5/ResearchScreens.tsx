"use client";

import { groupBySource } from "@/lib/source-groups";
import { documentHref } from "@/lib/document-route";
import { cn } from "@/lib/utils";
import type { DateType, Direction } from "@ksc/shared";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useRef, useState } from "react";
import type { NetworkQuery, NetworkView, PathHop, TimelineItem } from "@/data";
import { ActiveFilters, FilterOption, FilterSection } from "@/components/primitives/Filter";
import { Panel } from "@/components/primitives/Panel";
import { EmptyState } from "@/components/primitives/States";
import {
  CitationChip,
  DirectionBadge,
  EvidenceBasis,
  ProvenanceSource,
  RecordBlock,
  ScopeNote,
  SourceBadge,
  VerificationBadge,
  AiAnalysisBlock,
} from "@/components/provenance";
import { AppShell } from "@/components/shell/AppShell";
import {
  courtCitation,
  exhibitCitation,
  mockRepository,
  transcriptCitation,
  type MockNetworkNode,
  type MockTimelineItem,
} from "@/mock";
import { DirectoryScreen } from "./DirectoryScreen";
import { ActionLink, DemoNotice, ScreenHeader, TabStrip } from "./ScreenChrome";
import {
  KeyValue,
  NoteStrip,
  RailIndex,
  SectionCard,
  Segmented,
  StatStrip,
  ToolButton,
  Toolbar,
} from "./Workspace";

export { AiResearchScreen, AppealScreen, ArgumentLabScreen, PublicScreen } from "./AnalysisScreens";

// ------------------------------------------------ evidence explorer -------

export function EvidenceExplorerScreen({
  initialRows = [],
}: {
  initialRows?: readonly import("@/data").DirectoryRow[];
}) {
  const t = useTranslations("screens");
  return <DirectoryScreen kind="exhibits" screenTitle={t("exhibits")} initialRows={initialRows} />;
}

// ------------------------------------------------------------ network -----

const NETWORK_RELATIONS = ["cited_in", "mentioned_in", "testified_at"] as const;
const NETWORK_EVIDENCE = ["citation", "entity_occurrence", "witness_appearance"] as const;

function networkHref(focus: string | undefined, query: NetworkQuery): string {
  const params = new URLSearchParams();
  if (focus) params.set("focus", focus);
  if (query.relationshipType) params.set("type", query.relationshipType);
  if (query.evidenceKind) params.set("evidence", query.evidenceKind);
  if (query.cursor) params.set("cursor", query.cursor);
  const search = params.toString();
  return search ? `/network?${search}` : "/network";
}

/**
 * Server-side, cursor-paginated slice of `/network/edges`: filters and paging
 * are URL state, so the full graph is never loaded or rendered at once.
 */
function NetworkPageControls({
  page,
  focus,
  shown,
}: {
  page: NonNullable<NetworkView["page"]>;
  focus?: string;
  shown: number;
}) {
  const t19 = useTranslations("phase19");
  const { query } = page;
  const base = { relationshipType: query.relationshipType, evidenceKind: query.evidenceKind };
  const chip = (href: string, label: string, active: boolean) => (
    <Link
      key={href + label}
      href={href}
      aria-current={active ? "page" : undefined}
      className={`rounded-control border px-2 py-1 text-[10px] font-semibold ${
        active ? "border-accent text-accent" : "border-border text-fg-secondary"
      }`}
    >
      {label}
    </Link>
  );
  return (
    <div className="border-border bg-surface space-y-2 border-b px-3 py-2" data-network-page>
      <p className="text-fg-secondary text-[11px]">
        {t19("network.pageSummary", { total: page.total, shown })}
        {focus ? null : ` ${t19("network.overview")}`}
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-fg-tertiary text-[10px]">{t19("network.relationFilter")}</span>
        {chip(
          networkHref(focus, { evidenceKind: query.evidenceKind }),
          t19("network.all"),
          !query.relationshipType,
        )}
        {NETWORK_RELATIONS.map((relation) =>
          chip(
            networkHref(focus, { ...base, relationshipType: relation }),
            `${relation.replaceAll("_", " ")} (${page.byType[relation] ?? 0})`,
            query.relationshipType === relation,
          ),
        )}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-fg-tertiary text-[10px]">{t19("network.evidenceFilter")}</span>
        {chip(
          networkHref(focus, { relationshipType: query.relationshipType }),
          t19("network.all"),
          !query.evidenceKind,
        )}
        {NETWORK_EVIDENCE.map((kind) =>
          chip(
            networkHref(focus, { ...base, evidenceKind: kind }),
            t19(`evidenceKind.${kind}`),
            query.evidenceKind === kind,
          ),
        )}
        {query.cursor ? chip(networkHref(focus, base), t19("network.firstPage"), false) : null}
        {page.nextCursor
          ? chip(
              networkHref(focus, { ...base, cursor: page.nextCursor }),
              t19("network.nextPage"),
              false,
            )
          : null}
      </div>
    </div>
  );
}

const NODE_KINDS = [
  "person",
  "witness",
  "exhibit",
  "incident",
  "court",
  "location",
  "organisation",
  "spo",
  "defence",
] as const;

export function NetworkScreen({
  initialNetwork,
  initialFocus,
}: {
  initialNetwork?: NetworkView;
  initialFocus?: string;
}) {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const footer = useTranslations("footer");
  const t18 = useTranslations("phase18");
  const realData = initialNetwork !== undefined;
  const { nodes, edges }: NetworkView = initialNetwork ?? mockRepository.getNetwork();
  const [selectedNode, setSelectedNode] = useState(
    nodes.find((node) => node.ref === initialFocus) ?? nodes[0]!,
  );
  const [selectedEdge, setSelectedEdge] = useState(edges[0]!);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [query, setQuery] = useState("");
  const [isolated, setIsolated] = useState(false);
  const [expanded, setExpanded] = useState(true);
  const [depth, setDepth] = useState<"1" | "2" | "3">("2");
  const [layout, setLayout] = useState<"force" | "radial">("force");
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [sourceFilter, setSourceFilter] = useState("all");
  const [relationFilter, setRelationFilter] = useState("all");
  const [entityFilter, setEntityFilter] = useState("all");
  const edgeYears = edges.flatMap((edge) =>
    edge.relationshipDate ? [Number(edge.relationshipDate.slice(0, 4))] : [],
  );
  const minYear = edgeYears.length ? Math.min(...edgeYears) : 1998;
  const newestYear = edgeYears.length ? Math.max(...edgeYears) : 2025;
  const [fromYear, setFromYear] = useState(minYear);
  const [maxYear, setMaxYear] = useState(newestYear);
  const [fullscreen, setFullscreen] = useState(false);
  const [detent, setDetent] = useState<"peek" | "half" | "full">("peek");
  const detentClass = {
    peek: "max-lg:max-h-[22dvh]",
    half: "max-lg:max-h-[45dvh]",
    full: "max-lg:max-h-[85dvh]",
  }[detent];
  const dragStart = useRef<{
    pointerX: number;
    pointerY: number;
    panX: number;
    panY: number;
  } | null>(null);
  if (!selectedNode) {
    return (
      <AppShell footer={footer("network")}>
        <ScreenHeader
          realData={realData}
          eyebrow={t("network")}
          title={t("network")}
          description={t18("networkInitialLimit")}
        />
        <div className="mx-auto w-full max-w-[900px] p-4">
          <EmptyState title={t18("relationships")} reason={t18("networkNoFocusedRecords")} />
        </div>
      </AppShell>
    );
  }
  const neighbourIds = new Set([selectedNode.id]);
  for (let hop = 0; hop < Number(depth); hop += 1) {
    for (const edge of edges) {
      if (neighbourIds.has(edge.from) || neighbourIds.has(edge.to)) {
        neighbourIds.add(edge.from);
        neighbourIds.add(edge.to);
      }
    }
  }
  const directNeighbourIds = new Set(
    edges
      .filter((edge) => edge.from === selectedNode.id || edge.to === selectedNode.id)
      .flatMap((edge) => [edge.from, edge.to]),
  );
  const typeFilteredNodes = nodes.filter(
    (node) => entityFilter === "all" || node.entityKind === entityFilter,
  );
  const connectedNodes = typeFilteredNodes.filter(
    (node) => node.id === selectedNode.id || neighbourIds.has(node.id),
  );
  const visibleNodes = (
    !expanded
      ? typeFilteredNodes.filter((node) => directNeighbourIds.has(node.id))
      : isolated || realData
        ? connectedNodes.length > 1
          ? connectedNodes
          : typeFilteredNodes
        : typeFilteredNodes
  ).slice(0, depth === "1" ? 3 : depth === "2" ? 12 : 75);
  const visibleNodeIds = new Set(visibleNodes.map((n) => n.id));
  const visibleEdges = edges.filter(
    (e) =>
      visibleNodeIds.has(e.from) &&
      visibleNodeIds.has(e.to) &&
      (!verifiedOnly || e.verification === "verified") &&
      (sourceFilter === "all" || e.sourceType === sourceFilter) &&
      (relationFilter === "all" || e.relation === relationFilter) &&
      (!e.relationshipDate ||
        (Number(e.relationshipDate.slice(0, 4)) >= fromYear &&
          Number(e.relationshipDate.slice(0, 4)) <= maxYear)),
  );
  const listedNodes = nodes.filter((n) =>
    n.label.toLowerCase().includes(query.trim().toLowerCase()),
  );
  const degree = (id: string) => edges.filter((e) => e.from === id || e.to === id).length;
  function selectNode(node: MockNetworkNode) {
    setSelectedNode(node);
    const adjacent = edges.find((edge) => edge.from === node.id || edge.to === node.id);
    if (adjacent) setSelectedEdge(adjacent);
  }
  const nodeLabel = (id: string) => nodes.find((node) => node.id === id)?.label ?? "—";
  const relationshipLabel = (value: string) => value.replaceAll("_", " ");

  function handleGraphAction(key: string) {
    if (key === "zoomIn") setZoom((v) => Math.min(1.4, v + 0.1));
    if (key === "zoomOut") setZoom((v) => Math.max(0.7, v - 0.1));
    if (key === "isolate") setIsolated((v) => !v);
    if (key === "expand") setExpanded(true);
    if (key === "collapseGraph") setExpanded(false);
    if (key === "reset") {
      setZoom(1);
      setPan({ x: 0, y: 0 });
      setIsolated(false);
      setExpanded(true);
      setQuery("");
      setDepth("2");
      setVerifiedOnly(false);
      setSourceFilter("all");
      setRelationFilter("all");
      setEntityFilter("all");
      setFromYear(minYear);
      setMaxYear(newestYear);
    }
  }
  const position = (node: MockNetworkNode, index: number) =>
    layout === "force"
      ? node.id === selectedNode.id
        ? { x: 50, y: 50 }
        : {
            x:
              50 +
              34 * Math.cos(((index - 1) / Math.max(visibleNodes.length - 1, 1)) * Math.PI * 2),
            y:
              50 +
              34 * Math.sin(((index - 1) / Math.max(visibleNodes.length - 1, 1)) * Math.PI * 2),
          }
      : {
          x: 50 + 34 * Math.cos((index / Math.max(visibleNodes.length, 1)) * Math.PI * 2),
          y: 50 + 34 * Math.sin((index / Math.max(visibleNodes.length, 1)) * Math.PI * 2),
        };
  const inspector = (
    <div className="space-y-3 p-3">
      <Panel title={t("nodeInspector")}>
        <div className="flex items-center gap-2">
          <NodeGlyph type={selectedNode.type} />
          <p className="text-fg font-semibold">{selectedNode.label}</p>
        </div>
        <div className="mt-2">
          <KeyValue
            rows={[
              { key: "type", label: tb("typeBadges"), value: selectedNode.type },
              { key: "edges", label: t18("relationships"), value: degree(selectedNode.id) },
              { key: "visible", label: tb("counts"), value: visibleEdges.length },
            ]}
          />
        </div>
        <div className="mt-2 flex flex-wrap gap-2">
          <ToolButton
            onClick={() => {
              setIsolated(true);
            }}
          >
            {tb("recentre")}
          </ToolButton>
          <ActionLink href={`/network/path?from=${selectedNode.id}`}>
            {t("findConnection")}
          </ActionLink>
        </div>
      </Panel>
      <Panel title={t("whyConnection")}>
        <p className="text-fg text-[11px]">{relationshipLabel(selectedEdge.relation)}</p>
        <p className="text-fg-muted mt-1 text-[10px]">
          {nodeLabel(selectedEdge.from)} → {nodeLabel(selectedEdge.to)}
        </p>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <SourceBadge type={selectedEdge.sourceType} />
          <VerificationBadge state={selectedEdge.verification} size="sm" />
          <EvidenceBasis kind={selectedEdge.evidenceKind} count={selectedEdge.evidenceCount} />
        </div>
        {selectedEdge.provenance ? (
          <div className="mt-2">
            <ProvenanceSource provenance={selectedEdge.provenance} />
          </div>
        ) : (
          <>
            <div className="mt-2">
              <CitationChip citation={selectedEdge.citation} />
            </div>
            {selectedEdge.sourceCoordinate ? (
              <p className="identifier text-fg-muted mt-2 text-[10px]">
                {selectedEdge.sourceCoordinate}
              </p>
            ) : null}
            <div className="mt-3">
              <ActionLink
                href={selectedEdge.sourcePath ?? documentHref(selectedEdge.citation.docId)}
              >
                {t("openSource")}
              </ActionLink>
            </div>
          </>
        )}
        <p className="governance-text mt-3">{footer("network")}</p>
      </Panel>
      <Panel title={t("graphTextAlternative")}>
        <ul className="space-y-1 text-[10px]">
          {groupBySource(visibleEdges.slice(0, 100), (e) => {
            const versionRef = e.provenance?.versionRef ?? e.citation.ref;
            return {
              key: [e.from, e.to, e.relation, e.verification, versionRef].join("|"),
              versionRef,
              title: `${nodeLabel(e.from)} → ${nodeLabel(e.to)} · ${relationshipLabel(e.relation)}`,
              documentHref: "",
              page: e.provenance?.page ?? e.citation.page,
            };
          }).map((group) => {
            const [first, ...more] = group.items;
            if (!first) return null;
            return (
              <li key={group.key}>
                <button
                  type="button"
                  onClick={() => setSelectedEdge(first)}
                  className="text-left hover:underline"
                >
                  {group.title}
                  {more.length ? ` ×${group.items.length}` : ""}
                </button>
                {more.length
                  ? group.items.map((edge, index) => (
                      <button
                        key={edge.id}
                        type="button"
                        onClick={() => setSelectedEdge(edge)}
                        className="text-accent ml-1.5 font-mono hover:underline"
                      >
                        {(edge.provenance?.page ?? edge.citation.page) !== undefined
                          ? `p.${edge.provenance?.page ?? edge.citation.page}`
                          : `#${index + 1}`}
                      </button>
                    ))
                  : null}
              </li>
            );
          })}
        </ul>
      </Panel>
    </div>
  );
  return (
    <AppShell footer={footer("network")}>
      <ScreenHeader
        realData={realData}
        eyebrow={t("network")}
        title={t("network")}
        description={footer("network")}
        actions={
          <ActionLink
            href={`/network/path?from=${selectedNode.id}&to=${edges[0]?.to ?? selectedNode.id}`}
            primary
          >
            {t("findConnection")}
          </ActionLink>
        }
      />
      <Toolbar>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t("searchWithin")}
          aria-label={t("searchWithin")}
          className="border-border bg-surface-raised rounded-control h-8 min-w-44 border px-3 text-[11px]"
        />
        <Segmented
          label={tb("layout")}
          value={layout}
          onChange={setLayout}
          options={[
            { key: "force", label: `${tb("layout")}: A` },
            { key: "radial", label: "B" },
          ]}
        />
        <Segmented
          label={tb("depth")}
          value={depth}
          onChange={setDepth}
          options={[
            { key: "1", label: `${tb("depth")} 1` },
            { key: "2", label: "2" },
            { key: "3", label: "3" },
          ]}
        />
        <ToolButton pressed={verifiedOnly} onClick={() => setVerifiedOnly((v) => !v)}>
          {tb("filters")}
        </ToolButton>
        {["zoomIn", "zoomOut", "reset", "isolate", "expand", "collapseGraph"].map((key) => (
          <ToolButton
            key={key}
            onClick={() => handleGraphAction(key)}
            pressed={key === "isolate" ? isolated : undefined}
          >
            {t(key)}
          </ToolButton>
        ))}
        <ToolButton onClick={() => undefined}>{tb("saveView")}</ToolButton>
        <ToolButton onClick={() => undefined}>{t("export")}</ToolButton>
        <ToolButton pressed={fullscreen} onClick={() => setFullscreen((v) => !v)}>
          {tb("fullscreen")}
        </ToolButton>
        <span className="rounded-badge bg-surface-raised text-fg-muted ml-auto px-2 py-0.5 text-[10px]">
          {tb("resolvingDepth", { d: depth })}
        </span>
      </Toolbar>
      {initialNetwork?.page ? (
        <NetworkPageControls page={initialNetwork.page} focus={initialFocus} shown={edges.length} />
      ) : null}
      <div
        className={`grid min-h-[690px] flex-1 ${fullscreen ? "" : "lg:grid-cols-[220px_minmax(0,1fr)_280px]"}`}
      >
        {realData ? <span className="sr-only">{tb("realDataNotice")}</span> : null}
        <aside
          className={`border-border bg-surface space-y-3 border-r p-3 ${fullscreen ? "hidden" : "hidden lg:block"}`}
        >
          <Panel title={tb("legend")}>
            <ul className="space-y-1">
              {NODE_KINDS.map((k) => (
                <li key={k} className="flex items-center gap-2 text-[10px]">
                  <NodeGlyph type={k} />
                  <span className="text-fg-secondary">{tb(`nodeShapes.${k}`)}</span>
                </li>
              ))}
            </ul>
          </Panel>
          <FilterSection title={tb("dateSlider")}>
            <input
              type="range"
              min={minYear}
              max={newestYear}
              value={fromYear}
              onChange={(event) => setFromYear(Math.min(Number(event.target.value), maxYear))}
              aria-label={tb("from")}
              className="w-full"
            />
            <input
              type="range"
              min={minYear}
              max={newestYear}
              value={maxYear}
              onChange={(event) => setMaxYear(Math.max(Number(event.target.value), fromYear))}
              aria-label={tb("to")}
              className="w-full"
            />
            <p className="tabular text-fg-muted text-[10px]">
              {fromYear} — {maxYear}
            </p>
          </FilterSection>
          <FilterSection title={tb("sourceType")}>
            <select
              aria-label={tb("sourceType")}
              value={sourceFilter}
              onChange={(event) => setSourceFilter(event.target.value)}
              className="border-border bg-surface-raised rounded-control w-full border p-1 text-[10px]"
            >
              <option value="all">{t("allRecords")}</option>
              {[...new Set(edges.map((edge) => edge.sourceType))].map((source) => (
                <option key={source} value={source}>
                  {source}
                </option>
              ))}
            </select>
          </FilterSection>
          <FilterSection title={tb("relationshipType")}>
            <select
              aria-label={tb("relationshipType")}
              value={relationFilter}
              onChange={(event) => setRelationFilter(event.target.value)}
              className="border-border bg-surface-raised rounded-control w-full border p-1 text-[10px]"
            >
              <option value="all">{t("allRecords")}</option>
              {[...new Set(edges.map((edge) => edge.relation))].map((relation) => (
                <option key={relation} value={relation}>
                  {relation}
                </option>
              ))}
            </select>
          </FilterSection>
          <FilterSection title={tb("typeBadges")}>
            <select
              aria-label={tb("typeBadges")}
              value={entityFilter}
              onChange={(event) => setEntityFilter(event.target.value)}
              className="border-border bg-surface-raised rounded-control w-full border p-1 text-[10px]"
            >
              <option value="all">{t("allRecords")}</option>
              {[...new Set(nodes.map((node) => node.entityKind).filter(Boolean))].map((kind) => (
                <option key={kind} value={kind}>
                  {kind}
                </option>
              ))}
            </select>
          </FilterSection>
          <FilterSection title={tb("verificationFilter")}>
            <FilterOption
              label="verified"
              count={edges.filter((e) => e.verification === "verified").length}
              checked={verifiedOnly}
              onChange={setVerifiedOnly}
            />
          </FilterSection>
          <Panel title={t("allRecords")}>
            <div className="max-h-72 space-y-1 overflow-y-auto">
              {listedNodes.slice(0, 100).map((n) => (
                <button
                  key={n.id}
                  type="button"
                  onClick={() => selectNode(n)}
                  className="hover:bg-surface-raised rounded-control flex w-full items-center gap-2 px-2 py-1 text-left"
                >
                  <NodeGlyph type={n.type} />
                  <span className="text-[10px]">{n.label}</span>
                </button>
              ))}
            </div>
          </Panel>
        </aside>
        <div
          className="bg-bg-graph relative min-h-[560px] cursor-grab touch-none overflow-hidden active:cursor-grabbing"
          role="region"
          aria-label={t("network")}
          onPointerDown={(event) => {
            if ((event.target as Element).closest("button")) return;
            event.currentTarget.setPointerCapture(event.pointerId);
            dragStart.current = {
              pointerX: event.clientX,
              pointerY: event.clientY,
              panX: pan.x,
              panY: pan.y,
            };
          }}
          onPointerMove={(event) => {
            if (!dragStart.current) return;
            setPan({
              x: dragStart.current.panX + event.clientX - dragStart.current.pointerX,
              y: dragStart.current.panY + event.clientY - dragStart.current.pointerY,
            });
          }}
          onPointerUp={() => {
            dragStart.current = null;
          }}
          onPointerCancel={() => {
            dragStart.current = null;
          }}
        >
          <div
            className="absolute inset-0 transition-transform motion-reduce:transition-none"
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transformOrigin: "center",
            }}
          >
            <svg className="absolute inset-0 size-full" aria-hidden>
              {visibleEdges.map((edge) => {
                const ai = visibleNodes.findIndex((n) => n.id === edge.from);
                const bi = visibleNodes.findIndex((n) => n.id === edge.to);
                const a = position(visibleNodes[ai]!, ai);
                const b = position(visibleNodes[bi]!, bi);
                return (
                  <line
                    key={edge.id}
                    x1={`${a.x}%`}
                    y1={`${a.y}%`}
                    x2={`${b.x}%`}
                    y2={`${b.y}%`}
                    stroke={edge.id === selectedEdge.id ? "var(--accent)" : "var(--border)"}
                    strokeWidth={edge.id === selectedEdge.id ? 3 : 2}
                    onClick={() => setSelectedEdge(edge)}
                    className="cursor-pointer"
                  />
                );
              })}
            </svg>
            {visibleNodes.map((node, i) => {
              const p = position(node, i);
              return (
                <button
                  key={node.id}
                  type="button"
                  onClick={() => selectNode(node)}
                  onDoubleClick={() => setIsolated(true)}
                  style={{ left: `${p.x}%`, top: `${p.y}%` }}
                  className={`absolute z-10 flex -translate-x-1/2 -translate-y-1/2 items-center gap-1.5 rounded-full border px-3 py-2 text-[10px] ${node.id === selectedNode.id ? "border-accent bg-surface-high text-fg" : "border-border bg-surface text-fg"}`}
                >
                  <NodeGlyph type={node.type} />
                  {node.label}
                </button>
              );
            })}
          </div>
          <div className="absolute top-3 left-3 flex gap-1 lg:hidden">
            <ToolButton onClick={() => setIsolated((v) => !v)} pressed={isolated}>
              {tb("filters")}
            </ToolButton>
          </div>
          <svg
            aria-label={tb("minimap")}
            role="img"
            className="border-border bg-surface/80 absolute top-3 right-3 h-16 w-24 rounded border"
            viewBox="0 0 100 100"
          >
            {visibleNodes.map((n, i) => {
              const p = position(n, i);
              return (
                <circle
                  key={n.id}
                  cx={p.x}
                  cy={p.y}
                  r="4"
                  fill={n.id === selectedNode.id ? "var(--accent)" : "var(--border)"}
                />
              );
            })}
          </svg>
          <p className="governance-text bg-bg-deep/80 absolute bottom-4 left-4 max-w-xs rounded px-3 py-2">
            {footer("network")}
          </p>
          <p className="text-fg-secondary bg-bg-deep/90 absolute right-4 bottom-4 max-w-xs rounded px-3 py-2 text-[10px]">
            {t18("networkInitialLimit")}
          </p>
        </div>
        <div
          className={`border-border bg-surface max-lg:rounded-t-sheet max-lg:shadow-sheet border-l max-lg:fixed max-lg:right-0 max-lg:bottom-14 max-lg:left-0 max-lg:z-30 ${detentClass} max-lg:overflow-auto max-lg:border-t ${fullscreen ? "lg:hidden" : ""}`}
        >
          <div className="text-fg-secondary flex items-center justify-between px-4 py-2 text-[10px] font-semibold tracking-[0.16em] uppercase lg:hidden">
            <span>
              {t("viewDetails")} · {selectedNode.label}
            </span>
            <button
              type="button"
              onClick={(event) => {
                event.preventDefault();
                setDetent((d) => (d === "peek" ? "half" : d === "half" ? "full" : "peek"));
              }}
              className="border-border rounded-control border px-2 py-0.5 tracking-normal normal-case"
            >
              {detent}
            </button>
          </div>
          {inspector}
        </div>
      </div>
    </AppShell>
  );
}

function NodeGlyph({ type }: { type: string }) {
  const shape =
    type === "protected" || type === "witness"
      ? `border-witness rounded-full ${type === "protected" ? "border-dashed" : ""}`
      : type === "incident"
        ? "border-incident rotate-45"
        : type === "court"
          ? "border-court rounded"
          : type === "exhibit"
            ? "border-doc rounded-sm"
            : type === "spo"
              ? "border-spo rounded"
              : type === "defence"
                ? "border-defence rounded"
                : type === "location"
                  ? "border-location rounded-full"
                  : type === "organisation"
                    ? "border-organisation"
                    : "border-accent rounded-full";
  return <span aria-hidden className={`inline-block size-3.5 shrink-0 border ${shape}`} />;
}

// ------------------------------------------------------- evidence path ----

export function EvidencePathScreen({
  initialNetwork,
  initialHops,
  initialFrom,
  initialTo,
}: {
  initialNetwork?: NetworkView;
  initialHops?: readonly PathHop[];
  initialFrom?: string;
  initialTo?: string;
}) {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const footer = useTranslations("footer");
  const realData = initialNetwork !== undefined;
  const hops: readonly PathHop[] = initialHops ?? mockRepository.getPath();
  const { nodes } = initialNetwork ?? mockRepository.getNetwork();
  const [maxHops, setMaxHops] = useState<"1" | "2" | "3">("3");
  const [from, setFrom] = useState(initialFrom ?? nodes[0]?.id ?? "");
  const [to, setTo] = useState(initialTo ?? nodes[1]?.id ?? nodes[0]?.id ?? "");
  const [openHop, setOpenHop] = useState(1);
  const [alternate, setAlternate] = useState(0);
  const shown = hops.slice(0, Number(maxHops) + 1);
  const complete = shown.length === hops.length;
  const label = (id: string) => nodes.find((n) => n.id === id)?.label ?? "—";
  return (
    <AppShell footer={footer("network")}>
      <ScreenHeader
        realData={realData}
        eyebrow={t("network")}
        title={tb("pathCanvas")}
        description={t("pathLimit")}
        actions={<ActionLink href="/network">{tb("openInNetwork")}</ActionLink>}
      />
      <Toolbar>
        <span className="section-label">{tb("entityPicker")}</span>
        <label className="text-[11px]">
          <span className="text-fg-secondary mr-1">{tb("fromEntity")}</span>
          <select
            value={from}
            onChange={(e) => setFrom(e.target.value)}
            className="border-border bg-surface-raised rounded-control h-8 border px-2 text-[11px]"
          >
            {nodes.map((n) => (
              <option key={n.id} value={n.id}>
                {n.label}
              </option>
            ))}
          </select>
        </label>
        <label className="text-[11px]">
          <span className="text-fg-secondary mr-1">{tb("toEntity")}</span>
          <select
            value={to}
            onChange={(e) => setTo(e.target.value)}
            className="border-border bg-surface-raised rounded-control h-8 border px-2 text-[11px]"
          >
            {nodes.map((n) => (
              <option key={n.id} value={n.id}>
                {n.label}
              </option>
            ))}
          </select>
        </label>
        <Segmented
          label={tb("maxHops")}
          value={maxHops}
          onChange={setMaxHops}
          options={[
            { key: "1", label: "1" },
            { key: "2", label: "2" },
            { key: "3", label: "3" },
          ]}
        />
        <ActionLink href={`/network/path?from=${from}&to=${to}&maxHops=${maxHops}`} primary>
          {tb("findPath")}
        </ActionLink>
      </Toolbar>
      <div className="border-border bg-surface-raised text-fg border-b px-4 py-2 text-[11px]">
        {t("pathBanner")}
      </div>
      <div className="mx-auto grid w-full max-w-[1440px] min-w-0 flex-1 gap-3 p-3 md:p-4 xl:grid-cols-[minmax(0,1fr)_322px]">
        <div className="min-w-0 space-y-3">
          {realData ? <NoteStrip>{tb("realDataNotice")}</NoteStrip> : <DemoNotice />}
          <SectionCard title={tb("pathCanvas")}>
            <ol className="flex flex-col gap-2 md:flex-row md:items-center md:overflow-x-auto">
              {shown.map((hop, i) => (
                <li key={hop.id} className="flex flex-col gap-2 md:flex-row md:items-center">
                  {i === 0 ? <PathNode label={label(hop.from)} /> : null}
                  <button
                    type="button"
                    onClick={() => setOpenHop(hop.index)}
                    className={`border-border rounded-control flex items-center gap-1 border border-dashed px-2 py-1 text-[10px] ${openHop === hop.index ? "bg-surface-high text-fg" : "text-fg-secondary"}`}
                  >
                    <span className="tabular">{hop.index}</span> {hop.relation}
                  </button>
                  <PathNode label={label(hop.to)} />
                </li>
              ))}
            </ol>
            {!complete ? (
              <EmptyState
                className="mt-3"
                title={tb("noPath", { n: maxHops })}
                reason={tb("noPathReason")}
                action={<ToolButton onClick={() => setMaxHops("3")}>{tb("raiseLimit")}</ToolButton>}
              />
            ) : null}
          </SectionCard>
          <SectionCard title={tb("hopInspector")}>
            <ol className="divide-border-faint divide-y">
              {shown.map((hop) => (
                <li key={hop.id} className="py-2">
                  <button
                    type="button"
                    onClick={() => setOpenHop(hop.index)}
                    aria-expanded={openHop === hop.index}
                    className="grid w-full grid-cols-[28px_minmax(0,1fr)_auto] items-center gap-2 text-left text-[11px]"
                  >
                    <span className="tabular bg-surface-raised inline-flex size-6 items-center justify-center rounded-full text-[10px]">
                      {hop.index}
                    </span>
                    <span className="min-w-0 truncate">
                      <span className="text-fg">{label(hop.from)}</span> →{" "}
                      <span className="text-fg">{label(hop.to)}</span> · {hop.relation}
                    </span>
                    <span className="flex items-center gap-2">
                      <SourceBadge type={hop.sourceType} size="sm" />
                      <VerificationBadge state={hop.verification} size="sm" />
                    </span>
                  </button>
                  {openHop === hop.index ? (
                    <div className="mt-2 ml-9 space-y-2">
                      {realData && hop.provenance ? (
                        <ProvenanceSource provenance={hop.provenance} />
                      ) : realData ? (
                        <p className="text-fg-body text-[12px]">{hop.note}</p>
                      ) : (
                        <p className="text-fg-body font-serif text-[12px]">
                          “Generic verbatim excerpt for hop {hop.index} (demo).”
                        </p>
                      )}
                      <div className="flex flex-wrap items-center gap-2">
                        <CitationChip citation={hop.citation} />
                        <span
                          className={`rounded-badge px-1.5 py-0.5 text-[10px] date-${hop.dateType}`}
                        >
                          {hop.date} · {hop.dateType}
                        </span>
                        <ActionLink href={hop.sourcePath ?? documentHref(hop.citation.docId)}>
                          {t("openSource")}
                        </ActionLink>
                      </div>
                    </div>
                  ) : null}
                </li>
              ))}
            </ol>
          </SectionCard>
        </div>
        <aside className="min-w-0 space-y-3">
          <Panel title={tb("composition")}>
            <KeyValue
              rows={[
                { key: "h", label: tb("hops"), value: shown.length },
                { key: "c", label: tb("citationsBacking"), value: shown.length },
                {
                  key: "v",
                  label: tb("humanVerified"),
                  value: shown.filter((h) => h.verification === "verified").length,
                },
                { key: "t", label: tb("intermediateTypes"), value: "exhibit · incident · witness" },
              ]}
            />
          </Panel>
          {!realData ? (
            <Panel title={tb("alternates")}>
              <ol className="space-y-1">
                {[
                  { hops: 4, via: "P00123 · I-DEMO-01 · W01234" },
                  { hops: 5, via: "T-DEMO-01 · P00123" },
                ].map((a, i) => (
                  <li key={i}>
                    <button
                      type="button"
                      onClick={() => setAlternate(i)}
                      aria-current={alternate === i ? "true" : undefined}
                      className={`rounded-control w-full px-2 py-1.5 text-left text-[11px] ${alternate === i ? "bg-surface-high text-fg" : "text-fg-secondary"}`}
                    >
                      <span className="tabular">
                        {a.hops} {tb("hops").toLowerCase()}
                      </span>{" "}
                      · {tb("viaRefs")} {a.via}
                    </button>
                  </li>
                ))}
              </ol>
            </Panel>
          ) : null}
          <Panel title={t("cannotTell")}>
            <ul className="text-fg-secondary list-disc space-y-1 pl-4 text-[11px]">
              <li>{t("cannotRealWorld")}</li>
              <li>{t("cannotKnowledge")}</li>
              <li>{t("cannotSignificance")}</li>
            </ul>
            <p className="text-fg mt-2 text-[11px]">{t("canTell")}</p>
          </Panel>
          <NoteStrip>{footer("network")}</NoteStrip>
        </aside>
      </div>
    </AppShell>
  );
}

function PathNode({ label }: { label: string }) {
  return (
    <span className="border-accent bg-surface text-fg rounded-full border px-3 py-1.5 text-[11px] whitespace-nowrap">
      {label}
    </span>
  );
}

// ------------------------------------------------------------ timeline ----

const LANES = [
  "events",
  "documents",
  "hearings",
  "testimony",
  "decisions",
  "judgment",
  "appeal",
] as const;
type Lane = (typeof LANES)[number];
const LANE_FOR: Record<DateType, Lane> = {
  event: "events",
  document: "documents",
  filing: "documents",
  testimony: "testimony",
  decision: "decisions",
};
/** Lane glyph colours — the source palette, never a severity. */
const LANE_TONE: Record<Lane, string> = {
  events: "text-incident",
  documents: "text-doc",
  hearings: "text-accent",
  testimony: "text-witness",
  decisions: "text-court",
  judgment: "text-court",
  appeal: "text-court",
};
// Labelled chips per lane before further records become exact-date markers.
const MAX_TRACKS = 3;

/** A transcript is the record of a hearing: its official reference carries a
 * `/T/` segment. Read from the reference, never guessed from a title. */
function laneOf(item: MockTimelineItem): Lane {
  if (item.dateType === "document" && item.documentRef && /\/T\//u.test(item.documentRef)) {
    return "hearings";
  }
  return LANE_FOR[item.dateType];
}

function DateGlyph({ type, className }: { type: DateType; className?: string }) {
  const tone =
    type === "event"
      ? "text-incident"
      : type === "testimony"
        ? "text-witness"
        : type === "decision"
          ? "text-court"
          : "text-doc";
  return (
    <span
      aria-hidden
      className={cn(
        "inline-block size-2 shrink-0",
        tone,
        type === "event" && "rotate-45 bg-current",
        type === "testimony" && "rounded-full bg-current",
        type === "filing" && "border border-current",
        (type === "document" || type === "decision") && "bg-current",
        className,
      )}
    />
  );
}

interface Era {
  key: "historical" | "proceedings";
  start: number;
  end: number;
  ticks: { at: number; label: string }[];
  empty: boolean;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function buildEra(key: Era["key"], dates: number[]): Era {
  if (!dates.length) {
    return { key, start: 0, end: 1, ticks: [], empty: true };
  }
  const first = new Date(Math.min(...dates));
  const last = new Date(Math.max(...dates));
  if (key === "proceedings" || last.getUTCFullYear() - first.getUTCFullYear() > 3) {
    const y0 = first.getUTCFullYear();
    const y1 = last.getUTCFullYear() + 1;
    const ticks = [];
    for (let y = y0; y < y1; y += 1) ticks.push({ at: Date.UTC(y, 0, 1), label: String(y) });
    return { key, start: Date.UTC(y0, 0, 1), end: Date.UTC(y1, 0, 1), ticks, empty: false };
  }
  const m0 = Date.UTC(first.getUTCFullYear(), first.getUTCMonth() - (first.getUTCMonth() % 3), 1);
  const end = Date.UTC(last.getUTCFullYear(), last.getUTCMonth() + 1, 1);
  const ticks = [];
  for (let t = m0; t < end;) {
    const d = new Date(t);
    ticks.push({
      at: t,
      label: `${MONTHS[d.getUTCMonth()]} ${String(d.getUTCFullYear()).slice(2)}`,
    });
    t = Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 3, 1);
  }
  return { key, start: m0, end, ticks, empty: false };
}

/** The date as recorded, with its precision stated — an uncertain date is
 * never shown as if it were exact. */
function formatDate(item: MockTimelineItem): string {
  const approximate = item.datePrecision === "approximate";
  const range = `${item.date}${item.dateTo ? ` — ${item.dateTo}` : ""}`;
  const precision =
    item.datePrecision && item.datePrecision !== "exact" ? ` (${item.datePrecision})` : "";
  return `${approximate ? "≈ " : ""}${range}${precision}`;
}

function pct(era: Era, time: number): number {
  return ((time - era.start) / (era.end - era.start)) * 100;
}

export function TimelineScreen({ initialItems }: { initialItems?: readonly TimelineItem[] }) {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const tt = useTranslations("timelineDesign");
  const ts = useTranslations("screens");
  const realData = initialItems !== undefined;
  const items = initialItems ?? mockRepository.getTimeline();
  const [visible, setVisible] = useState<Set<Lane>>(new Set(LANES));
  const [selected, setSelected] = useState<MockTimelineItem | null>(items[0] ?? null);
  const [zoom, setZoom] = useState({ historical: 1, proceedings: 1 });
  const [filters, setFilters] = useState<{ id: string; label: string }[]>(
    realData ? [] : [{ id: "witness", label: "W01234" }],
  );
  const dateLabel: Record<DateType, string> = {
    event: t("event"),
    document: t("document"),
    filing: t("filing"),
    testimony: t("testimonyDate"),
    decision: t("decision"),
  };
  const timeOf = (item: MockTimelineItem) => Date.parse(item.date);
  const dated = items.filter((item) => Number.isFinite(timeOf(item)));
  const isHistorical = (item: MockTimelineItem) => Number(item.date.slice(0, 4)) < 2020;
  const eras: Era[] = [
    buildEra("historical", dated.filter(isHistorical).map(timeOf)),
    buildEra("proceedings", dated.filter((item) => !isHistorical(item)).map(timeOf)),
  ];
  // An era without records keeps a narrow column (it is never removed).
  const eraWeight = (era: Era) => (era.empty ? 0.22 : era.key === "historical" ? 0.8 : 1.6);
  const columns = eras.map((era) => `${eraWeight(era) * zoom[era.key]}fr`).join(" ");
  const chipPct = (era: Era) => 19 / (eraWeight(era) * zoom[era.key]);
  const orderedItems = [...items]
    .filter((item) => visible.has(laneOf(item)))
    .sort((a, b) => a.date.localeCompare(b.date));
  const selectedLane = selected ? laneOf(selected) : null;
  return (
    <AppShell footer={t("sequenceNote")}>
      <Toolbar className="min-h-11">
        <div className="mr-2 flex items-baseline gap-2">
          <h1 className="text-fg text-[15px] font-semibold">{ts("timeline")}</h1>
          <span className="text-fg-muted hidden text-[9px] lg:inline">
            {tt("recordCount", { count: items.length })}
          </span>
        </div>
        <ActiveFilters
          filters={filters}
          onRemove={(id) => setFilters((f) => f.filter((x) => x.id !== id))}
          onClearAll={() => setFilters([])}
        />
        <div className="ml-auto flex flex-wrap items-center gap-1">
          {!realData ? <DemoNotice /> : null}
          {eras.map((era) => (
            <span key={era.key} className="inline-flex items-center gap-1 text-[10px]">
              <span className="text-fg-secondary">
                {tb(era.key === "historical" ? "eraHistorical" : "eraProceedings")}
              </span>
              <ToolButton
                ariaLabel={`${tb("zoomEra", { era: era.key })} −`}
                onClick={() =>
                  setZoom((z) => ({ ...z, [era.key]: Math.max(0.5, z[era.key] - 0.25) }))
                }
              >
                −
              </ToolButton>
              <ToolButton
                ariaLabel={`${tb("zoomEra", { era: era.key })} +`}
                onClick={() =>
                  setZoom((z) => ({ ...z, [era.key]: Math.min(3, z[era.key] + 0.25) }))
                }
              >
                +
              </ToolButton>
            </span>
          ))}
        </div>
      </Toolbar>
      <div className="border-border-subtle flex flex-wrap items-center gap-x-4 gap-y-1 border-b px-4 py-1.5 text-[10px]">
        <span className="section-label">{tt("dateTypesShown")}</span>
        {(Object.keys(dateLabel) as DateType[]).map((d) => (
          <span key={d} className="text-fg-secondary inline-flex items-center gap-1.5">
            <DateGlyph type={d} />
            {dateLabel[d]}
          </span>
        ))}
        <span className="text-fg-muted ml-auto hidden text-[10px] lg:inline">
          {tb("dateMergeNote")}
        </span>
      </div>
      <div className="grid min-h-0 w-full min-w-0 flex-1 xl:grid-cols-[minmax(0,1fr)_314px]">
        <div className="min-w-0">
          <div className="hidden overflow-x-auto md:block">
            <div className="grid min-w-[880px] grid-cols-[170px_minmax(0,1fr)]">
              <div className="section-label border-border-faint flex items-end border-r border-b px-3 pb-2">
                {tb("layers")}
              </div>
              <div
                className="border-border-faint grid border-b"
                style={{ gridTemplateColumns: columns }}
              >
                {eras.map((era) => (
                  <div
                    key={era.key}
                    className={cn(
                      "relative min-w-0 px-2 pt-2 pb-5",
                      era.key === "historical" && "border-border border-r border-dashed",
                    )}
                  >
                    <div
                      className={cn(
                        "truncate text-[10px] font-semibold tracking-wide uppercase",
                        era.key === "historical" ? "text-incident" : "text-court",
                      )}
                    >
                      {tt(era.key === "historical" ? "eventsEra" : "proceedingsEra")}
                      {era.empty
                        ? ""
                        : ` · ${new Date(era.start).getUTCFullYear()} – ${new Date(era.end - 1).getUTCFullYear()}`}
                    </div>
                    {era.empty ? (
                      <div className="text-fg-muted mt-0.5 text-[9px] leading-tight">
                        {tt("noHistorical")}
                      </div>
                    ) : (
                      era.ticks.map((tick) => (
                        <span
                          key={tick.at}
                          className="tabular text-fg-muted absolute bottom-1 text-[9px]"
                          style={{ left: `${pct(era, tick.at)}%` }}
                        >
                          {tick.label}
                        </span>
                      ))
                    )}
                  </div>
                ))}
              </div>
              {LANES.map((lane) => {
                const laneItems = dated
                  .filter((item) => laneOf(item) === lane)
                  .sort((a, b) => a.date.localeCompare(b.date));
                const on = visible.has(lane);
                return (
                  <div key={lane} className="contents">
                    <button
                      type="button"
                      aria-label={tb(`lanes.${lane}`)}
                      aria-pressed={on}
                      onClick={() =>
                        setVisible((v) => {
                          const n = new Set(v);
                          if (n.has(lane)) n.delete(lane);
                          else n.add(lane);
                          return n;
                        })
                      }
                      className={cn(
                        "border-border-faint flex items-center gap-2 border-r border-b px-3 text-left text-[11px]",
                        selectedLane === lane && "bg-surface-raised",
                        on ? "text-fg" : "text-fg-muted line-through",
                      )}
                    >
                      <span
                        aria-hidden
                        className={cn("inline-block size-2 bg-current", LANE_TONE[lane])}
                      />
                      <span className="font-medium">{tb(`lanes.${lane}`)}</span>
                      <span className="tabular text-fg-muted ml-auto text-[9px]">
                        {laneItems.length}
                      </span>
                    </button>
                    <div
                      className="border-border-faint grid min-h-12 border-b"
                      style={{ gridTemplateColumns: columns }}
                    >
                      {eras.map((era) => {
                        const eraItems = laneItems.filter((item) =>
                          era.key === "historical" ? isHistorical(item) : !isHistorical(item),
                        );
                        // Greedy packing: a chip takes the first track whose
                        // last chip ends before it; the rest are markers at
                        // their exact date — every record stays drawn.
                        const trackEnds: number[] = [];
                        const chips: { item: MockTimelineItem; x: number; track: number }[] = [];
                        const markers: { item: MockTimelineItem; x: number }[] = [];
                        for (const item of eraItems) {
                          const x = pct(era, timeOf(item));
                          const track = trackEnds.findIndex((end) => end <= x);
                          if (track >= 0) {
                            trackEnds[track] = x + chipPct(era);
                            chips.push({ item, x, track });
                          } else if (trackEnds.length < MAX_TRACKS) {
                            trackEnds.push(x + chipPct(era));
                            chips.push({ item, x, track: trackEnds.length - 1 });
                          } else {
                            markers.push({ item, x });
                          }
                        }
                        const height =
                          10 + Math.max(1, trackEnds.length) * 22 + (markers.length ? 14 : 0);
                        return (
                          <div
                            key={era.key}
                            data-era={era.key}
                            className={cn(
                              "relative min-w-0 overflow-hidden",
                              era.key === "historical" && "border-border border-r border-dashed",
                            )}
                            style={{ height }}
                          >
                            {era.ticks.map((tick) => (
                              <span
                                key={tick.at}
                                aria-hidden
                                className="border-border-faint absolute inset-y-0 border-l"
                                style={{ left: `${pct(era, tick.at)}%` }}
                              />
                            ))}
                            {on && era.key === "proceedings" && laneItems.length === 0 ? (
                              <span className="text-fg-muted absolute inset-y-0 left-2 flex items-center text-[10px]">
                                {tb("emptyLane")}
                              </span>
                            ) : null}
                            {on
                              ? chips.map(({ item, x, track }) => (
                                  <button
                                    key={item.id}
                                    type="button"
                                    title={`${item.date} · ${item.label}`}
                                    onClick={() => setSelected(item)}
                                    aria-pressed={selected?.id === item.id}
                                    className={cn(
                                      "rounded-badge bg-surface-raised absolute z-10 flex items-center gap-1.5 overflow-hidden px-1.5 py-0.5 text-[10px]",
                                      `date-${item.dateType}`,
                                      selected?.id === item.id &&
                                        "ring-accent bg-surface-high ring-1",
                                    )}
                                    style={{
                                      // Exactly the track slot: chips never
                                      // overlap, and ones at the era's end
                                      // stay inside it (the title keeps the date).
                                      left: `${Math.min(x, 100 - chipPct(era))}%`,
                                      width: `${chipPct(era) - 0.4}%`,
                                      top: 6 + track * 22,
                                    }}
                                  >
                                    <DateGlyph type={item.dateType} />
                                    <span className="truncate">{item.label}</span>
                                  </button>
                                ))
                              : null}
                            {on
                              ? markers.map(({ item, x }) => (
                                  <button
                                    key={item.id}
                                    type="button"
                                    title={`${item.date} · ${item.label}`}
                                    aria-label={`${item.date} · ${item.label}`}
                                    onClick={() => setSelected(item)}
                                    className={cn(
                                      "absolute z-10 -translate-x-1/2 p-0.5",
                                      selected?.id === item.id && "ring-accent rounded ring-1",
                                    )}
                                    style={{ left: `${x}%`, bottom: 3 }}
                                  >
                                    <DateGlyph type={item.dateType} />
                                  </button>
                                ))
                              : null}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
            <p className="text-fg-muted px-3 pt-2 text-[10px]">{tt("markersNote")}</p>
            {realData ? (
              <p className="text-fg-muted px-3 pb-2 text-[10px]">{tb("realDataNotice")}</p>
            ) : null}
          </div>
          <ol className="space-y-2 p-3 md:hidden">
            {orderedItems.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  onClick={() => setSelected(item)}
                  className="border-border-subtle bg-surface hover:bg-surface-raised rounded-card grid w-full gap-1 border p-3 text-left text-[11px]"
                >
                  <span className="flex items-center gap-2">
                    <DateGlyph type={item.dateType} />
                    <span className="text-fg-secondary text-[10px]">
                      {dateLabel[item.dateType]} · {tb(`lanes.${laneOf(item)}`)}
                    </span>
                  </span>
                  <span className="text-fg font-medium">{item.label}</span>
                  <span className="text-fg-muted tabular text-[10px]">
                    {item.date}
                    {item.dateTo ? ` — ${item.dateTo}` : ""}
                  </span>
                </button>
              </li>
            ))}
          </ol>
        </div>
        <aside className="border-border-subtle bg-bg-deep flex min-w-0 flex-col gap-3 border-l p-3 xl:sticky xl:top-0 xl:self-start">
          <p className="section-label">{tt("selectedCard")}</p>
          {selected ? (
            <div className="border-accent/40 bg-surface rounded-card space-y-2 border p-3">
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    "rounded-badge px-1.5 py-0.5 text-[9px] font-semibold uppercase",
                    `date-${selected.dateType}`,
                  )}
                >
                  {dateLabel[selected.dateType]}
                </span>
                <span className="tabular text-fg-secondary text-[11px]">
                  {formatDate(selected)}
                </span>
              </div>
              <h2 className="text-fg text-[13px] leading-snug font-semibold">{selected.label}</h2>
              {selected.description ? (
                <p className="text-fg-secondary text-[11px] leading-relaxed">
                  {selected.description}
                </p>
              ) : null}
              <p className="text-fg-muted text-[10px]">
                {tb("drawnOn")}: {tb(`lanes.${laneOf(selected)}`)}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {selected.documentRef ? (
                  <Link
                    href={selected.href}
                    className="rounded-badge identifier border-doc/50 text-doc border px-1.5 py-0.5 text-[10px]"
                  >
                    {selected.documentRef} →
                  </Link>
                ) : null}
                {!realData ? <CitationChip citation={courtCitation} size="sm" /> : null}
              </div>
            </div>
          ) : (
            <p className="text-fg-secondary text-[11px]">{tb("selectCard")}</p>
          )}
          {selected ? (
            <>
              <p className="section-label">{tt("datesAttached")}</p>
              <div className="border-border-subtle rounded-card border">
                <div className="bg-surface flex items-center justify-between px-3 py-1.5 text-[11px]">
                  <span className="flex items-center gap-1.5">
                    <DateGlyph type={selected.dateType} />
                    {dateLabel[selected.dateType]}
                  </span>
                  <span className="tabular text-fg">{formatDate(selected)}</span>
                </div>
              </div>
              <p className="text-fg-muted text-[10px]">{tt("oneCardManyDates")}</p>
              <p className="section-label">{tb("linkedFrom")}</p>
              <ul className="space-y-1.5 text-[11px]">
                {selected.documentRef ? (
                  <li className="border-border-subtle rounded-card flex items-center justify-between border px-3 py-1.5">
                    <span className="text-fg-secondary">{tt("document")}</span>
                    <Link href={selected.href} className="text-accent">
                      {t("open")} →
                    </Link>
                  </li>
                ) : null}
                <li className="border-border-subtle rounded-card flex items-center justify-between border px-3 py-1.5">
                  <span className="text-fg-secondary">{tt("networkView")}</span>
                  <Link
                    href={`/network${selected.documentRef ? `?focus=${encodeURIComponent(selected.documentRef)}` : ""}`}
                    className="text-accent"
                  >
                    {t("open")} →
                  </Link>
                </li>
                {selected.sourceUrl ? (
                  <li className="border-border-subtle rounded-card flex items-center justify-between border px-3 py-1.5">
                    <span className="text-fg-secondary">{tt("officialSource")}</span>
                    <a href={selected.sourceUrl} className="text-accent">
                      {t("open")} ↗
                    </a>
                  </li>
                ) : null}
              </ul>
            </>
          ) : null}
          <p className="text-fg-muted border-border-subtle mt-auto border-t pt-2 text-[10px] leading-relaxed">
            {t("sequenceNote")}
          </p>
        </aside>
      </div>
    </AppShell>
  );
}

// ------------------------------------------------------------ incident ----

const INCIDENT_TABS = [
  "overview",
  "evidence",
  "findings",
  "witnesses",
  "documents",
  "timeline",
  "network",
  "arguments",
  "research",
] as const;

export function IncidentScreen({ id }: { id: string }) {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const evidence = mockRepository.getEvidence();
  const [direction, setDirection] = useState<Direction | "all">("all");
  const [courtCited, setCourtCited] = useState<"all" | "yes" | "no">("all");
  const [sortDir, setSortDir] = useState(false);
  const cited = (i: number) => i % 2 === 0;
  const rows = evidence
    .map((row, i) => ({ ...row, cited: cited(i) }))
    .filter(
      (r) =>
        (direction === "all" || r.direction === direction) &&
        (courtCited === "all" || (courtCited === "yes") === r.cited),
    );
  const sorted = sortDir ? [...rows].sort((a, b) => a.direction.localeCompare(b.direction)) : rows;
  const summary = (["supports", "contradicts", "qualifies", "neutral"] as const).map((d) => ({
    key: d,
    label: tb(d),
    value: evidence.filter((e) => e.direction === d).length,
  }));
  return (
    <AppShell
      footer={tb("incidentFooter")}
      crumbs={[{ label: t("incidents"), href: "/incidents" }, { label: id }]}
    >
      <header className="border-border-subtle bg-bg-deep border-b px-4 py-4">
        <div className="mx-auto flex w-full max-w-[1440px] flex-wrap items-start gap-4">
          <span
            aria-hidden
            className="border-incident mt-1 inline-block size-8 shrink-0 rotate-45 border-2"
          />
          <div className="min-w-0 flex-1">
            <h1 className="text-fg text-[24px] leading-tight font-bold tracking-[-0.02em]">
              Illustrative recorded event
            </h1>
            <p className="text-fg-secondary mt-1 text-[11px]">
              <span className="identifier">{id}</span> · {tb("eventDates")}:{" "}
              <span className="tabular">1999-05-01 — 1999-05-03</span> · {tb("location")}: Demo
              Village ({tb("recordedVariants")}: Fshati Demo · Demo-Village)
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              <span className="rounded-badge border-border bg-surface-raised border px-1.5 py-0.5 text-[10px]">
                Count 1 · demo
              </span>
              <span className="rounded-badge border-border bg-surface-raised border px-1.5 py-0.5 text-[10px]">
                Count 3 · demo
              </span>
              <span className="text-fg-muted text-[10px]">{t("chargeNote")}</span>
            </div>
          </div>
          <div className="flex gap-2">
            <ActionLink href={`/timeline?incident=${id}`}>{t("viewTimeline")}</ActionLink>
            <ActionLink href={`/network?focus=${id}`}>{t("viewNetwork")}</ActionLink>
            <ActionLink href="/ai" primary>
              {t("askAi")}
            </ActionLink>
          </div>
        </div>
      </header>
      <TabStrip
        tabs={INCIDENT_TABS.map((k) => ({
          key: k,
          label:
            k === "evidence"
              ? t("evidenceMatrix")
              : k === "witnesses"
                ? tb("witnesses")
                : tb(`tabs.${k}`),
        }))}
        active="evidence"
      />
      <div className="mx-auto grid w-full max-w-[1440px] min-w-0 flex-1 gap-3 p-3 md:p-4 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div className="min-w-0 space-y-3">
          <DemoNotice />
          <StatStrip label={tb("directionSummary")} items={summary} columns={4} />
          <SectionCard
            title={t("evidenceMatrix")}
            aside={
              <div className="flex flex-wrap gap-2">
                <Segmented
                  label={tb("directionFilter")}
                  value={direction}
                  onChange={setDirection}
                  options={[
                    { key: "all", label: tb("allCategories") },
                    { key: "supports", label: tb("supports") },
                    { key: "contradicts", label: tb("contradicts") },
                    { key: "qualifies", label: tb("qualifies") },
                    { key: "neutral", label: tb("neutral") },
                  ]}
                />
                <Segmented
                  label={tb("courtCitedFilter")}
                  value={courtCited}
                  onChange={setCourtCited}
                  options={[
                    { key: "all", label: tb("allCategories") },
                    { key: "yes", label: tb("yes") },
                    { key: "no", label: tb("no") },
                  ]}
                />
                <ToolButton pressed={sortDir} onClick={() => setSortDir((v) => !v)}>
                  {t("sort")}
                </ToolButton>
              </div>
            }
          >
            <ScopeNote />
            <div className="mt-2 overflow-x-auto">
              <table className="w-full text-[11px]">
                <thead>
                  <tr className="text-fg-secondary text-left">
                    {(["source", "claim", "direction", "courtCited", "verification"] as const).map(
                      (c) => (
                        <th
                          key={c}
                          className="border-border-faint border-b px-2 py-1.5 font-medium"
                        >
                          {tb(`matrixColumns.${c}`)}
                        </th>
                      ),
                    )}
                  </tr>
                </thead>
                <tbody>
                  {sorted.map((row) => (
                    <tr key={row.id} className="border-border-faint border-b align-top">
                      <td className="px-2 py-2">
                        <SourceBadge type={row.sourceType} size="sm" />
                        <div className="mt-1">
                          <CitationChip citation={row.citation} size="sm" />
                        </div>
                      </td>
                      <td className="px-2 py-2 font-serif text-[12px]">{row.claim}</td>
                      <td className="px-2 py-2">
                        <DirectionBadge direction={row.direction} />
                      </td>
                      <td className="tabular px-2 py-2">
                        {row.cited ? `${tb("yes")} · ¶46` : tb("no")}
                      </td>
                      <td className="px-2 py-2">
                        <VerificationBadge state={row.verification} size="sm" />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {sorted.length === 0 ? (
              <p className="text-fg-secondary mt-2 text-[11px]">{tb("noContrary")}</p>
            ) : null}
            <p className="text-fg-muted mt-2 text-[10px]">{tb("matrixNote")}</p>
          </SectionCard>
        </div>
        <aside className="min-w-0 space-y-3">
          <RecordBlock sourceType="court" title={t("courtFinding")} citations={[courtCitation]}>
            <p className="font-serif">
              “Generic demo wording of a court finding about this event.”
            </p>
          </RecordBlock>
          <RecordBlock sourceType="spo" title={t("spo")} citations={[courtCitation]}>
            Demo prosecution position, shown as an argument.
          </RecordBlock>
          <RecordBlock sourceType="defence" title={t("defence")} citations={[courtCitation]}>
            Demo defence position, shown separately with the same treatment.
          </RecordBlock>
          <Panel title={tb("witnessesInRecord")}>
            <div className="flex flex-wrap gap-1.5">
              <Link
                href="/witnesses/W01234"
                className="rounded-badge border-witness identifier border border-dashed px-1.5 py-0.5 text-[10px]"
              >
                W01234
              </Link>
              <Link
                href="/witnesses/W04567"
                className="rounded-badge border-witness border px-1.5 py-0.5 text-[10px]"
              >
                W04567
              </Link>
            </div>
          </Panel>
        </aside>
      </div>
    </AppShell>
  );
}

// ------------------------------------------------------------- finding ----

const CHAIN = [
  "courtFinding",
  "evidenceReliedUpon",
  "whatSourcesSay",
  "otherMaterial",
  "trialArguments",
  "courtResponse",
  "potentialIssues",
  "redTeam",
  "sourceAudit",
] as const;

export function FindingDetailScreen({ id }: { id: string }) {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const evidence = mockRepository.getEvidence();
  const [tab, setTab] = useState<"chain" | "quotes" | "arguments" | "annotations">("chain");
  const index = CHAIN.map((k, i) => ({
    id: `step-${k}`,
    label: t(k),
    number: String(i + 1).padStart(2, "0"),
  }));
  const direction = (["supports", "contradicts", "qualifies", "neutral"] as const).map((d) => ({
    key: d,
    label: tb(d),
    value: evidence.filter((e) => e.direction === d).length,
    href: `/incidents/I-DEMO-01?tab=evidence&direction=${d}`,
  }));
  return (
    <AppShell crumbs={[{ label: t("courtFindings"), href: "/findings" }, { label: id }]}>
      <ScreenHeader
        eyebrow={<span className="identifier">{id} · Judgment ¶45–46</span>}
        title="Illustrative finding"
        description={t("mockNotice")}
        actions={
          <>
            <ActionLink href="/appeal/argument/new">{t("sendToLab")}</ActionLink>
            <Segmented
              label={t("viewDetails")}
              value={tab}
              onChange={setTab}
              options={[
                { key: "chain", label: tb("chainIndex") },
                { key: "quotes", label: tb("verbatim") },
                { key: "arguments", label: t("arguments") },
                { key: "annotations", label: t("addNote") },
              ]}
            />
          </>
        }
      />
      <div className="mx-auto grid w-full max-w-[1440px] min-w-0 flex-1 gap-3 p-3 md:p-4 lg:grid-cols-[236px_minmax(0,1fr)] xl:grid-cols-[236px_minmax(0,1fr)_316px]">
        <RailIndex
          label={tb("chainIndex")}
          items={index}
          extra={
            <Panel title={tb("relatedFindings")}>
              <ul className="space-y-1 text-[11px]">
                <li>
                  <Link href="/findings/FD-DEMO-2002" className="text-accent">
                    FD-DEMO-2002
                  </Link>{" "}
                  · Demo record 02
                </li>
              </ul>
            </Panel>
          }
        />
        <ol className="border-border-subtle relative min-w-0 space-y-3 border-l pl-6">
          {CHAIN.map((step, i) => (
            <li key={step} className="relative">
              <span
                aria-hidden
                className="bg-surface-high text-fg tabular absolute top-3 -left-[35px] inline-flex size-5 items-center justify-center rounded-full text-[10px]"
              >
                {i + 1}
              </span>
              <SectionCard
                id={`step-${step}`}
                number={String(i + 1).padStart(2, "0")}
                title={t(step)}
              >
                {step === "courtFinding" ? (
                  <RecordBlock sourceType="court" citations={[courtCitation]}>
                    <p className="font-serif text-[13px]">
                      “Generic demo wording of the finding, quoted verbatim with its paragraph
                      range.”
                    </p>
                    <div className="mt-2 flex gap-2">
                      <VerificationBadge state="verified" size="sm" />
                      <span className="text-fg-muted text-[10px]">demo-reviewer · 2026-09-20</span>
                    </div>
                  </RecordBlock>
                ) : null}
                {step === "evidenceReliedUpon" ? (
                  <ul className="divide-border-faint divide-y">
                    {evidence.map((row) => (
                      <li
                        key={row.id}
                        className="flex flex-wrap items-center gap-2 py-1.5 text-[11px]"
                      >
                        <SourceBadge type={row.sourceType} size="sm" />
                        <span className="min-w-0 flex-1">{row.claim}</span>
                        <CitationChip citation={row.citation} size="sm" />
                        <span className="text-fg-muted text-[10px]">{tb("extent")}: 1 ¶</span>
                      </li>
                    ))}
                  </ul>
                ) : null}
                {step === "whatSourcesSay" ? (
                  <div className="grid gap-2 md:grid-cols-2">
                    {[transcriptCitation, exhibitCitation].map((c) => (
                      <RecordBlock key={c.display} sourceType={c.sourceType} citations={[c]}>
                        <p className="font-serif">“Generic verbatim demo excerpt.”</p>
                        <p className="text-fg-muted mt-1 text-[10px]">
                          {tb("speaker")}: {c.sourceType === "witness" ? "W01234" : "—"}
                        </p>
                      </RecordBlock>
                    ))}
                  </div>
                ) : null}
                {step === "otherMaterial" ? (
                  <>
                    <StatStrip items={direction} label={tb("directionCounts")} columns={4} />
                    <ScopeNote />
                    <p className="text-fg-secondary mt-2 text-[11px]">
                      {evidence.some((e) => e.direction === "contradicts") ? "" : tb("noContrary")}
                    </p>
                  </>
                ) : null}
                {step === "trialArguments" ? (
                  <div className="grid gap-2 md:grid-cols-2">
                    <RecordBlock sourceType="spo" citations={[courtCitation]}>
                      Demo SPO submission.
                    </RecordBlock>
                    <RecordBlock sourceType="defence" citations={[courtCitation]}>
                      Demo Defence submission.
                    </RecordBlock>
                  </div>
                ) : null}
                {step === "courtResponse" ? (
                  <RecordBlock sourceType="court" citations={[courtCitation]}>
                    <p className="font-serif">
                      “Generic demo wording of the Panel’s response to both submissions.”
                    </p>
                  </RecordBlock>
                ) : null}
                {step === "potentialIssues" ? (
                  <ul className="space-y-1 text-[11px]">
                    <li className="flex justify-between gap-2">
                      <span>
                        {tb("categories.evidence")} · demo question about the extent of the cited
                        passage
                      </span>
                      <span className="rounded-badge bg-surface-raised px-1.5 text-[10px]">
                        {tb("reviewStates.awaiting")}
                      </span>
                    </li>
                  </ul>
                ) : null}
                {step === "redTeam" ? (
                  <div className="grid gap-2 md:grid-cols-2">
                    <Panel title={t("defenceAnalyst")}>
                      <p className="text-[11px]">Demo counter-reading, cited.</p>
                    </Panel>
                    <Panel title={t("spoRedTeam")}>
                      <p className="text-[11px]">Demo response, cited.</p>
                    </Panel>
                  </div>
                ) : null}
                {step === "sourceAudit" ? (
                  <KeyValue
                    rows={[
                      { key: "t", label: tb("audit.citationsTotal"), value: 4 },
                      { key: "r", label: tb("audit.citationsResolved"), value: 4 },
                      { key: "h", label: tb("audit.humanVerified"), value: 2 },
                      { key: "d", label: tb("audit.redacted"), value: 0 },
                    ]}
                  />
                ) : null}
              </SectionCard>
            </li>
          ))}
        </ol>
        <aside className="min-w-0 space-y-3 lg:col-span-2 xl:col-span-1">
          <Panel title={tb("analysis")}>
            <StatStrip items={direction} columns={2} />
          </Panel>
          <Panel title={tb("issuesReview")}>
            <KeyValue
              rows={[{ key: "s", label: tb("reviewState"), value: tb("reviewStates.awaiting") }]}
            />
            <div className="mt-2">
              <ActionLink href="/appeal">{t("appealReview")}</ActionLink>
            </div>
          </Panel>
          <AiAnalysisBlock citations={[courtCitation]}>
            Demo analysis of where the sources address the finding. No prediction is produced.
          </AiAnalysisBlock>
          <NoteStrip>{t("noPrediction")}</NoteStrip>
        </aside>
      </div>
    </AppShell>
  );
}
