"use client";

import type { DateType } from "@ksc/shared";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useState } from "react";
import { DataTable, type Column } from "@/components/primitives/DataTable";
import { Panel } from "@/components/primitives/Panel";
import { GapNotice } from "@/components/primitives/States";
import {
  CitationChip,
  ProtectionNotice,
  RecordBlock,
  SourceBadge,
  VerificationBadge,
} from "@/components/provenance";
import { AppShell } from "@/components/shell/AppShell";
import { courtCitation, exhibitCitation, mockRepository, transcriptCitation } from "@/mock";
import { ActionLink, DemoNotice, TabStrip } from "./ScreenChrome";
import { HexAvatar, KeyValue, NoteStrip, SectionCard, StatStrip, ToolButton } from "./Workspace";

const PERSON_TABS = [
  "overview",
  "findings",
  "testimony",
  "documents",
  "exhibits",
  "incidents",
  "timeline",
  "network",
  "arguments",
  "research",
] as const;
const WITNESS_TABS = [
  "overview",
  "testimony",
  "cross",
  "prior",
  "exhibits",
  "findings",
  "incidents",
  "timeline",
  "network",
  "research",
] as const;

interface FindingRow {
  ref: string;
  title: string;
  paras: string;
  state: "verified" | "unreviewed";
  outcome: string;
}
const FINDINGS: readonly FindingRow[] = [
  {
    ref: "F-DEMO-01",
    title: "Illustrative finding",
    paras: "¶45–46",
    state: "verified",
    outcome: "Demo outcome wording",
  },
  {
    ref: "FD-DEMO-2002",
    title: "Demo record 02",
    paras: "¶120",
    state: "unreviewed",
    outcome: "Demo outcome wording",
  },
];

function TypedDates() {
  const t = useTranslations("phase5");
  const items = mockRepository.getTimeline();
  const labels: Record<DateType, string> = {
    event: t("event"),
    document: t("document"),
    filing: t("filing"),
    testimony: t("testimonyDate"),
    decision: t("decision"),
  };
  return (
    <ol className="space-y-1.5">
      {items.map((item) => (
        <li
          key={item.id}
          className="grid grid-cols-[110px_minmax(0,1fr)_auto] items-center gap-2 text-[11px]"
        >
          <span className="tabular text-fg-secondary">{item.date}</span>
          <Link href={item.href} className="text-fg min-w-0 truncate hover:underline">
            {item.label}
          </Link>
          <span className={`rounded-badge px-1.5 py-0.5 text-[10px] date-${item.dateType}`}>
            {labels[item.dateType]}
          </span>
        </li>
      ))}
    </ol>
  );
}

function NetworkPreview({ focus }: { focus: string }) {
  const tb = useTranslations("phase5b");
  const { nodes, edges } = mockRepository.getNetwork();
  return (
    <div>
      <svg
        viewBox="0 0 100 60"
        role="img"
        aria-label={tb("networkPreview")}
        className="bg-bg-graph rounded-card h-40 w-full"
      >
        {edges.map((e) => {
          const a = nodes.find((n) => n.id === e.from)!;
          const b = nodes.find((n) => n.id === e.to)!;
          return (
            <line
              key={e.id}
              x1={a.x}
              y1={a.y * 0.6}
              x2={b.x}
              y2={b.y * 0.6}
              stroke="var(--border)"
              strokeWidth="0.6"
            />
          );
        })}
        {nodes.map((n) => (
          <circle
            key={n.id}
            cx={n.x}
            cy={n.y * 0.6}
            r={n.id === focus ? 3.5 : 2.2}
            fill={n.id === focus ? "var(--accent)" : "var(--surface-high)"}
            stroke={n.type === "protected" ? "var(--witness)" : "var(--border)"}
            strokeDasharray={n.type === "protected" ? "1 1" : undefined}
            strokeWidth="0.5"
          />
        ))}
      </svg>
      <div className="mt-2">
        <ActionLink href={`/network?focus=${focus}`}>{tb("openInNetwork")}</ActionLink>
      </div>
    </div>
  );
}

