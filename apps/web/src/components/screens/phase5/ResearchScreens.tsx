"use client";

import type { AnswerBlockKind, DateType, SourceType } from "@ksc/shared";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useRef, useState } from "react";
import { Panel } from "@/components/primitives/Panel";
import {
  AiAnalysisBlock,
  CitationChip,
  DirectionBadge,
  ProvenanceBoundary,
  RecordBlock,
  ScopeNote,
  SourceBadge,
  VerificationBadge,
} from "@/components/provenance";
import { AppShell } from "@/components/shell/AppShell";
import { courtCitation, exhibitCitation, mockRepository, transcriptCitation } from "@/mock";
import { ActionLink, DemoNotice, ScreenHeader, TabStrip, WorkspaceGrid } from "./ScreenChrome";

const sourceForAnswer: Record<
  Exclude<AnswerBlockKind, "ai">,
  Exclude<SourceType, "ai" | "incident" | "location" | "organisation">
> = { court: "court", evidence: "exhibit", testimony: "witness", spo: "spo", defence: "defence" };

export function EvidenceExplorerScreen() {
  const t = useTranslations("phase5");
  const rows = mockRepository.getDirectory("exhibits");
  return (
    <AppShell>
      <ScreenHeader
        eyebrow={t("allRecords")}
        title={t("exhibits")}
        description={t("mockNotice")}
        actions={
          <>
            <button className="border-border bg-surface-raised rounded-control border px-3 py-1.5 text-[11px]">
              {t("filter")}
            </button>
            <button className="border-border bg-surface-raised rounded-control border px-3 py-1.5 text-[11px]">
              {t("export")}
            </button>
          </>
        }
      />
      <WorkspaceGrid
        right={
          <Panel title={t("viewDetails")}>
            <SourceBadge type="exhibit" />
            <h2 className="text-fg mt-2 font-semibold">P00123</h2>
            <p className="text-fg-secondary mt-2 text-[11px]">
              Generic sample record with mock provenance.
            </p>
            <div className="mt-3">
              <CitationChip citation={exhibitCitation} />
            </div>
          </Panel>
        }
      >
        <div className="space-y-3">
          <DemoNotice />
          <Panel padded={false}>
            {rows.map((row) => (
              <Link
                key={row.id}
                href={row.href}
                className="border-border-faint hover:bg-surface-raised grid grid-cols-[100px_minmax(0,1fr)_100px_150px] items-center gap-3 border-b px-3 py-3 text-[11px]"
              >
                <span className="identifier text-doc">{row.id}</span>
                <span>
                  <strong className="text-fg block">{row.title}</strong>
                  <small className="text-fg-secondary">{row.description}</small>
                </span>
                <span className="tabular text-right">{row.references}</span>
                <VerificationBadge state={row.verification} />
              </Link>
            ))}
          </Panel>
        </div>
      </WorkspaceGrid>
    </AppShell>
  );
}

