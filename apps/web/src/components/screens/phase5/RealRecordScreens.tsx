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
import { ActionLink, ScreenHeader } from "./ScreenChrome";
import { KeyValue, NoteStrip, StatStrip } from "./Workspace";

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
  const t15 = useTranslations("phase15");
  const tr = useTranslations("referenceCounts");
  const t18 = useTranslations("phase18");
  return (
    <AppShell crumbs={[{ label: tb("people"), href: "/people" }, { label: person.displayName }]}>
      <ScreenHeader
        realData
        eyebrow={t15("verifiedPublicRecord")}
        title={person.displayName}
        description={t15("sourceBacked")}
        actions={
          <div className="flex gap-2">
            <ActionLink href={`/network?focus=${encodeURIComponent(person.slug)}`}>
              {t("viewNetwork")}
            </ActionLink>
            <ActionLink href={`/search?q=${encodeURIComponent(person.displayName)}`}>
              {t("search")}
            </ActionLink>
          </div>
        }
      />
      <div className="mx-auto w-full max-w-[1440px] space-y-3 p-3 md:p-4">
        <StatStrip
          label={t15("referenceCounts")}
          disclaimer={tr("disclaimer")}
          items={countKeys.map((key) => ({ key, label: tr(key), value: person.counts[key] }))}
        />
        <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_340px]">
          <Panel title={t18("recordActivity")}>
            <div className="grid gap-2 lg:grid-cols-2">
              <RecordActivity
                href={`/search?q=${encodeURIComponent(person.displayName)}`}
                label={t18("openDocuments")}
                value={person.counts.documentMentions}
              />
              <RecordActivity
                href={`/search?q=${encodeURIComponent(person.displayName)}`}
                label={t18("openTranscripts")}
                value={person.counts.transcriptMentions}
              />
              <RecordActivity
                href={`/search?q=${encodeURIComponent(person.displayName)}`}
                label={t18("openFindings")}
                value={person.counts.findings}
              />
              <RecordActivity
                href={`/network?focus=${encodeURIComponent(person.slug)}`}
                label={t18("openRelationships")}
                value={person.relationshipCount ?? 0}
              />
            </div>
          </Panel>
          <Panel title={t("metadata")}>
            <KeyValue rows={[{ key: "role", label: t15("role"), value: person.role || "—" }]} />
            <p className="section-label mt-3 mb-1">{t15("aliases")}</p>
            <div className="flex flex-wrap gap-1.5">
              {person.aliases.length ? (
                person.aliases.slice(0, 6).map((alias) => (
                  <span
                    key={alias}
                    className="rounded-chip border-border bg-surface-raised text-fg-secondary border px-2 py-1 text-[10px]"
                  >
                    {alias}
                  </span>
                ))
              ) : (
                <span className="text-fg-muted text-[11px]">—</span>
              )}
            </div>
            <div className="mt-3 flex gap-2">
              <ActionLink href={`/search?q=${encodeURIComponent(person.displayName)}`}>
                {t("search")}
              </ActionLink>
              <ActionLink href={`/network?focus=${encodeURIComponent(person.slug)}`}>
                {t("viewNetwork")}
              </ActionLink>
            </div>
          </Panel>
        </div>
        {appearances.length ? <AppearancesPanel appearances={appearances} /> : null}
        <ResearchTrail
          entityRef={person.slug}
          occurrences={occurrences}
          mentions={mentions}
          network={network}
        />
        <NoteStrip tone="legal">{tb("noScore")}</NoteStrip>
      </div>
    </AppShell>
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

