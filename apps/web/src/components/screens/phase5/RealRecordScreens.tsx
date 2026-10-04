import { useTranslations } from "next-intl";
import Link from "next/link";
import { EmptyState } from "@/components/primitives/States";
import { Panel } from "@/components/primitives/Panel";
import {
  CitationChip,
  EvidenceBasis,
  IntelligenceStateLabel,
  ProtectionNotice,
  ProvenanceSource,
  SourceBadge,
  VerificationBadge,
  GroupedSourceList,
} from "@/components/provenance";
import { AppShell } from "@/components/shell/AppShell";
import type {
  EntityMention,
  EntityMentionsView,
  ExhibitDossier,
  ExhibitStatusEventView,
  IncidentView,
  NetworkView,
  OrganizationDossier,
  PersonDossier,
  SearchResult,
  WitnessAppearanceView,
  WitnessDossier,
} from "@/data";
import type { DirectoryKind, DirectoryRow } from "@/data";
import { groupBySource, versionHref, type SourceGroup } from "@/lib/source-groups";
import { documentHref } from "@/lib/document-route";
import { ActionLink, ScreenHeader, TabStrip } from "./ScreenChrome";
import { HexAvatar, KeyValue, NoteStrip, SectionCard, StatStrip } from "./Workspace";

const countKeys = [
  "documentMentions",
  "transcriptMentions",
  "exhibitRefs",
  "findings",
  "witnessesWhoReferred",
  "incidents",
  "citationsResolved",
] as const;

const NO_MENTIONS: EntityMentionsView = { total: 0, items: [] };
// Relationship groups shown inline; every relationship stays one click away
// in the focused Network view, which pages through all of them.
const MAX_EDGE_GROUPS = 8;