export function NetworkScreen() {
  const t = useTranslations("phase5");
  const footer = useTranslations("footer");
  const { nodes, edges } = mockRepository.getNetwork();
  const [selectedNode, setSelectedNode] = useState(nodes[0]!);
  const [selectedEdge, setSelectedEdge] = useState(edges[0]!);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [query, setQuery] = useState("");
  const [isolated, setIsolated] = useState(false);
  const [expanded, setExpanded] = useState(true);
  const dragStart = useRef<{
    pointerX: number;
    pointerY: number;
    panX: number;
    panY: number;
  } | null>(null);
  const neighbourIds = new Set(
    edges
      .filter((edge) => edge.from === selectedNode.id || edge.to === selectedNode.id)
      .flatMap((edge) => [edge.from, edge.to]),
  );
  const visibleNodes = isolated
    ? nodes.filter((node) => neighbourIds.has(node.id))
    : expanded
      ? nodes
      : nodes.slice(0, 3);
  const visibleNodeIds = new Set(visibleNodes.map((node) => node.id));
  const visibleEdges = edges.filter(
    (edge) => visibleNodeIds.has(edge.from) && visibleNodeIds.has(edge.to),
  );
  const listedNodes = nodes.filter((node) =>
    node.label.toLowerCase().includes(query.trim().toLowerCase()),
  );

  function handleGraphAction(key: string) {
    if (key === "zoomIn") setZoom((value) => Math.min(1.4, value + 0.1));
    if (key === "zoomOut") setZoom((value) => Math.max(0.7, value - 0.1));
    if (key === "isolate") setIsolated((value) => !value);
    if (key === "expand") setExpanded(true);
    if (key === "collapseGraph") setExpanded(false);
    if (key === "reset") {
      setZoom(1);
      setPan({ x: 0, y: 0 });
      setIsolated(false);
      setExpanded(true);
      setQuery("");
    }
  }
  return (
    <AppShell footer={footer("network")}>
      <ScreenHeader
        eyebrow={t("network")}
        title={t("network")}
        description={footer("network")}
        actions={
          <ActionLink href="/network/path?from=demo-research-subject">
            {t("findConnection")}
          </ActionLink>
        }
      />
      <div className="border-border-subtle flex flex-wrap gap-2 border-b px-4 py-2">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={t("searchWithin")}
          aria-label={t("searchWithin")}
          className="border-border bg-surface-raised rounded-control min-w-44 border px-3 py-1 text-[10px]"
        />
        {["zoomIn", "zoomOut", "reset", "isolate", "expand", "collapseGraph"].map((key) => (
          <button
            key={key}
            onClick={() => handleGraphAction(key)}
            aria-pressed={key === "isolate" ? isolated : undefined}
            className="border-border bg-surface-raised rounded-control border px-3 py-1 text-[10px]"
          >
            {t(key)}
          </button>
        ))}
      </div>
      <div className="grid min-h-[690px] flex-1 lg:grid-cols-[220px_minmax(0,1fr)_300px]">
        <aside className="border-border bg-surface hidden border-r p-3 lg:block">
          <Panel title={t("allRecords")}>
            <div className="space-y-2">
              {listedNodes.map((node) => (
                <button
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  className="hover:bg-surface-raised rounded-control flex w-full items-center gap-2 px-2 py-1.5 text-left"
                >
                  <NodeGlyph type={node.type} />
                  <span className="text-[10px]">{node.label}</span>
                </button>
              ))}
            </div>
          </Panel>
        </aside>
        <main
          className="bg-bg-graph relative min-h-[560px] cursor-grab touch-none overflow-hidden active:cursor-grabbing"
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
                const a = visibleNodes.find((node) => node.id === edge.from)!;
                const b = visibleNodes.find((node) => node.id === edge.to)!;
                return (
                  <line
                    key={edge.id}
                    x1={`${a.x}%`}
                    y1={`${a.y}%`}
                    x2={`${b.x}%`}
                    y2={`${b.y}%`}
                    stroke="var(--border)"
                    strokeWidth="2"
                    onClick={() => setSelectedEdge(edge)}
                    className="cursor-pointer"
                  />
                );
              })}
            </svg>
            {visibleNodes.map((node) => (
              <button
                key={node.id}
                onClick={() => setSelectedNode(node)}
                style={{ left: `${node.x}%`, top: `${node.y}%` }}
                className="border-accent bg-surface text-fg absolute z-10 -translate-x-1/2 -translate-y-1/2 rounded-full border px-3 py-2 text-[9px]"
              >
                {node.label}
              </button>
            ))}
          </div>
          <p className="governance-text bg-bg-deep/80 absolute right-4 bottom-4 max-w-xs rounded px-3 py-2">
            {footer("network")}
          </p>
        </main>
        <details
          open
          className="border-border bg-surface max-lg:rounded-t-sheet max-lg:shadow-sheet border-l max-lg:fixed max-lg:right-0 max-lg:bottom-14 max-lg:left-0 max-lg:z-30 max-lg:max-h-[42dvh] max-lg:overflow-auto max-lg:border-t"
        >
          <summary className="text-fg-secondary cursor-pointer list-none px-4 py-2 text-center text-[10px] font-semibold tracking-[0.16em] uppercase lg:hidden">
            {t("viewDetails")}
          </summary>
          <div className="p-3">
            <Panel title={t("nodeInspector")}>
              <NodeGlyph type={selectedNode.type} />
              <p className="text-fg mt-2 font-semibold">{selectedNode.label}</p>
            </Panel>
            <Panel className="mt-3" title={t("whyConnection")}>
              <p className="text-fg text-[11px]">{selectedEdge.relation}</p>
              <div className="mt-2">
                <SourceBadge type={selectedEdge.sourceType} />
              </div>
              <div className="mt-2">
                <CitationChip citation={selectedEdge.citation} />
              </div>
              <div className="mt-2">
                <VerificationBadge state={selectedEdge.verification} />
              </div>
              <div className="mt-3">
                <ActionLink href={`/documents/${selectedEdge.citation.docId}`}>
                  {t("openSource")}
                </ActionLink>
              </div>
            </Panel>
            <Panel className="mt-3" title={t("graphTextAlternative")}>
              <ul className="space-y-2 text-[10px]">
                {edges.map((edge) => (
                  <li key={edge.id}>
                    <button onClick={() => setSelectedEdge(edge)}>
                      {edge.from} → {edge.to}
                    </button>
                  </li>
                ))}
              </ul>
            </Panel>
          </div>
        </details>
      </div>
    </AppShell>
  );
}