export function PersonDossierScreen({ slug }: { slug: string }) {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const tRef = useTranslations("referenceCounts");
  const tFooter = useTranslations("footer");
  const person = mockRepository.getPerson(slug);
  const [tab, setTab] = useState<(typeof PERSON_TABS)[number]>("overview");
  const columns: readonly Column<FindingRow>[] = [
    {
      key: "ref",
      header: "ID",
      identifier: true,
      cell: (r) => (
        <Link href={`/findings/${r.ref}`} className="text-accent">
          {r.ref}
        </Link>
      ),
    },
    { key: "title", header: t("courtFindings"), minWidth: 180, cell: (r) => r.title },
    {
      key: "paras",
      header: tb("paragraphs"),
      cell: (r) => <span className="identifier">{r.paras}</span>,
    },
    { key: "outcome", header: tb("outcome"), minWidth: 160, cell: (r) => r.outcome },
    {
      key: "state",
      header: tb("verification"),
      cell: (r) => <VerificationBadge state={r.state} size="sm" />,
    },
  ];
  const stats = (
    [
      "documentMentions",
      "transcriptMentions",
      "exhibitRefs",
      "findings",
      "witnessesWhoReferred",
      "incidents",
      "citationsResolved",
    ] as const
  ).map((k) => ({
    key: k,
    label: tRef(k),
    value: person.counts[k],
    href: k === "findings" ? "/findings" : k === "incidents" ? "/incidents" : "/documents",
  }));
  return (
    <AppShell
      footer={tFooter("referenceCounts")}
      crumbs={[{ label: tb("people"), href: "/people" }, { label: person.displayName }]}
    >
      <header className="border-border-subtle bg-bg-deep border-b px-4 py-4">
        <div className="mx-auto flex w-full max-w-[1440px] flex-wrap items-start gap-4">
          <HexAvatar
            initials={person.displayName
              .split(" ")
              .map((w) => w[0])
              .join("")
              .slice(0, 2)}
          />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-fg text-[24px] leading-tight font-bold tracking-[-0.02em]">
                {person.displayName}
              </h1>
              <span className="rounded-badge bg-surface-raised text-fg-secondary px-1.5 py-0.5 text-[10px]">
                {tb("caseRole")}: {person.role}
              </span>
              <SourceBadge type="court" size="sm" />
            </div>
            <p className="text-fg-secondary mt-1 text-[11px]">
              {tb("publicRoles")}: {person.role} (2019–2024)
            </p>
            <p className="text-fg-muted mt-0.5 text-[11px]">
              {tb("aliases")}: {person.aliases.join(" · ")}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <ActionLink href={`/network?focus=${person.slug}`}>{t("viewNetwork")}</ActionLink>
            <ActionLink href={`/timeline?person=${person.slug}`}>{t("viewTimeline")}</ActionLink>
            <ActionLink href={`/network/path?from=${person.slug}`}>
              {t("findConnection")}
            </ActionLink>
            <ActionLink href={`/ai?q=${person.slug}`} primary>
              {t("askAi")}
            </ActionLink>
          </div>
        </div>
      </header>
      <div className="mx-auto w-full max-w-[1440px] px-3 pt-3 md:px-4">
        <StatStrip label={tb("recordReferences")} disclaimer={tRef("disclaimer")} items={stats} />
      </div>
      <TabStrip tabs={PERSON_TABS.map((k) => ({ key: k, label: tb(`tabs.${k}`) }))} active={tab} />
      <div className="sr-only">
        <div role="tablist">
          {PERSON_TABS.map((k) => (
            <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)}>
              {tb(`tabs.${k}`)}
            </button>
          ))}
        </div>
      </div>
      <div className="mx-auto grid w-full max-w-[1440px] min-w-0 flex-1 gap-3 p-3 md:p-4 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div className="min-w-0 space-y-3">
          <DemoNotice />
          <SectionCard
            id="summary"
            title={tb("citedSummary")}
            aside={<span className="text-fg-muted text-[10px]">{tb("everySentenceCited")}</span>}
          >
            <p className="text-fg-body font-serif text-[13px] leading-relaxed">
              The demo record refers to this entity in a filing{" "}
              <CitationChip citation={courtCitation} size="sm" /> and in an exhibit description{" "}
              <CitationChip citation={exhibitCitation} size="sm" />. A protected witness refers to
              the entity by role only <CitationChip citation={transcriptCitation} size="sm" />.
            </p>
          </SectionCard>
          <SectionCard
            id="findings"
            title={t("courtFindings")}
            aside={<ToolButton pressed>{tb("sortJudgmentOrder")}</ToolButton>}
          >
            <DataTable columns={columns} rows={FINDINGS} rowKey={(r) => r.ref} density="compact" />
          </SectionCard>
          <SectionCard id="dates" title={tb("typedDates")}>
            <TypedDates />
            <NoteStrip className="mt-3">{t("dateTypes")}</NoteStrip>
          </SectionCard>
          <SectionCard id="network" title={tb("networkPreview")}>
            <NetworkPreview focus={person.slug} />
          </SectionCard>
        </div>
        <aside className="min-w-0 space-y-3">
          <Panel title={tb("referenceBreakdown")}>
            <KeyValue
              rows={[
                { key: "j", label: "Judgment", value: 6 },
                { key: "s", label: t("spo"), value: 4 },
                { key: "d", label: t("defence"), value: 3 },
                { key: "t", label: t("testimony"), value: person.counts.transcriptMentions },
                { key: "e", label: t("exhibits"), value: person.counts.exhibitRefs },
              ]}
            />
          </Panel>
          <Panel title={tb("keyReferences")}>
            <ul className="space-y-2">
              {[courtCitation, exhibitCitation, transcriptCitation].map((c) => (
                <li key={c.display} className="flex flex-wrap items-center gap-2 text-[11px]">
                  <SourceBadge type={c.sourceType} size="sm" />
                  <CitationChip citation={c} size="sm" />
                </li>
              ))}
            </ul>
          </Panel>
          <NoteStrip tone="legal">{tb("noScore")}</NoteStrip>
        </aside>
      </div>
    </AppShell>
  );
}

