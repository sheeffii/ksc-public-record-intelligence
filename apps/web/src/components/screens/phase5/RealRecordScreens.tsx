import { useTranslations } from "next-intl";
import { EmptyState } from "@/components/primitives/States";
import { Panel } from "@/components/primitives/Panel";
import { ProtectionNotice, SourceBadge } from "@/components/provenance";
import { AppShell } from "@/components/shell/AppShell";
import type { IncidentView, PersonDossier, WitnessDossier } from "@/data";
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

export function RealPersonScreen({ person }: { person: PersonDossier }) {
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
        actions={<SourceBadge type="court" />}
      />
      <div className="mx-auto w-full max-w-[1100px] space-y-3 p-3 md:p-4">
        <StatStrip
          label={t15("referenceCounts")}
          disclaimer={tr("disclaimer")}
          items={countKeys.map((key) => ({ key, label: tr(key), value: person.counts[key] }))}
        />
        <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_320px]">
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
            <KeyValue
              rows={[
                { key: "role", label: t15("role"), value: person.role || "—" },
                { key: "aliases", label: t15("aliases"), value: person.aliases.join(" · ") || "—" },
              ]}
            />
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
        <NoteStrip tone="legal">{tb("noScore")}</NoteStrip>
      </div>
    </AppShell>
  );
}

export function RealWitnessScreen({ dossier }: { dossier: WitnessDossier }) {
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
      <div className="mx-auto w-full max-w-[1100px] space-y-3 p-3 md:p-4">
        <StatStrip
          label={t15("referenceCounts")}
          disclaimer={tr("disclaimer")}
          items={countKeys.map((key) => ({ key, label: tr(key), value: counts[key] }))}
        />
        <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_320px]">
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
            <NoteStrip>{t18("hearingsUnavailable")}</NoteStrip>
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