function NodeGlyph({ type }: { type: string }) {
  return (
    <span
      aria-hidden
      className={`inline-block size-4 border ${type === "protected" ? "border-witness rounded-full border-dashed" : type === "incident" ? "border-incident rotate-45" : type === "court" ? "border-court rounded" : "border-accent rounded-full"}`}
    />
  );
}

export function EvidencePathScreen() {
  const t = useTranslations("phase5");
  const footer = useTranslations("footer");
  const hops = mockRepository.getPath();
  return (
    <AppShell footer={footer("network")}>
      <ScreenHeader
        eyebrow={t("findConnection")}
        title={t("findConnection")}
        description={t("pathBanner")}
        actions={<ActionLink href="/network">{t("viewNetwork")}</ActionLink>}
      />
      <WorkspaceGrid
        right={
          <>
            <Panel title={t("cannotTell")}>
              <ul className="space-y-2 text-[11px]">
                <li>✕ {t("cannotRealWorld")}</li>
                <li>✕ {t("cannotKnowledge")}</li>
                <li>✕ {t("cannotSignificance")}</li>
                <li className="text-verified">✓ {t("canTell")}</li>
              </ul>
            </Panel>
            <Panel className="mt-3" title={t("results")} footer={t("pathLimit")}>
              <p className="tabular text-fg text-[20px] font-bold">{hops.length}</p>
              <span className="text-fg-muted text-[10px]">hops · {hops.length} citations</span>
            </Panel>
          </>
        }
      >
        <div className="space-y-4">
          <DemoNotice />
          <div className="border-border bg-bg-graph rounded-card flex min-h-48 items-center gap-2 overflow-x-auto border p-6">
            {hops.map((hop, index) => (
              <div key={hop.id} className="contents">
                <div className="min-w-28 text-center">
                  <NodeGlyph type={index === 0 ? "person" : hop.sourceType} />
                  <p className="text-fg mt-2 text-[9px]">{hop.from}</p>
                </div>
                <div className="min-w-32 text-center">
                  <span className="bg-accent inline-flex size-6 items-center justify-center rounded-full text-[10px] text-white">
                    {hop.index}
                  </span>
                  <div className="border-accent mt-2 border-t"></div>
                  <small className="text-fg-muted">{hop.relation}</small>
                </div>
                {index === hops.length - 1 ? (
                  <div className="min-w-28 text-center">
                    <NodeGlyph type="court" />
                    <p className="text-fg mt-2 text-[9px]">{hop.to}</p>
                  </div>
                ) : null}
              </div>
            ))}
          </div>
          <div className="space-y-2">
            {hops.map((hop) => (
              <Panel
                key={hop.id}
                title={`${hop.index}. ${hop.from} → ${hop.to}`}
                actions={<VerificationBadge state={hop.verification} />}
              >
                <p className="text-fg-secondary mb-2 text-[11px]">
                  {hop.relation} · {hop.date} · {hop.dateType}
                </p>
                <CitationChip citation={hop.citation} />
              </Panel>
            ))}
          </div>
        </div>
      </WorkspaceGrid>
    </AppShell>
  );
}