function MentionList({ mentions }: { mentions: readonly EntityMention[] }) {
  const t18 = useTranslations("phase18");
  const t19 = useTranslations("phase19");
  return (
    <ul className="divide-border-faint divide-y">
      {mentions.map((mention) => (
        <li key={mention.id} className="py-2 first:pt-0 last:pb-0">
          <Link href={mention.href} className="text-accent text-[11px] font-semibold">
            {mention.documentTitle}
          </Link>
          <p className="text-fg mt-1 font-mono text-[11px] break-words">{mention.occurrenceText}</p>
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
        </li>
      ))}
    </ul>
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
  const verified = mentions.items
    .filter((mention) => mention.matchClass === "VERIFIED_MENTION")
    .slice(0, 8);
  const reviewRequired = mentions.items
    .filter((mention) => mention.matchClass === "REVIEW_REQUIRED")
    .slice(0, 6);
  const sources = occurrences
    .filter(
      (row, index, all) =>
        (row.category === "documents" || row.category === "transcripts") &&
        // Only coordinate-bearing hits are exact occurrences; title-only matches stay in Search.
        (row.citation?.page !== undefined ||
          row.citation?.paraFrom !== undefined ||
          row.citation?.lineFrom !== undefined) &&
        all.findIndex((candidate) => candidate.href === row.href) === index,
    )
    .slice(0, 6);
  const focusNode = network.nodes.find((node) => node.ref === entityRef);
  const edges = focusNode
    ? network.edges
        .filter((edge) => edge.from === focusNode.id || edge.to === focusNode.id)
        .slice(0, 8)
    : [];
  const nodeLabel = (id: string) => network.nodes.find((node) => node.id === id)?.label ?? "—";
  if (!mentions.items.length && !sources.length && !edges.length) return null;
  return (
    <div className="space-y-3">
      {mentions.items.length ? (
        <div className="grid gap-3 lg:grid-cols-2">
          {verified.length ? (
            <Panel title={t19("verifiedMentions")}>
              {mentions.total > mentions.items.length ? (
                <p className="text-fg-tertiary mb-2 text-[10px]">
                  {t19("mentionTotal", { shown: verified.length, total: mentions.total })}
                </p>
              ) : null}
              <MentionList mentions={verified} />
            </Panel>
          ) : null}
          {reviewRequired.length ? (
            <Panel title={t19("reviewRequiredMentions")}>
              <p className="text-fg-secondary mb-2 text-[11px] leading-relaxed">
                {t19("reviewRequiredNote")}
              </p>
              <MentionList mentions={reviewRequired} />
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
            <ul className="divide-border-faint divide-y">
              {sources.map((row) => (
                <li key={row.href} className="py-2 first:pt-0 last:pb-0">
                  <Link href={row.href} className="text-accent text-[11px] font-semibold">
                    {row.title}
                  </Link>
                  {row.context ? (
                    <p className="text-fg-secondary mt-1 line-clamp-3 text-[11px] leading-relaxed">
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
                </li>
              ))}
            </ul>
          </Panel>
        ) : null}
        {edges.length ? (
          <Panel title={t18("relationships")}>
            {network.page && network.page.total > edges.length ? (
              <p className="text-fg-tertiary mb-2 text-[10px]">
                {t19("relationshipTotal", { shown: edges.length, total: network.page.total })}{" "}
                <Link
                  href={`/network?focus=${encodeURIComponent(entityRef)}`}
                  className="text-accent font-semibold"
                >
                  {t("viewNetwork")}
                </Link>
              </p>
            ) : null}
            <ul className="divide-border-faint divide-y">
              {edges.map((edge) => {
                const other = edge.from === focusNode?.id ? edge.to : edge.from;
                return (
                  <li key={edge.id} className="space-y-1.5 py-2 first:pt-0 last:pb-0">
                    <p className="text-fg text-[11px] font-medium">
                      {edge.relation.replaceAll("_", " ")} · {nodeLabel(other)}
                    </p>
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
                  </li>
                );
              })}
            </ul>
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
  const tr = useTranslations("referenceCounts");
  const date = [incident.dateFrom, incident.dateTo].filter(Boolean).join(" — ") || "—";
  return (
    <AppShell crumbs={[{ label: t("incidents"), href: "/incidents" }, { label: incident.slug }]}>
      <ScreenHeader
        realData
        eyebrow={t15("verifiedPublicRecord")}
        title={incident.title}
        description={t15("incidentBoundary")}
        actions={<SourceBadge type="incident" />}
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
                { key: "date", label: t15("date"), value: date },
                { key: "precision", label: t15("precision"), value: incident.datePrecision },
              ]}
            />
          </Panel>
        </div>
      </div>
    </AppShell>
  );
}

export function RealPublicScreen({
  topic,
  rowsByKind,
}: {
  topic?: string;
  rowsByKind: Readonly<Record<DirectoryKind, readonly DirectoryRow[]>>;
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
              {ts(kind)} ({rowsByKind[kind].length})
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