export function RealPersonScreen({
  person,
  occurrences = [],
  mentions = NO_MENTIONS,
  network = { nodes: [], edges: [] },
  appearances = [],
}: {
  person: PersonDossier;
  occurrences?: readonly SearchResult[];
  mentions?: EntityMentionsView;
  network?: NetworkView;
  appearances?: readonly WitnessAppearanceView[];
}) {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const tr = useTranslations("referenceCounts");
  const tp = useTranslations("personDossier");
  const tg = useTranslations("sourceGroups");
  const name = encodeURIComponent(person.displayName);
  const slug = encodeURIComponent(person.slug);
  const counts = person.counts;
  const verified = groupMentions(
    mentions.items.filter((mention) => mention.matchClass === "VERIFIED_MENTION"),
  );
  // The versions that mention this person most, among the mentions loaded
  // here — a count of occurrences, never a ranking of importance.
  const keyReferences = [...verified]
    .sort((a, b) => b.items.length - a.items.length || a.versionRef.localeCompare(b.versionRef))
    .slice(0, 5);
  const rare = counts.documentMentions + counts.transcriptMentions <= 3;
  const stats = countKeys.map((key) => ({
    key,
    label: tr(key),
    value: counts[key],
    href:
      key === "findings"
        ? "/findings"
        : key === "incidents"
          ? "/incidents"
          : key === "witnessesWhoReferred"
            ? "/witnesses"
            : key === "exhibitRefs"
              ? "/exhibits"
              : `/search?q=${name}`,
  }));
  return (
    <AppShell crumbs={[{ label: tb("people"), href: "/people" }, { label: person.displayName }]}>
      <header className="border-border-subtle bg-bg-deep border-b px-4 py-4">
        <div className="mx-auto flex w-full max-w-[1440px] flex-wrap items-start gap-4">
          <HexAvatar initials={initialsOf(person.displayName)} />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-fg text-[24px] leading-tight font-bold tracking-[-0.02em]">
                {person.displayName}
              </h1>
              {person.role ? (
                <span className="rounded-badge border-accent/40 text-accent border px-1.5 py-0.5 text-[10px] font-semibold uppercase">
                  {roleLabel(tp, person.role)}
                </span>
              ) : null}
            </div>
            <p className="text-fg-secondary mt-1 text-[11px]">{tp("recordedIn")}</p>
            {person.aliases.length ? (
              <div className="mt-2 flex flex-wrap items-center gap-1.5">
                <span className="text-fg-muted text-[10px]">{tp("alsoRecordedAs")}</span>
                {person.aliases.map((alias) => (
                  <span
                    key={alias}
                    className="rounded-chip border-border bg-surface-raised text-fg-secondary border px-2 py-0.5 text-[10px]"
                  >
                    {alias}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
          <div className="flex flex-wrap gap-2">
            <ActionLink href={`/network?focus=${slug}`}>{t("viewNetwork")}</ActionLink>
            <ActionLink href={`/timeline?person=${slug}`}>{t("viewTimeline")}</ActionLink>
            <ActionLink href={`/network/path?from=${slug}`}>{t("findConnection")}</ActionLink>
            <ActionLink href={`/ai?q=${name}`} primary>
              {t("askAi")}
            </ActionLink>
          </div>
        </div>
      </header>
      <div className="mx-auto w-full max-w-[1440px] px-3 pt-3 md:px-4">
        <StatStrip label={tb("recordReferences")} disclaimer={tr("disclaimer")} items={stats} />
      </div>
      <TabStrip
        tabs={(["overview", "documents", "testimony", "findings", "network"] as const).map(
          (key) => ({ key, label: tb(`tabs.${key}`), href: `#${key}` }),
        )}
        active="overview"
      />
      <div
        id="overview"
        className="mx-auto grid w-full max-w-[1440px] min-w-0 flex-1 gap-3 p-3 md:p-4 lg:grid-cols-[minmax(0,1fr)_300px]"
      >
        <div className="min-w-0 space-y-3">
          {rare ? <NoteStrip>{tp("appearsRarely")}</NoteStrip> : null}
          <SectionCard
            id="documents"
            title={tp("verifiedMentions")}
            aside={
              <span className="text-fg-muted text-[10px]">
                {tg("documents", { documents: verified.length, occurrences: countItems(verified) })}
                {mentions.total > mentions.items.length
                  ? ` · ${tp("loadedOf", { shown: mentions.items.length, total: mentions.total })}`
                  : ""}
              </span>
            }
          >
            {verified.length ? (
              <MentionList
                groups={verified}
                countLabel={(n) => tg("verifiedCount", { count: n })}
              />
            ) : (
              <p className="text-fg-muted text-[11px]">{tp("noVerifiedMentions")}</p>
            )}
          </SectionCard>
          <SectionCard
            id="findings"
            title={t("courtFindings")}
            aside={<span className="text-fg-muted text-[10px]">{tp("judgmentOrder")}</span>}
          >
            <p className="text-fg-secondary text-[11px]">
              {counts.findings
                ? tp("findingsLinked", { count: counts.findings })
                : tp("noFindings")}
            </p>
            {counts.findings ? (
              <div className="mt-2">
                <ActionLink href="/findings">{tp("openFindings")}</ActionLink>
              </div>
            ) : null}
          </SectionCard>
          <SectionCard id="testimony" title={tb("typedDates")}>
            {appearances.length ? (
              <ol className="space-y-1.5">
                {[...appearances]
                  .sort((a, b) => a.hearingDate.localeCompare(b.hearingDate))
                  .map((row) => (
                    <li
                      key={`${row.versionRef}-${row.pageFrom ?? 0}`}
                      className="grid grid-cols-[96px_minmax(0,1fr)_auto] items-center gap-2 text-[11px]"
                    >
                      <span className="tabular text-fg-secondary">{row.hearingDate}</span>
                      <span className="text-fg min-w-0 truncate">
                        {row.sessionLabel ?? row.versionRef}
                      </span>
                      <span className="rounded-badge date-testimony px-1.5 py-0.5 text-[10px]">
                        {t("testimonyDate")}
                      </span>
                    </li>
                  ))}
              </ol>
            ) : (
              <p className="text-fg-muted text-[11px]">{tp("noDates")}</p>
            )}
            <NoteStrip className="mt-3">{t("dateTypes")}</NoteStrip>
          </SectionCard>
          <ResearchTrail
            entityRef={person.slug}
            occurrences={occurrences}
            mentions={{
              total: mentions.total,
              items: mentions.items.filter((m) => m.matchClass === "REVIEW_REQUIRED"),
            }}
            network={network}
          />
        </div>
        <aside id="network" className="min-w-0 space-y-3">
          <Panel title={tb("networkPreview")}>
            <NetworkPreviewReal focusRef={person.slug} network={network} />
            <div className="mt-2">
              <ActionLink href={`/network?focus=${slug}`}>{tb("openInNetwork")}</ActionLink>
            </div>
          </Panel>
          <Panel title={tb("referenceBreakdown")}>
            <KeyValue
              rows={[
                { key: "d", label: tr("documentMentions"), value: counts.documentMentions },
                { key: "t", label: tr("transcriptMentions"), value: counts.transcriptMentions },
                { key: "e", label: tr("exhibitRefs"), value: counts.exhibitRefs },
                { key: "c", label: tr("citationsResolved"), value: counts.citationsResolved },
                {
                  key: "r",
                  label: tp("relationships"),
                  value: person.relationshipCount ?? 0,
                },
              ]}
            />
          </Panel>
          <Panel title={tb("keyReferences")}>
            {keyReferences.length ? (
              <ul className="space-y-2">
                {keyReferences.map((group) => (
                  <li
                    key={group.key}
                    className="border-border-subtle rounded-card border p-2 text-[11px]"
                  >
                    <Link
                      href={group.documentHref}
                      className="text-fg line-clamp-3 block font-medium hover:underline"
                    >
                      {group.title}
                    </Link>
                    <span className="identifier text-fg-tertiary mt-1 block text-[10px] break-all">
                      {group.versionRef}
                    </span>
                    <span className="text-fg-secondary mt-0.5 block text-[10px]">
                      {tg("verifiedCount", { count: group.items.length })}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-fg-muted text-[11px]">—</p>
            )}
            <p className="text-fg-muted mt-2 text-[10px]">{tp("keyReferencesNote")}</p>
          </Panel>
          <NoteStrip tone="legal">{tb("noScore")}</NoteStrip>
        </aside>
      </div>
    </AppShell>
  );
}

function initialsOf(name: string): string {
  const words = name.split(/\s+/u).filter((word) => /^\p{L}/u.test(word));
  return (
    words.length > 1 ? `${words[0]![0]}${words[words.length - 1]![0]}` : name.slice(0, 2)
  ).toUpperCase();
}

function roleLabel(tp: (key: string) => string, role: string): string {
  const known = ["accused", "witness", "counsel_or_participant", "judge", "victim"];
  return known.includes(role) ? tp(`roles.${role}`) : role.replaceAll("_", " ");
}

/** Depth-1 neighbourhood of the focus, laid out on a circle — the edges are
 * the record's own relationships, drawn without weight or ranking. */
function NetworkPreviewReal({ focusRef, network }: { focusRef: string; network: NetworkView }) {
  const tb = useTranslations("phase5b");
  const focus = network.nodes.find((node) => node.ref === focusRef);
  if (!focus) return <p className="text-fg-muted text-[11px]">—</p>;
  const neighbourIds = [
    ...new Set(
      network.edges
        .filter((edge) => edge.from === focus.id || edge.to === focus.id)
        .map((edge) => (edge.from === focus.id ? edge.to : edge.from)),
    ),
  ].slice(0, 8);
  const neighbours = neighbourIds
    .map((id) => network.nodes.find((node) => node.id === id))
    .filter((node): node is NonNullable<typeof node> => Boolean(node));
  const point = (index: number) => {
    const angle = (index / Math.max(1, neighbours.length)) * Math.PI * 2 - Math.PI / 2;
    return { x: 50 + Math.cos(angle) * 36, y: 32 + Math.sin(angle) * 22 };
  };
  const graph = (
    <svg
      viewBox="0 0 100 64"
      role="img"
      aria-label={tb("networkPreview")}
      className="bg-bg-graph rounded-card h-40 w-full"
    >
      {neighbours.map((node, index) => {
        const p = point(index);
        return (
          <line
            key={`l-${node.id}`}
            x1={50}
            y1={32}
            x2={p.x}
            y2={p.y}
            stroke="var(--border)"
            strokeWidth="0.5"
          />
        );
      })}
      {neighbours.map((node, index) => {
        return (
          <circle
            key={node.id}
            cx={point(index).x}
            cy={point(index).y}
            r={2.4}
            fill="var(--surface-high)"
            stroke="var(--border)"
            strokeWidth="0.5"
          />
        );
      })}
      <circle cx={50} cy={32} r={4} fill="var(--accent)" />
    </svg>
  );
  return (
    <div>
      {graph}
      <ul className="mt-2 space-y-0.5 text-[10px]">
        {neighbours.map((node) => (
          <li key={node.id} className="text-fg-secondary truncate" title={node.label}>
            {node.label}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function RealWitnessScreen({
  dossier,
  occurrences = [],
  mentions = NO_MENTIONS,
  network = { nodes: [], edges: [] },
  appearances = [],
}: {
  dossier: WitnessDossier;
  occurrences?: readonly SearchResult[];
  mentions?: EntityMentionsView;
  network?: NetworkView;
  appearances?: readonly WitnessAppearanceView[];
}) {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const t15 = useTranslations("phase15");
  const t18 = useTranslations("phase18");
  const tr = useTranslations("referenceCounts");
  const { witness, counts } = dossier;
  const title = witness.protected ? witness.code : witness.public.displayName;
  return (
    <AppShell crumbs={[{ label: tb("witnesses"), href: "/witnesses" }, { label: witness.code }]}>
      <ScreenHeader
        realData
        eyebrow={t15("verifiedPublicRecord")}
        title={title}
        description={witness.protected ? t15("protectedWitnessBoundary") : t15("sourceBacked")}
        actions={<SourceBadge type="witness" />}
      />
      <div className="mx-auto w-full max-w-[1440px] space-y-3 p-3 md:p-4">
        <StatStrip
          label={t15("referenceCounts")}
          disclaimer={tr("disclaimer")}
          items={countKeys.map((key) => ({ key, label: tr(key), value: counts[key] }))}
        />
        <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_340px]">
          <div className="space-y-3">
            <Panel title={t18("recordActivity")}>
              <div className="grid gap-2 lg:grid-cols-2">
                <RecordActivity
                  href={`/search?q=${encodeURIComponent(witness.code)}`}
                  label={t18("openTranscripts")}
                  value={counts.transcriptMentions}
                />
                <RecordActivity
                  href={`/search?q=${encodeURIComponent(witness.code)}`}
                  label={t18("openDocuments")}
                  value={counts.documentMentions}
                />
                <RecordActivity
                  href={`/timeline?q=${encodeURIComponent(witness.code)}`}
                  label={t18("openTimeline")}
                  value={counts.incidents}
                />
                <RecordActivity
                  href={`/network?focus=${encodeURIComponent(witness.code)}`}
                  label={t18("openRelationships")}
                  value={dossier.relationshipCount}
                />
              </div>
            </Panel>
            {appearances.length ? null : <NoteStrip>{t18("hearingsUnavailable")}</NoteStrip>}
            <Panel title={t18("sourceNavigation")}>
              <p className="text-fg-secondary text-[11px] leading-relaxed">
                {t18("sourceNavigationHint")}
              </p>
              <div className="mt-3">
                <ActionLink href={`/witnesses/${encodeURIComponent(witness.code)}/compare`}>
                  {t("statementComparison")}
                </ActionLink>
              </div>
            </Panel>
          </div>
          <div className="space-y-3">
            <Panel title={t("metadata")}>
              <KeyValue
                rows={[
                  { key: "code", label: t15("witnessCode"), value: witness.code },
                  {
                    key: "protected",
                    label: t("protectedOnly"),
                    value: witness.protected ? t15("yes") : t15("no"),
                  },
                  {
                    key: "measures",
                    label: t15("protectiveMeasures"),
                    value: witness.protectiveMeasures.join(" · ") || "—",
                  },
                  ...(!witness.protected
                    ? [
                        {
                          key: "called",
                          label: tb("calledBy"),
                          value: witness.public.calledBy.toUpperCase(),
                        },
                      ]
                    : []),
                ]}
              />
            </Panel>
            {witness.protected ? <ProtectionNotice /> : null}
          </div>
        </div>
        {appearances.length ? <AppearancesPanel appearances={appearances} /> : null}
        <ResearchTrail
          entityRef={witness.code}
          occurrences={occurrences}
          mentions={mentions}
          network={network}
        />
      </div>
    </AppShell>
  );
}

function groupMentions(mentions: readonly EntityMention[]): SourceGroup<EntityMention>[] {
  return groupBySource(mentions, (mention) => ({
    versionRef: mention.citation.ref,
    title: mention.documentTitle,
    documentHref: versionHref(mention.href),
    page: mention.citation.page,
  }));
}

function countItems(groups: readonly SourceGroup<unknown>[]): number {
  return groups.reduce((sum, group) => sum + group.items.length, 0);
}

function MentionList({
  groups,
  countLabel,
}: {
  groups: readonly SourceGroup<EntityMention>[];
  countLabel: (count: number) => string;
}) {
  const t18 = useTranslations("phase18");
  const t19 = useTranslations("phase19");
  return (
    <GroupedSourceList
      groups={groups}
      countLabel={countLabel}
      itemKey={(mention) => mention.id}
      renderItem={(mention) => (
        <>
          <p className="text-fg font-mono text-[11px] break-words">{mention.occurrenceText}</p>
          <div className="mt-1.5 flex flex-wrap items-center gap-2">
            <span className="text-fg-secondary font-mono text-[10px] font-semibold">
              {t19(`matchClass.${mention.matchClass}`)}
            </span>
            <CitationChip citation={mention.citation} size="sm" />
            <span className="text-fg-tertiary font-mono text-[10px]">{mention.ruleId}</span>
            {mention.versionSuperseded ? (
              <span className="text-fg-tertiary text-[10px]">{t19("supersededVersion")}</span>
            ) : null}
            <ActionLink href={mention.href}>{t18("openExactSource")}</ActionLink>
          </div>
        </>
      )}
    />
  );
}

/** Hearings with a recorded public appearance — stored rows only, never estimated. */
function AppearancesPanel({ appearances }: { appearances: readonly WitnessAppearanceView[] }) {
  const t19 = useTranslations("phase19");
  const hearings = new Set(appearances.map((row) => row.hearingDate)).size;
  return (
    <Panel title={t19("appearances.title")}>
      <p className="text-fg-secondary mb-2 text-[11px] leading-relaxed">
        {t19("appearances.summary", { hearings, rows: appearances.length })}
      </p>
      <p className="text-fg-tertiary mb-2 text-[10px] leading-relaxed">
        {t19("appearances.basis")}
      </p>
      <ul className="divide-border-faint divide-y">
        {appearances.map((row, index) => (
          <li key={`${row.versionRef}-${index}`} className="space-y-1.5 py-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="identifier text-fg text-[11px] font-semibold">
                {row.hearingDate}
              </span>
              <span className="text-fg-secondary font-mono text-[10px]">{row.versionRef}</span>
              <IntelligenceStateLabel state="VERIFIED" />
            </div>
            <p className="text-fg-secondary text-[11px]">
              {t19("appearances.pages", {
                from: row.pageFrom ?? "—",
                to: row.pageTo ?? "—",
                header: row.headerPages,
              })}{" "}
              ·{" "}
              {t19("appearances.sessions", {
                open: row.openSessionPages,
                private: row.privateSessionPages,
                closed: row.closedSessionPages,
              })}
            </p>
            {row.examinations.length ? (
              <ul className="text-fg-secondary space-y-0.5 text-[11px]">
                {row.examinations.map((exam) => (
                  <li key={`${exam.page ?? "x"}-${exam.text}`}>
                    <span className="font-mono text-[10px]">{exam.page ?? "—"}</span> · {exam.text}
                  </li>
                ))}
              </ul>
            ) : null}
            <ProvenanceSource provenance={row.provenance} />
          </li>
        ))}
      </ul>
    </Panel>
  );
}

/** Exhibit status history: explicit court-record statements only. */
function StatusHistoryPanel({
  events,
  status,
}: {
  events: readonly ExhibitStatusEventView[];
  status: string;
}) {
  const t19 = useTranslations("phase19");
  return (
    <Panel title={t19("statusHistory.title")}>
      <p className="text-fg-tertiary mb-2 text-[10px] leading-relaxed">
        {t19("statusHistory.basis")}
      </p>
      {events.length ? (
        <ul className="divide-border-faint divide-y">
          {events.map((event, index) => (
            <li
              key={`${event.provenance.versionRef}-${event.eventType}-${index}`}
              className="space-y-1.5 py-2"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-fg text-[11px] font-semibold">
                  {t19(`statusHistory.event.${event.eventType}`)}
                </span>
                <span className="identifier text-fg-secondary text-[10px]">{event.identifier}</span>
                {event.classification ? (
                  <span className="text-fg-secondary text-[10px]">{event.classification}</span>
                ) : null}
                <span className="text-fg-tertiary font-mono text-[10px]">
                  {t19("statusHistory.statementDate", { date: event.statementDate ?? "—" })}
                </span>
                {event.speaker ? (
                  <span className="text-fg-tertiary text-[10px]">{event.speaker}</span>
                ) : null}
              </div>
              <ProvenanceSource provenance={event.provenance} />
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-fg-secondary flex flex-wrap items-center gap-2 text-[11px]">
          {status.toLowerCase() === "unknown" ? <IntelligenceStateLabel state="UNKNOWN" /> : null}
          {t19("statusHistory.none")}
        </p>
      )}
    </Panel>
  );
}

function ResearchTrail({
  entityRef,
  occurrences,
  mentions,
  network,
}: {
  entityRef: string;
  occurrences: readonly SearchResult[];
  mentions: EntityMentionsView;
  network: NetworkView;
}) {
  const t = useTranslations("phase5");
  const t18 = useTranslations("phase18");
  const t19 = useTranslations("phase19");
  const tg = useTranslations("sourceGroups");
  // Every loaded occurrence stays reachable; repeated rows from one version
  // collapse into one group. Verified and review-required never share a group.
  const verified = groupMentions(
    mentions.items.filter((mention) => mention.matchClass === "VERIFIED_MENTION"),
  );
  const reviewRequired = groupMentions(
    mentions.items.filter((mention) => mention.matchClass === "REVIEW_REQUIRED"),
  );
  const sources = occurrences.filter(
    (row, index, all) =>
      (row.category === "documents" || row.category === "transcripts") &&
      // Only coordinate-bearing hits are exact occurrences; title-only matches stay in Search.
      (row.citation?.page !== undefined ||
        row.citation?.paraFrom !== undefined ||
        row.citation?.lineFrom !== undefined) &&
      all.findIndex((candidate) => candidate.href === row.href) === index,
  );
  const sourceGroups = groupBySource(sources, (row) => ({
    versionRef: row.citation?.ref ?? row.href,
    title: row.title,
    documentHref: versionHref(row.href),
    page: row.citation?.page,
  }));
  const focusNode = network.nodes.find((node) => node.ref === entityRef);
  const edges = focusNode
    ? network.edges.filter((edge) => edge.from === focusNode.id || edge.to === focusNode.id)
    : [];
  const nodeLabel = (id: string) => network.nodes.find((node) => node.id === id)?.label ?? "—";
  // The same relation to the same record, evidenced several times in one
  // version (e.g. cited on p.236 and p.454), is one row with its occurrences.
  const edgeGroups = groupBySource(edges, (edge) => {
    const other = edge.from === focusNode?.id ? edge.to : edge.from;
    const versionRef = edge.provenance?.versionRef ?? edge.citation.ref;
    return {
      key: [edge.relation, other, versionRef, edge.verification].join("|"),
      versionRef,
      title: `${edge.relation.replaceAll("_", " ")} · ${nodeLabel(other)}`,
      documentHref: versionHref(edge.sourcePath ?? documentHref(edge.citation.docId)),
      page: edge.provenance?.page ?? edge.citation.page,
    };
  });
  if (!mentions.items.length && !sources.length && !edges.length) return null;
  return (
    <div className="space-y-3">
      {mentions.items.length ? (
        <div className="grid gap-3 lg:grid-cols-2">
          {verified.length ? (
            <Panel title={t19("verifiedMentions")}>
              <p className="text-fg-tertiary mb-2 text-[10px]">
                {tg("documents", {
                  documents: verified.length,
                  occurrences: countItems(verified),
                })}
                {mentions.total > mentions.items.length
                  ? ` · ${t19("mentionTotal", { shown: mentions.items.length, total: mentions.total })}`
                  : ""}
              </p>
              <MentionList
                groups={verified}
                countLabel={(n) => tg("verifiedCount", { count: n })}
              />
            </Panel>
          ) : null}
          {reviewRequired.length ? (
            <Panel title={t19("reviewRequiredMentions")}>
              <p className="text-fg-secondary mb-2 text-[11px] leading-relaxed">
                {t19("reviewRequiredNote")}
              </p>
              <MentionList
                groups={reviewRequired}
                countLabel={(n) => tg("reviewCount", { count: n })}
              />
            </Panel>
          ) : null}
        </div>
      ) : null}
      <div className="grid gap-3 lg:grid-cols-2">
        {sources.length ? (
          <Panel title={t19("searchMatches")}>
            <p className="text-fg-secondary mb-2 text-[11px] leading-relaxed">
              {t19("searchMatchesNote")}
            </p>
            <GroupedSourceList
              groups={sourceGroups}
              countLabel={(n) => tg("matchCount", { count: n })}
              itemKey={(row) => row.href}
              renderItem={(row) => (
                <>
                  {row.context ? (
                    <p className="text-fg-secondary line-clamp-3 text-[11px] leading-relaxed">
                      {row.context}
                    </p>
                  ) : null}
                  <div className="mt-1.5 flex flex-wrap items-center gap-2">
                    <span className="text-fg-secondary font-mono text-[10px] font-semibold">
                      {t19("matchClass.SEARCH_MATCH")}
                    </span>
                    {row.citation ? <CitationChip citation={row.citation} size="sm" /> : null}
                    {row.matchKind ? (
                      <span className="text-fg-tertiary font-mono text-[10px]">
                        {t18(`matchKind.${row.matchKind}`)}
                      </span>
                    ) : null}
                    <ActionLink href={row.href}>{t18("openExactSource")}</ActionLink>
                  </div>
                </>
              )}
            />
          </Panel>
        ) : null}
        {edges.length ? (
          <Panel title={t18("relationships")}>
            {edgeGroups.length > MAX_EDGE_GROUPS ||
            (network.page && network.page.total > edges.length) ? (
              <p className="text-fg-tertiary mb-2 text-[10px]">
                {t19("relationshipTotal", {
                  shown: edgeGroups
                    .slice(0, MAX_EDGE_GROUPS)
                    .reduce((sum, group) => sum + group.items.length, 0),
                  total: network.page?.total ?? edges.length,
                })}{" "}
                <Link
                  href={`/network?focus=${encodeURIComponent(entityRef)}`}
                  className="text-accent font-semibold"
                >
                  {t("viewNetwork")}
                </Link>
              </p>
            ) : null}
            <GroupedSourceList
              groups={edgeGroups.slice(0, MAX_EDGE_GROUPS)}
              countLabel={(n) => tg("relationshipCount", { count: n })}
              itemKey={(edge) => edge.id}
              renderItem={(edge) => (
                <div className="space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <SourceBadge type={edge.sourceType} size="sm" />
                    <VerificationBadge state={edge.verification} size="sm" />
                    <EvidenceBasis kind={edge.evidenceKind} count={edge.evidenceCount} />
                  </div>
                  {edge.provenance ? (
                    <ProvenanceSource provenance={edge.provenance} />
                  ) : (
                    <div className="flex flex-wrap items-center gap-2">
                      <CitationChip citation={edge.citation} size="sm" />
                      {edge.sourcePath ? (
                        <ActionLink href={edge.sourcePath}>{t("openSource")}</ActionLink>
                      ) : null}
                    </div>
                  )}
                </div>
              )}
            />
          </Panel>
        ) : null}
      </div>
    </div>
  );
}

export function RealExhibitScreen({
  exhibit,
  occurrences,
  mentions = NO_MENTIONS,
  network,
  statusEvents = [],
}: {
  exhibit: ExhibitDossier;
  occurrences: readonly SearchResult[];
  mentions?: EntityMentionsView;
  network: NetworkView;
  statusEvents?: readonly ExhibitStatusEventView[];
}) {
  const t = useTranslations("phase5");
  const t15 = useTranslations("phase15");
  const t18 = useTranslations("phase18");
  const tr = useTranslations("referenceCounts");
  return (
    <AppShell crumbs={[{ label: t("exhibits"), href: "/exhibits" }, { label: exhibit.id }]}>
      <ScreenHeader
        realData
        eyebrow={t15("verifiedPublicRecord")}
        title={exhibit.title}
        description={t15("sourceBacked")}
        actions={<SourceBadge type="exhibit" />}
      />
      <div className="mx-auto w-full max-w-[1100px] space-y-3 p-3 md:p-4">
        <StatStrip
          label={t15("referenceCounts")}
          disclaimer={tr("disclaimer")}
          items={countKeys.map((key) => ({ key, label: tr(key), value: exhibit.counts[key] }))}
        />
        <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_320px]">
          <Panel title={t15("summary")}>
            <p className="text-fg-body text-[12px] leading-relaxed">
              {exhibit.description ?? t18("noDescription")}
            </p>
          </Panel>
          <Panel title={t("metadata")}>
            <KeyValue
              rows={[
                { key: "id", label: t18("officialIdentifier"), value: exhibit.id },
                {
                  key: "status",
                  label: t18("status"),
                  value:
                    exhibit.status.toLowerCase() === "unknown" ? (
                      <IntelligenceStateLabel state="UNKNOWN" />
                    ) : (
                      exhibit.status.toUpperCase()
                    ),
                },
                { key: "party", label: t18("tenderedBy"), value: exhibit.tenderedBy ?? "—" },
                {
                  key: "date",
                  label: t15("date"),
                  value: exhibit.admittedDate ?? exhibit.documentDate ?? "—",
                },
              ]}
            />
            {exhibit.throughWitnessCode ? (
              <div className="mt-3">
                <ActionLink href={`/witnesses/${exhibit.throughWitnessCode}`}>
                  {t18("throughWitness")}: {exhibit.throughWitnessCode}
                </ActionLink>
              </div>
            ) : null}
          </Panel>
        </div>
        <StatusHistoryPanel events={statusEvents} status={exhibit.status} />
        <ResearchTrail
          entityRef={exhibit.id}
          occurrences={occurrences}
          mentions={mentions}
          network={network}
        />
      </div>
    </AppShell>
  );
}

export function RealOrganizationScreen({
  organization,
  occurrences,
  mentions = NO_MENTIONS,
  network,
}: {
  organization: OrganizationDossier;
  occurrences: readonly SearchResult[];
  mentions?: EntityMentionsView;
  network: NetworkView;
}) {
  const t15 = useTranslations("phase15");
  const t18 = useTranslations("phase18");
  const tr = useTranslations("referenceCounts");
  return (
    <AppShell
      crumbs={[
        { label: t18("organizations"), href: "/organizations" },
        { label: organization.name },
      ]}
    >
      <ScreenHeader
        realData
        eyebrow={t15("verifiedPublicRecord")}
        title={organization.name}
        description={t15("sourceBacked")}
        actions={<SourceBadge type="court" />}
      />
      <div className="mx-auto w-full max-w-[1100px] space-y-3 p-3 md:p-4">
        <StatStrip
          label={t15("referenceCounts")}
          disclaimer={tr("disclaimer")}
          items={countKeys.map((key) => ({ key, label: tr(key), value: organization.counts[key] }))}
        />
        <Panel title={t18("overview")}>
          <KeyValue
            rows={[
              { key: "kind", label: t18("organizationType"), value: organization.kind ?? "—" },
              {
                key: "variants",
                label: t15("aliases"),
                value: organization.nameVariants.join(" · ") || "—",
              },
            ]}
          />
        </Panel>
        <ResearchTrail
          entityRef={organization.slug}
          occurrences={occurrences}
          mentions={mentions}
          network={network}
        />
      </div>
    </AppShell>
  );
}

export function OrganizationDirectoryScreen({ rows }: { rows: readonly OrganizationDossier[] }) {
  const t15 = useTranslations("phase15");
  const t18 = useTranslations("phase18");
  return (
    <AppShell>
      <ScreenHeader
        realData
        eyebrow={t15("verifiedPublicRecord")}
        title={t18("organizations")}
        description={t15("sourceBacked")}
      />
      <div className="mx-auto w-full max-w-[1100px] p-3 md:p-4">
        <Panel title={t18("organizations")}>
          <ul className="divide-border-faint divide-y">
            {rows.map((row) => (
              <li key={row.slug} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <span>
                  <Link
                    href={`/organizations/${row.slug}`}
                    className="text-accent text-[12px] font-semibold"
                  >
                    {row.name}
                  </Link>
                  <span className="text-fg-secondary mt-1 block text-[11px]">
                    {row.kind ?? "—"}
                  </span>
                </span>
                <span className="tabular text-fg-muted text-[10px]">
                  {row.counts.documentMentions + row.counts.transcriptMentions}{" "}
                  {t18("sourceOccurrences").toLowerCase()}
                </span>
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </AppShell>
  );
}

function RecordActivity({ href, label, value }: { href: string; label: string; value: number }) {
  return (
    <ActionLink href={href}>
      <span className="flex w-full min-w-0 items-center justify-between gap-4">
        <span>{label}</span>
        <span className="tabular text-fg font-semibold">{value}</span>
      </span>
    </ActionLink>
  );
}

export function RealIncidentScreen({ incident }: { incident: IncidentView }) {
  const t = useTranslations("phase5");
  const t15 = useTranslations("phase15");
  const ti = useTranslations("incidentDetail");
  const tr = useTranslations("referenceCounts");
  const date = [incident.dateFrom, incident.dateTo].filter(Boolean).join(" — ") || "—";
  return (
    <AppShell crumbs={[{ label: t("incidents"), href: "/incidents" }, { label: incident.slug }]}>
      <ScreenHeader
        realData
        eyebrow={
          incident.sourceCategory === "spo_allegation"
            ? ti("spoAllegation")
            : t15("verifiedPublicRecord")
        }
        title={incident.title}
        description={t15("incidentBoundary")}
        actions={
          <>
            <SourceBadge type="incident" />
            <VerificationBadge state={incident.verification} />
          </>
        }
      />
      <div className="mx-auto w-full max-w-[1100px] space-y-3 p-3 md:p-4">
        <StatStrip
          label={t15("referenceCounts")}
          disclaimer={tr("disclaimer")}
          items={countKeys.map((key) => ({ key, label: tr(key), value: incident.counts[key] }))}
        />
        <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_320px]">
          <Panel title={t15("summary")}>
            {incident.summary ? (
              <p className="text-fg-body text-[13px] leading-relaxed">{incident.summary}</p>
            ) : (
              <EmptyState title={t15("noSourceOccurrences")} reason={t15("incidentBoundary")} />
            )}
          </Panel>
          <Panel title={t("metadata")}>
            <KeyValue
              rows={[
                { key: "id", label: "ID", value: incident.slug },
                { key: "location", label: t15("location"), value: incident.location || "—" },
                { key: "date", label: ti("dateAsPleaded"), value: incident.dateAsPleaded || date },
                { key: "precision", label: t15("precision"), value: incident.datePrecision },
              ]}
            />
          </Panel>
        </div>
        {incident.sourceCategory === "spo_allegation" ? (
          <Panel title={ti("withdrawalReview")}>
            <p className="text-fg-body text-[12px] leading-relaxed">
              {incident.withdrawalStatus === "UNAFFECTED"
                ? ti("unaffected")
                : ti("reviewUnavailable")}
            </p>
            {incident.withdrawalBasis ? (
              <p className="text-fg-secondary mt-2 text-[11px] leading-relaxed">
                {incident.withdrawalBasis}
              </p>
            ) : null}
          </Panel>
        ) : null}
        <Panel title={ti("sources")}>
          {incident.sources.length ? (
            <ol className="space-y-3">
              {incident.sources.map((source) => (
                <li
                  key={`${source.role}-${source.sequence}`}
                  className="border-border-subtle bg-surface-raised rounded-card border p-3"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-fg text-[11px] font-semibold">
                      {ti(`role.${source.role}`)}
                    </span>
                    <VerificationBadge state={source.verification} size="sm" />
                  </div>
                  <p className="text-fg-secondary mt-1 text-[11px]">
                    {source.sourceRef}
                    {source.paragraphNumber ? ` · ¶${source.paragraphNumber}` : ""}
                  </p>
                  {source.excerpt ? (
                    <blockquote className="border-spo text-fg-body mt-2 border-l-2 pl-3 text-[12px] leading-relaxed">
                      {source.excerpt}
                    </blockquote>
                  ) : null}
                  {source.note ? (
                    <p className="text-fg-secondary mt-2 text-[11px] leading-relaxed">
                      {source.note}
                    </p>
                  ) : null}
                  <div className="mt-2">
                    {source.targetPath ? (
                      <ActionLink href={source.targetPath}>
                        {source.role === "operative" ? ti("openExactSource") : ti("openSource")}
                      </ActionLink>
                    ) : (
                      <span className="text-fg-muted text-[11px]">{ti("sourceUnavailable")}</span>
                    )}
                  </div>
                </li>
              ))}
            </ol>
          ) : (
            <EmptyState title={ti("noSources")} reason={t15("incidentBoundary")} />
          )}
        </Panel>
      </div>
    </AppShell>
  );
}

export function RealPublicScreen({
  topic,
  rowsByKind,
  totals = {},
}: {
  topic?: string;
  rowsByKind: Readonly<Record<DirectoryKind, readonly DirectoryRow[]>>;
  /** Directory totals when `rowsByKind` holds only a first page. */
  totals?: Partial<Readonly<Record<DirectoryKind, number>>>;
}) {
  const t = useTranslations("phase5");
  const ts = useTranslations("screens");
  const t15 = useTranslations("phase15");
  const kinds: readonly DirectoryKind[] = [
    "findings",
    "documents",
    "witnesses",
    "people",
    "exhibits",
    "incidents",
  ];
  const active = kinds.includes(topic as DirectoryKind) ? (topic as DirectoryKind) : "findings";
  const rows = rowsByKind[active];
  return (
    <AppShell mode="light">
      <ScreenHeader
        realData
        eyebrow={t15("verifiedPublicRecord")}
        title={t("simpleIntro")}
        description={t15("sourceBacked")}
      />
      <div className="mx-auto w-full max-w-[1100px] space-y-4 p-3 md:p-6">
        <nav aria-label={t15("publicSections")} className="grid grid-cols-2 gap-2 md:grid-cols-6">
          {kinds.map((kind) => (
            <ActionLink key={kind} href={`/public/${kind}`} primary={kind === active}>
              {ts(kind)} ({totals[kind] ?? rowsByKind[kind].length})
            </ActionLink>
          ))}
        </nav>
        <Panel title={ts(active)}>
          {rows.length ? (
            <ul className="divide-border-faint divide-y">
              {rows.slice(0, 25).map((row) => (
                <li key={row.id} className="py-3">
                  <a href={row.href} className="text-accent font-semibold">
                    {row.title}
                  </a>
                  <p className="text-fg-secondary mt-1 text-[12px]">{row.description}</p>
                  <p className="identifier text-fg-muted mt-1 text-[10px]">
                    {row.id} · {row.date}
                  </p>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title={t15(`empty.${active}`)} reason={t15("sourceBacked")} />
          )}
        </Panel>
        <NoteStrip tone="legal">{t("plainLanguage")}</NoteStrip>
      </div>
    </AppShell>
  );
}