export function TimelineScreen() {
  const t = useTranslations("phase5");
  const items = mockRepository.getTimeline();
  const label: Record<DateType, string> = {
    event: t("event"),
    document: t("document"),
    filing: t("filing"),
    testimony: t("testimonyDate"),
    decision: t("decision"),
  };
  return (
    <AppShell footer={t("sequenceNote")}>
      <ScreenHeader
        eyebrow={t("dateTypes")}
        title={t("viewTimeline")}
        description={t("sequenceNote")}
      />
      <div className="mx-auto w-full max-w-[1440px] p-4">
        <DemoNotice />
        <div className="border-border bg-surface rounded-card mt-4 overflow-hidden border">
          <div className="border-border-subtle grid grid-cols-[44%_56%] border-b">
            <div className="p-3">
              <span className="section-label">Events</span>
            </div>
            <div className="border-border border-l-2 border-dashed p-3">
              <span className="section-label">Proceedings</span>
            </div>
          </div>
          {items.map((item) => (
            <Link
              key={item.id}
              href={item.href}
              className="border-border-faint hover:bg-surface-raised grid grid-cols-[160px_minmax(0,1fr)] items-center border-b p-3"
            >
              <span className="text-fg-muted text-[10px]">{label[item.dateType]}</span>
              <span>
                <strong className="text-fg text-[11px]">{item.label}</strong>
                <small className="text-fg-muted ml-3">{item.date}</small>
              </span>
            </Link>
          ))}
        </div>
      </div>
    </AppShell>
  );
}

export function IncidentScreen({ id }: { id: string }) {
  const t = useTranslations("phase5");
  const footer = useTranslations("footer");
  const evidence = mockRepository.getEvidence();
  const tabs = [
    "overview",
    "courtFindings",
    "testimony",
    "evidenceMatrix",
    "spo",
    "defence",
    "viewTimeline",
    "network",
    "potentialIssues",
  ].map((key) => ({ key, label: t(key as never), href: `?tab=${key}` }));
  return (
    <AppShell crumbs={[{ label: id }]} footer={footer("neutrality")}>
      <ScreenHeader
        eyebrow={id}
        title="Illustrative recorded event"
        description={t("chargeNote")}
        actions={<SourceBadge type="incident" />}
      />
      <TabStrip tabs={tabs} />
      <WorkspaceGrid
        right={
          <Panel title={t("positions")}>
            <RecordBlock sourceType="spo" citations={[courtCitation]}>
              Generic illustrative SPO position.
            </RecordBlock>
            <div className="mt-3">
              <RecordBlock sourceType="defence" citations={[courtCitation]}>
                Generic illustrative Defence position.
              </RecordBlock>
            </div>
          </Panel>
        }
      >
        <div className="space-y-3">
          <DemoNotice />
          <Panel title={t("evidenceMatrix")} footer={<ScopeNote />}>
            {evidence.map((row) => (
              <div
                key={row.id}
                className="border-border-faint grid gap-2 border-b py-3 md:grid-cols-[130px_minmax(0,1fr)_120px_150px]"
              >
                <div>
                  <SourceBadge type={row.sourceType} />
                </div>
                <p className="text-fg-body text-[11px]">{row.claim}</p>
                <DirectionBadge direction={row.direction} />
                <div>
                  <VerificationBadge state={row.verification} />
                  <div className="mt-1">
                    <CitationChip citation={row.citation} size="sm" />
                  </div>
                </div>
              </div>
            ))}
          </Panel>
        </div>
      </WorkspaceGrid>
    </AppShell>
  );
}

