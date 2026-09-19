import { useTranslations } from "next-intl";
import { Panel } from "@/components/primitives/Panel";
import {
  ProtectionNotice,
  RecordBlock,
  ReferenceCountStrip,
  SourceBadge,
  VerificationBadge,
} from "@/components/provenance";
import { AppShell } from "@/components/shell/AppShell";
import { courtCitation, mockRepository, transcriptCitation } from "@/mock";
import { ActionLink, DemoNotice, ScreenHeader, TabStrip, WorkspaceGrid } from "./ScreenChrome";

const DOSSIER_TAB_KEYS = [
  "overview",
  "documents",
  "testimony",
  "exhibits",
  "incidents",
  "viewTimeline",
  "courtFindings",
  "arguments",
  "network",
  "appealReview",
] as const;

export function PersonDossierScreen({ slug }: { slug: string }) {
  const t = useTranslations("phase5");
  const footer = useTranslations("footer");
  const person = mockRepository.getPerson(slug);
  const tabs = DOSSIER_TAB_KEYS.map((key) => ({ key, label: t(key), href: `?tab=${key}` }));
  return (
    <AppShell crumbs={[{ label: person.displayName }]} footer={footer("referenceCounts")}>
      <ScreenHeader
        eyebrow={t("overview")}
        title={person.displayName}
        description={person.role}
        actions={
          <>
            <ActionLink href={`/network?focus=${person.slug}&depth=2`}>
              {t("viewNetwork")}
            </ActionLink>
            <ActionLink href="/timeline">{t("viewTimeline")}</ActionLink>
            <ActionLink href={`/network/path?from=${person.slug}`}>
              {t("findConnection")}
            </ActionLink>
            <ActionLink href="/ai">{t("askAi")}</ActionLink>
          </>
        }
      />
      <TabStrip tabs={tabs} />
      <WorkspaceGrid
        right={
          <>
            <Panel title={t("network")}>
              <MiniNetwork />
            </Panel>
            <Panel className="mt-3" title={t("courtFindings")}>
              <RecordLinkList />
            </Panel>
          </>
        }
      >
        <div className="flex flex-col gap-4">
          <DemoNotice />
          <ReferenceCountStrip counts={person.counts} />
          <RecordBlock sourceType="court" title={t("overview")} citations={[courtCitation]}>
            <p className="font-serif">
              Generic demo summary. Every substantive sentence on a production dossier will resolve
              to a source.
            </p>
          </RecordBlock>
          <Panel title={t("viewTimeline")}>
            <TimelineList />
          </Panel>
        </div>
      </WorkspaceGrid>
    </AppShell>
  );
}

export function WitnessDossierScreen({ code }: { code: string }) {
  const t = useTranslations("phase5");
  const footer = useTranslations("footer");
  const witness = mockRepository.getWitness(code);
  const title = witness.protected ? witness.code : witness.public.displayName;
  const tabs = [
    "overview",
    "testimony",
    "crossExamination",
    "priorStatements",
    "exhibits",
    "courtFindings",
    "statementComparison",
    "viewTimeline",
    "network",
    "askAi",
  ].map((key) => ({ key, label: t(key), href: `?tab=${key}` }));
  const counts = {
    documentMentions: 7,
    transcriptMentions: 18,
    exhibitRefs: 4,
    findings: 2,
    witnessesWhoReferred: 0,
    incidents: 1,
    citationsResolved: 26,
  };
  return (
    <AppShell crumbs={[{ label: witness.code }]} footer={footer("neutrality")}>
      {witness.protected ? (
        <ProtectedWitnessHeader code={witness.code} />
      ) : (
        <ScreenHeader
          eyebrow={t("testimony")}
          title={title}
          description={`${witness.code} · ${witness.public.statedOccupation ?? ""}`}
          actions={<SourceBadge type="witness" />}
        />
      )}
      <TabStrip tabs={tabs} />
      <WorkspaceGrid
        left={
          <Panel title={t("examination")}>
            <TimelineList />
          </Panel>
        }
        right={
          <>
            <Panel title={t("courtFindings")}>
              <RecordLinkList />
            </Panel>
            <Panel className="mt-3" title={t("statementComparison")}>
              <ActionLink href={`/witnesses/${witness.code}/compare`}>{t("open")}</ActionLink>
            </Panel>
          </>
        }
      >
        <div className="flex flex-col gap-4">
          {witness.protected ? <ProtectionNotice /> : null}
          <ReferenceCountStrip counts={counts} />
          <Panel title={t("testimony")}>
            <TranscriptExcerpt code={witness.code} />
          </Panel>
          <Panel title={t("crossExamination")} actions={<VerificationBadge state="ai-flagged" />}>
            <TranscriptExcerpt code={witness.code} />
            <div className="mt-3">
              <ActionLink href={`/witnesses/${witness.code}/compare?segment=demo`}>
                {t("statementComparison")}
              </ActionLink>
            </div>
          </Panel>
        </div>
      </WorkspaceGrid>
    </AppShell>
  );
}

export function ProtectedWitnessHeader({ code }: { code: string }) {
  const t = useTranslations("phase5");
  return (
    <ScreenHeader
      eyebrow={t("protectedOnly")}
      title={<span className="identifier text-witness">{code}</span>}
      description={t("protectedOnly")}
      actions={<SourceBadge type="witness" />}
    />
  );
}

function TranscriptExcerpt({ code }: { code: string }) {
  const t = useTranslations("phase5");
  return (
    <div className="font-serif text-[12px] leading-[1.8]">
      <div className="grid grid-cols-[28px_80px_1fr] gap-2">
        <span className="tabular text-fg-muted">12</span>
        <strong className="text-fg-secondary font-sans">COUNSEL:</strong>
        <span>
          {t("question")}: Generic sample question about the sequence recorded in the public
          material.
        </span>
        <span className="tabular text-fg-muted">15</span>
        <strong className="text-witness font-sans">{code}:</strong>
        <span>
          {t("answer")}: Generic sample response shown only to demonstrate transcript layout.
        </span>
      </div>
      <div className="mt-3">
        <RecordBlock sourceType="witness" citations={[transcriptCitation]}>
          Illustrative transcript lines; not real testimony.
        </RecordBlock>
      </div>
    </div>
  );
}

function TimelineList() {
  return (
    <ol className="space-y-2">
      {mockRepository
        .getTimeline()
        .slice(0, 3)
        .map((item) => (
          <li key={item.id} className="border-border-faint border-b pb-2 text-[11px]">
            <span className="text-fg font-medium">{item.label}</span>
            <div className="text-fg-muted">
              {item.date} · {item.dateType}
            </div>
          </li>
        ))}
    </ol>
  );
}

function RecordLinkList() {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="identifier text-court">F-DEMO-01</span>
        <VerificationBadge state="verified" />
      </div>
      <p className="text-fg-secondary text-[11px]">Generic illustrative finding.</p>
    </div>
  );
}

function MiniNetwork() {
  return (
    <div
      className="bg-bg-graph rounded-card relative h-36 overflow-hidden"
      aria-label="Network preview"
    >
      <span className="border-accent text-fg absolute top-12 left-5 rounded-full border px-2 py-1 text-[9px]">
        Demo entity
      </span>
      <span className="border-doc text-doc absolute top-5 right-8 rounded border px-2 py-1 text-[9px]">
        P00123
      </span>
      <span className="border-witness text-witness absolute right-7 bottom-5 rounded-full border border-dashed px-2 py-1 text-[9px]">
        W01234
      </span>
    </div>
  );
}