const CHRONOLOGY = [
  { id: "s1", kind: "direct", date: "2024-05-14", pages: "T. 12–24", examiner: "SPO", held: true },
  {
    id: "s2",
    kind: "cross",
    date: "2024-05-14",
    pages: "T. 25–31",
    examiner: "Defence",
    held: true,
  },
  { id: "s3", kind: "closed", date: "2024-05-15", pages: "T. 32–40", examiner: "—", held: false },
  {
    id: "s4",
    kind: "redirect",
    date: "2024-05-15",
    pages: "T. 41–44",
    examiner: "SPO",
    held: true,
  },
] as const;

export function WitnessDossierScreen({ code }: { code: string }) {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const tRef = useTranslations("referenceCounts");
  const witness = mockRepository.getWitness(code);
  const [tab, setTab] = useState<(typeof WITNESS_TABS)[number]>("testimony");
  const [segment, setSegment] = useState<string>("s1");
  const current = CHRONOLOGY.find((c) => c.id === segment)!;
  const stats = [
    { key: "sessions", value: 2 },
    { key: "transcriptPages", value: 33 },
    { key: "exhibitsShown", value: 3 },
    { key: "findingsCiting", value: 2 },
    { key: "incidents", value: 1 },
    { key: "priorStatements", value: 0 },
    { key: "closedPages", value: 9 },
  ].map((s) => ({ ...s, label: tb(`witnessStats.${s.key}`) }));
  return (
    <AppShell crumbs={[{ label: tb("witnesses"), href: "/witnesses" }, { label: witness.code }]}>
      <div className="border-border-subtle bg-bg-deep border-b px-4 py-4">
        <div className="mx-auto grid w-full max-w-[1440px] gap-3 lg:grid-cols-2">
          <section
            aria-label={tb("headerProtected")}
            className={`rounded-card border p-3 ${witness.protected ? "border-witness" : "border-border-subtle opacity-70"}`}
          >
            <p className="section-label mb-2">{tb("headerProtected")}</p>
            <div className="flex items-start gap-3">
              <HexAvatar initials="W" dashed />
              <div className="min-w-0 flex-1">
                <h1 className="identifier text-fg text-[22px] font-bold">{witness.code}</h1>
                <p className="text-fg-secondary text-[11px]">
                  {t("protectedOnly")} · {witness.protectiveMeasures.join(" · ") || "—"}
                </p>
              </div>
            </div>
            <div className="mt-3">
              <ProtectionNotice />
            </div>
          </section>
          <section
            aria-label={tb("headerPublic")}
            className={`rounded-card border p-3 ${witness.protected ? "border-border-subtle border-dashed opacity-70" : "border-accent"}`}
          >
            <p className="section-label mb-2">{tb("headerPublic")}</p>
            {witness.protected ? (
              <KeyValue
                rows={[
                  { key: "n", label: "displayName", value: "—" },
                  { key: "o", label: tb("statedOccupation"), value: "—" },
                  { key: "c", label: tb("calledBy"), value: "—" },
                ]}
              />
            ) : (
              <div className="flex items-start gap-3">
                <HexAvatar initials={witness.public.displayName[0] ?? "W"} />
                <div>
                  <h1 className="text-fg text-[22px] font-bold">{witness.public.displayName}</h1>
                  <p className="text-fg-secondary text-[11px]">
                    {witness.code} · {tb("calledBy")}: {witness.public.calledBy.toUpperCase()}
                    {witness.public.statedOccupation
                      ? ` · ${tb("statedOccupation")}: ${witness.public.statedOccupation}`
                      : ""}
                  </p>
                </div>
              </div>
            )}
            <p className="text-fg-muted mt-3 text-[10px]">{tb("publicWitnessNote")}</p>
          </section>
        </div>
        <div className="mx-auto mt-3 flex w-full max-w-[1440px] flex-wrap items-start gap-3">
          <div className="min-w-0 flex-1">
            <StatStrip items={stats} label={tRef("title")} disclaimer={tRef("disclaimer")} />
          </div>
          <div className="flex gap-2">
            <ActionLink href={`/witnesses/${witness.code}/compare`}>
              {t("statementComparison")}
            </ActionLink>
            <ActionLink href={`/ai?q=${witness.code}`} primary>
              {t("askAi")}
            </ActionLink>
          </div>
        </div>
      </div>
      <TabStrip tabs={WITNESS_TABS.map((k) => ({ key: k, label: tb(`tabs.${k}`) }))} active={tab} />
      <div className="sr-only">
        <div role="tablist">
          {WITNESS_TABS.map((k) => (
            <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)}>
              {tb(`tabs.${k}`)}
            </button>
          ))}
        </div>
      </div>
      <div className="mx-auto grid w-full max-w-[1440px] min-w-0 flex-1 gap-3 p-3 md:p-4 lg:grid-cols-[228px_minmax(0,1fr)] xl:grid-cols-[228px_minmax(0,1fr)_286px]">
        <aside className="min-w-0">
          <Panel title={tb("chronology")}>
            <label className="lg:hidden">
              <span className="sr-only">{tb("chronology")}</span>
              <select
                value={segment}
                onChange={(e) => setSegment(e.target.value)}
                className="border-border bg-surface-raised rounded-control h-8 w-full border px-2 text-[11px]"
              >
                {CHRONOLOGY.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.pages} · {c.kind}
                  </option>
                ))}
              </select>
            </label>
            <ol className="hidden space-y-1 lg:block">
              {CHRONOLOGY.map((c) => (
                <li key={c.id}>
                  <button
                    type="button"
                    onClick={() => setSegment(c.id)}
                    aria-current={segment === c.id ? "true" : undefined}
                    className={`rounded-control w-full px-2 py-1.5 text-left text-[11px] ${segment === c.id ? "bg-surface-high text-fg" : "text-fg-secondary"} ${c.kind === "closed" ? "border-border border border-dashed" : ""}`}
                  >
                    <span className="tabular block text-[10px]">
                      {c.date} · {c.pages}
                    </span>
                    <span>
                      {c.kind === "closed"
                        ? tb("closedSession")
                        : `${c.kind} · ${tb("examiner")}: ${c.examiner}`}
                    </span>
                  </button>
                </li>
              ))}
            </ol>
          </Panel>
        </aside>
        <div className="min-w-0 space-y-3">
          <DemoNotice />
          <SectionCard
            id="testimony"
            title={tb("testimonyReader")}
            aside={<span className="identifier text-fg-muted text-[10px]">{current.pages}</span>}
          >
            {current.held ? (
              <RecordBlock sourceType="witness" title={`${witness.code} · ${current.kind}`}>
                <p className="font-serif">
                  <strong className="font-sans text-[10px]">Q</strong> Generic demo question put in{" "}
                  {current.kind} examination.
                </p>
                <p className="mt-2 font-serif">
                  <strong className="font-sans text-[10px]">A</strong> Generic demo answer; wording
                  carries no identity attribute.
                </p>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <CitationChip citation={transcriptCitation} />
                  <span className="rounded-badge bg-surface-raised text-fg-secondary px-1.5 py-0.5 text-[10px]">
                    {tb("exhibitShown")}: P00123
                  </span>
                  <span className="rounded-badge bg-surface-raised text-fg-secondary px-1.5 py-0.5 text-[10px]">
                    {tb("citedInFindings")}: F-DEMO-01
                  </span>
                  <VerificationBadge state="verified" size="sm" />
                  <Link
                    href={`/witnesses/${witness.code}/compare`}
                    className="text-accent text-[10px] font-semibold"
                  >
                    {tb("flagForComparison")} →
                  </Link>
                </div>
              </RecordBlock>
            ) : (
              <GapNotice
                kind="closed-session"
                reference={current.pages}
                extent="9 pages"
                reason={tb("closedSession")}
              />
            )}
          </SectionCard>
          <SectionCard id="exhibits" title={t("exhibits")}>
            <ul className="flex flex-wrap gap-2">
              <li>
                <Link
                  href="/documents/P00123?page=4"
                  className="identifier text-accent text-[11px]"
                >
                  P00123
                </Link>
              </li>
            </ul>
          </SectionCard>
          <SectionCard id="timeline" title={tb("tabs.timeline")}>
            <TypedDates />
          </SectionCard>
          <SectionCard id="network" title={tb("tabs.network")}>
            <NetworkPreview focus={witness.code} />
          </SectionCard>
        </div>
        <aside className="min-w-0 space-y-3 lg:col-span-2 xl:col-span-1">
          <Panel title={t("courtFindings")}>
            <ul className="space-y-1 text-[11px]">
              <li>
                <Link href="/findings/F-DEMO-01" className="text-accent">
                  F-DEMO-01
                </Link>{" "}
                · {tb("citedInFindings")}
              </li>
            </ul>
          </Panel>
          <Panel title={t("priorStatements")}>
            <p className="text-fg-secondary text-[11px]">{tb("noPriorStatement")}</p>
          </Panel>
          <Panel title={tb("comparisonStatus")}>
            <KeyValue
              rows={[
                { key: "t", label: t("results"), value: 3 },
                { key: "c", label: t("consistent"), value: 1 },
                { key: "p", label: t("possibleContradiction"), value: 1 },
                { key: "n", label: t("notComparable"), value: 1 },
              ]}
            />
            <div className="mt-2">
              <ActionLink href={`/witnesses/${witness.code}/compare`}>
                {t("statementComparison")}
              </ActionLink>
            </div>
          </Panel>
          <NoteStrip>{t("comparisonNeutral")}</NoteStrip>
        </aside>
      </div>
    </AppShell>
  );
}

export function ProtectedWitnessHeader({ code }: { code: string }) {
  return <span className="identifier">{code}</span>;
}