export function FindingDetailScreen({ id }: { id: string }) {
  const t = useTranslations("phase5");
  const footer = useTranslations("footer");
  const evidence = mockRepository.getEvidence();
  const steps = [
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
  return (
    <AppShell crumbs={[{ label: id }]} footer={footer("sourceNote")}>
      <ScreenHeader
        eyebrow={id}
        title="Illustrative finding"
        description={t("mockNotice")}
        actions={<ActionLink href="/appeal/argument/new">{t("sendToLab")}</ActionLink>}
      />
      <TabStrip
        tabs={[
          { key: "chain", label: "Chain" },
          { key: "quotes", label: t("whatSourcesSay") },
          { key: "arguments", label: t("arguments") },
          { key: "annotations", label: t("addNote") },
        ]}
      />
      <WorkspaceGrid
        left={
          <Panel title={t("overview")}>
            <ol className="space-y-2">
              {steps.map((step, index) => (
                <li key={step}>
                  <a href={`#${step}`} className="text-accent text-[10px]">
                    {String(index + 1).padStart(2, "0")} · {t(step)}
                  </a>
                </li>
              ))}
            </ol>
          </Panel>
        }
        right={
          <>
            <AiAnalysisBlock title={t("potentialIssues")} citations={[courtCitation]}>
              Generic question surfaced for human review. {t("noPrediction")}
            </AiAnalysisBlock>
            <Panel className="mt-3" title={t("sourceAudit")}>
              <dl className="grid grid-cols-2 gap-2 text-[11px]">
                <dt>{t("citationStatus")}</dt>
                <dd className="text-verified">3 / 3</dd>
                <dt>{t("verificationStatus")}</dt>
                <dd>
                  <VerificationBadge state="verified" />
                </dd>
              </dl>
            </Panel>
          </>
        }
      >
        <div className="space-y-4">
          {steps.map((step, index) => (
            <section id={step} key={step} className="scroll-mt-24">
              <div className="mb-2 flex items-center gap-2">
                <span className="bg-surface-high text-fg inline-flex size-6 items-center justify-center rounded-full text-[10px]">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h2 className="text-fg text-[14px] font-semibold">{t(step)}</h2>
              </div>
              {step === "courtFinding" ? (
                <RecordBlock sourceType="court" citations={[courtCitation]}>
                  <p className="font-serif">
                    Generic sample finding. It contains no assertion about a real person.
                  </p>
                </RecordBlock>
              ) : step === "evidenceReliedUpon" || step === "whatSourcesSay" ? (
                <div className="space-y-2">
                  <RecordBlock sourceType="exhibit" citations={[exhibitCitation]}>
                    Generic sample exhibit passage.
                  </RecordBlock>
                  <RecordBlock sourceType="witness" citations={[transcriptCitation]}>
                    Generic sample testimony passage.
                  </RecordBlock>
                </div>
              ) : step === "otherMaterial" ? (
                <Panel footer={<ScopeNote />}>
                  {evidence.map((row) => (
                    <div key={row.id} className="flex items-center justify-between border-b py-2">
                      <span className="text-[10px]">{row.claim}</span>
                      <DirectionBadge direction={row.direction} />
                    </div>
                  ))}
                </Panel>
              ) : step === "trialArguments" ? (
                <div className="grid gap-3 md:grid-cols-2">
                  <RecordBlock sourceType="defence" citations={[courtCitation]}>
                    Generic Defence argument.
                  </RecordBlock>
                  <RecordBlock sourceType="spo" citations={[courtCitation]}>
                    Generic SPO argument.
                  </RecordBlock>
                </div>
              ) : step === "potentialIssues" || step === "redTeam" ? (
                <>
                  <ProvenanceBoundary />
                  <AiAnalysisBlock citations={[courtCitation]}>
                    Mock analysis for human review. {t("noPrediction")}
                  </AiAnalysisBlock>
                </>
              ) : (
                <RecordBlock sourceType="court" citations={[courtCitation]}>
                  Generic source-backed content for this chain step.
                </RecordBlock>
              )}
            </section>
          ))}
        </div>
      </WorkspaceGrid>
    </AppShell>
  );
}

export function AppealScreen() {
  const t = useTranslations("phase5");
  const categories = [
    "Evidence Assessment",
    "Error of Law",
    "Error of Fact",
    "Reasoning",
    "Mode of Liability",
    "Procedural Fairness",
    "Sentencing",
    "Other",
  ];
  return (
    <AppShell footer={t("noPrediction")}>
      <ScreenHeader
        eyebrow={t("appealReview")}
        title={t("potentialIssues")}
        description={t("noPrediction")}
      />
      <WorkspaceGrid
        left={
          <Panel title={t("issueCategories")}>
            <ul className="space-y-2">
              {categories.map((category) => (
                <li key={category}>
                  <button className="text-accent text-[11px]">{category}</button>
                </li>
              ))}
            </ul>
          </Panel>
        }
        right={
          <Panel title={t("missingMaterial")}>
            <p className="text-fg-secondary text-[11px]">
              Generic public-record gap stated explicitly; nothing is inferred.
            </p>
          </Panel>
        }
      >
        <div className="space-y-3">
          <DemoNotice />
          {categories.slice(0, 3).map((category, index) => (
            <Panel
              key={category}
              label={category}
              title={`Illustrative issue ${index + 1}`}
              actions={<VerificationBadge state="unreviewed" />}
            >
              <div className="grid gap-3 md:grid-cols-2">
                <RecordBlock sourceType="court" citations={[courtCitation]}>
                  Generic court reasoning at issue.
                </RecordBlock>
                <RecordBlock sourceType="defence" citations={[courtCitation]}>
                  Generic Defence position.
                </RecordBlock>
                <RecordBlock sourceType="spo" citations={[courtCitation]}>
                  Generic SPO position.
                </RecordBlock>
                <AiAnalysisBlock citations={[courtCitation]}>
                  Potential issue for human review. {t("noPrediction")}
                </AiAnalysisBlock>
              </div>
              <div className="mt-3">
                <ActionLink href="/appeal/argument/new">{t("sendToLab")}</ActionLink>
              </div>
            </Panel>
          ))}
        </div>
      </WorkspaceGrid>
    </AppShell>
  );
}

export function ArgumentLabScreen({ id }: { id: string }) {
  const t = useTranslations("phase5");
  const [stage, setStage] = useState(1);
  const actions = [
    "researchSupport",
    "findContrary",
    "checkCitations",
    "findDefence",
    "findSpo",
    "findCourt",
  ] as const;
  const stages = [
    { title: t("defenceAnalyst"), source: "defence" as const },
    { title: t("spoRedTeam"), source: "spo" as const },
    { title: t("neutralReviewer"), source: "court" as const },
  ];
  return (
    <AppShell>
      <ScreenHeader eyebrow={id} title={t("argumentEditor")} description={t("mockNotice")} />
      <div className="mx-auto w-full max-w-[1440px] space-y-4 p-4">
        <DemoNotice />
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_292px]">
          <Panel title={t("argumentEditor")}>
            <textarea
              defaultValue="Generic sample research argument. [F01234 · ¶45–46]"
              className="border-border bg-bg text-fg rounded-control min-h-52 w-full border p-3 text-[12px]"
            />
            <p className="governance-text mt-2">
              The editor flags absence of citation only. It does not evaluate whether an argument is
              correct.
            </p>
          </Panel>
          <Panel title={t("actions")}>
            <div className="grid gap-2">
              {actions.map((key) => (
                <button
                  key={key}
                  className="border-border bg-surface-raised text-fg rounded-control border px-3 py-2 text-left text-[11px]"
                >
                  {t(key)}
                </button>
              ))}
            </div>
          </Panel>
        </div>
        <div className="flex gap-2">
          {stages.map((item, index) => (
            <button
              key={item.title}
              onClick={() => setStage(index + 1)}
              className={`rounded-control border px-3 py-2 text-[11px] ${stage === index + 1 ? "border-accent bg-surface-high" : "border-border bg-surface"}`}
            >
              {index + 1}. {item.title}
            </button>
          ))}
        </div>
        <div className="grid gap-3 lg:grid-cols-3">
          {stages.map((item, index) => (
            <RecordBlock
              key={item.title}
              sourceType={item.source}
              title={item.title}
              citations={[courtCitation]}
            >
              <p>Generic review output with a source citation.</p>
              {index === 2 ? (
                <ul className="mt-3 space-y-1 text-[10px]">
                  <li>{t("unsupported")}</li>
                  <li>{t("missingCitations")}</li>
                  <li>{t("ignoredEvidence")}</li>
                  <li>{t("unanswered")}</li>
                  <li>{t("factualDisputes")}</li>
                  <li>
                    {t("legalQuestions")} — {t("legalDecline")}
                  </li>
                  <li>{t("humanReview")}</li>
                </ul>
              ) : null}
            </RecordBlock>
          ))}
        </div>
      </div>
    </AppShell>
  );
}

export function AiResearchScreen() {
  const t = useTranslations("phase5");
  const footer = useTranslations("footer");
  const answer = mockRepository.getAnswer();
  const record = answer.filter((block) => block.kind !== "ai");
  const ai = answer.filter((block) => block.kind === "ai");
  return (
    <AppShell footer={footer("sourceNote")}>
      <ScreenHeader
        eyebrow={t("askAi")}
        title="How does the sample record address this research question?"
        description={t("mockNotice")}
        actions={
          <>
            <ActionLink href="/network">{t("viewEvidenceGraph")}</ActionLink>
            <ActionLink href="/appeal/argument/new">{t("createArgument")}</ActionLink>
          </>
        }
      />
      <WorkspaceGrid
        left={
          <Panel title={t("results")}>
            <p className="text-fg text-[11px]">Demo research session</p>
          </Panel>
        }
        right={
          <>
            <Panel title={t("sourcesUsed")}>
              <div className="space-y-2">
                <CitationChip citation={courtCitation} />
                <CitationChip citation={transcriptCitation} />
                <CitationChip citation={exhibitCitation} />
              </div>
            </Panel>
            <Panel className="mt-3" title={t("citationStatus")}>
              <VerificationBadge state="verified" />
              <p className="text-fg-muted mt-2 text-[10px]">3 / 3</p>
            </Panel>
          </>
        }
      >
        <div className="space-y-3">
          <DemoNotice />
          {record.map((block, index) => (
            <RecordBlock
              key={`${block.kind}-${index}`}
              sourceType={sourceForAnswer[block.kind as Exclude<AnswerBlockKind, "ai">]}
              title={block.kind}
              citations={block.citations}
              previewCitations
            >
              <p>{block.text}</p>
            </RecordBlock>
          ))}
          <ProvenanceBoundary />
          {ai.map((block, index) => (
            <AiAnalysisBlock
              key={index}
              title={t("neutralReview")}
              citations={block.citations}
              previewCitations
            >
              {block.text}
            </AiAnalysisBlock>
          ))}
          <div className="flex flex-wrap gap-2">
            <button className="border-border bg-surface-raised rounded-control border px-3 py-2 text-[11px]">
              {t("openAllSources")}
            </button>
            <button className="border-border bg-surface-raised rounded-control border px-3 py-2 text-[11px]">
              {t("saveNote")}
            </button>
          </div>
        </div>
      </WorkspaceGrid>
    </AppShell>
  );
}

export function PublicScreen() {
  const t = useTranslations("phase5");
  const footer = useTranslations("footer");
  const entries = [
    "whatDecided",
    "whoTestified",
    "whichEvidence",
    "whatHappened",
    "howConnected",
    "readSource",
  ] as const;
  return (
    <AppShell mode="light" footer={footer("sourceNote")}>
      <ScreenHeader
        eyebrow={t("beforeBegin")}
        title={t("simpleIntro")}
        description={t("mockNotice")}
      />
      <div className="mx-auto w-full max-w-6xl space-y-6 p-4 md:p-8">
        <Panel title={t("beforeBegin")}>
          <p className="text-fg-body text-[12px]">{t("simpleIntro")}</p>
        </Panel>
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {entries.map((key) => (
            <Link
              key={key}
              href={key === "readSource" ? "/documents/F01234" : "/public/demo"}
              className="border-border bg-surface hover:bg-surface-raised rounded-card border p-4"
            >
              <h2 className="text-fg text-[14px] font-semibold">{t(key)}</h2>
              <p className="text-fg-secondary mt-2 text-[11px]">
                Generic demo explanation with a route back to the source.
              </p>
            </Link>
          ))}
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <Panel title={t("plainLanguage")}>
            <p className="text-fg-body text-[13px]">
              A generic sample finding records a limited conclusion based on the cited public
              material.
            </p>
            <div className="mt-3">
              <CitationChip citation={courtCitation} />
            </div>
          </Panel>
          <RecordBlock sourceType="court" title={t("originalText")} citations={[courtCitation]}>
            <p className="font-serif">
              Generic demonstrative record wording shown beside, never replaced by, the explanation.
            </p>
          </RecordBlock>
        </div>
        <Panel title={t("doesNotMean")}>
          <ul className="space-y-2 text-[11px]">
            <li>— It does not create a conclusion about any real person.</li>
            <li>— It does not replace the cited record.</li>
            <li>— Other sample material may point in another direction.</li>
          </ul>
        </Panel>
      </div>
    </AppShell>
  );
}
