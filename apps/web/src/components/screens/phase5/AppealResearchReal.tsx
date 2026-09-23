"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import type {
  AppealIssueView,
  AppealWorkspaceView,
  ArgumentLabView,
  FindingCitationView,
  StatementComparisonView,
} from "@/data";
import { EmptyState, GapNotice } from "@/components/primitives/States";
import { Panel } from "@/components/primitives/Panel";
import { CitationChip, RecordBlock, VerificationBadge } from "@/components/provenance";
import { AppShell } from "@/components/shell/AppShell";
import { ScreenHeader } from "./ScreenChrome";
import { KeyValue, NoteStrip, SectionCard } from "./Workspace";

function SourceLink({ source }: { source: FindingCitationView }) {
  const t = useTranslations("phase12");
  return (
    <span className="flex flex-wrap items-center gap-2">
      <CitationChip citation={source.citation} navigable={false} size="sm" />
      {source.targetPath ? (
        <Link href={source.targetPath} className="text-accent text-[10px] font-semibold">
          {t("openExactSource")}
        </Link>
      ) : (
        <span className="text-unresolved text-[10px]">{t("unresolved")}</span>
      )}
    </span>
  );
}

export function RealAppealScreen({
  workspace,
  issue,
}: {
  workspace: AppealWorkspaceView;
  issue?: AppealIssueView;
}) {
  const t = useTranslations("phase12");
  return (
    <AppShell footer={t("noPrediction")} showDemoFlag={false}>
      <ScreenHeader
        eyebrow={t("appealResearch")}
        title={t("potentialIssues")}
        description={t("neutralFraming")}
        realData
      />
      <div className="mx-auto grid w-full max-w-[1440px] gap-4 p-3 md:p-4 xl:grid-cols-[230px_minmax(0,1fr)_300px]">
        <aside className="space-y-3">
          <Panel title={t("categories")}>
            <ul className="space-y-2 text-[11px]">
              {workspace.issues.map((item) => (
                <li key={item.key}>
                  <Link
                    className="text-accent"
                    href={`/appeal?issue=${encodeURIComponent(item.key)}`}
                  >
                    {t(`category.${item.category}`)}
                  </Link>
                </li>
              ))}
            </ul>
          </Panel>
          <Panel title={t("coverage")}>
            <KeyValue
              rows={[
                { key: "i", label: t("issues"), value: workspace.coverage.issues },
                { key: "s", label: t("sourceLinks"), value: workspace.coverage.sourceBackedLinks },
                { key: "c", label: t("comparisons"), value: workspace.coverage.comparisons },
                { key: "r", label: t("resolved"), value: workspace.coverage.citationsResolved },
              ]}
            />
          </Panel>
        </aside>
        <div className="min-w-0 space-y-4">
          {!issue ? (
            <EmptyState title={t("noIssues")} reason={t("noIssuesReason")} />
          ) : (
            <>
              <SectionCard
                title={issue.title}
                aside={<VerificationBadge state={issue.verification} size="sm" />}
              >
                <p className="text-fg-body text-[12px] leading-relaxed">{issue.description}</p>
                <div className="mt-3 flex flex-wrap gap-2 text-[10px]">
                  <span className="rounded-badge bg-surface-raised px-2 py-1">
                    {t(`category.${issue.category}`)}
                  </span>
                  <span className="rounded-badge bg-surface-raised px-2 py-1">
                    {t(`courtTreatment.${issue.courtTreatment}`)}
                  </span>
                  <span className="rounded-badge bg-surface-raised px-2 py-1">
                    {t(`redTeamResult.${issue.redTeamResult}`)}
                  </span>
                </div>
                <p className="text-fg-secondary mt-3 text-[11px]">{issue.courtTreatmentNote}</p>
              </SectionCard>
              {issue.sources.map((source) => (
                <RecordBlock
                  key={source.id}
                  sourceType={source.source.citation.sourceType}
                  title={t(`role.${source.role}`)}
                >
                  <p className="font-serif text-[12px] leading-relaxed whitespace-pre-line">
                    {source.excerpt}
                  </p>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <SourceLink source={source.source} />
                    <VerificationBadge state={source.verification} size="sm" />
                  </div>
                  {source.note ? (
                    <p className="text-fg-muted mt-2 text-[10px]">{source.note}</p>
                  ) : null}
                </RecordBlock>
              ))}
              <SectionCard title={t("missingMaterial")}>
                <div className="space-y-2">
                  {issue.missingMaterial.map((item) => (
                    <GapNotice
                      key={item.reference}
                      kind="unresolved-citation"
                      reference={item.reference}
                      extent={item.kind}
                      reason={item.reason}
                    />
                  ))}
                </div>
              </SectionCard>
              <div className="flex flex-wrap gap-3">
                <Link
                  className="border-accent text-accent rounded-control border px-3 py-2 text-[11px] font-semibold"
                  href={`/appeal/argument/${encodeURIComponent(issue.key)}`}
                >
                  {t("openArgumentLab")}
                </Link>
                {issue.comparisons[0] ? (
                  <Link
                    className="border-border text-fg rounded-control border px-3 py-2 text-[11px]"
                    href={`/witnesses/${encodeURIComponent(issue.comparisons[0].key)}/compare`}
                  >
                    {t("openComparison")}
                  </Link>
                ) : null}
              </div>
              <NoteStrip tone="legal">{t("noPrediction")}</NoteStrip>
            </>
          )}
        </div>
        <aside className="space-y-3">
          <Panel title={t("citationAudit")}>
            {issue ? (
              <>
                <KeyValue
                  rows={[
                    { key: "t", label: t("citationsTotal"), value: issue.audit.citationsTotal },
                    { key: "r", label: t("resolved"), value: issue.audit.citationsResolved },
                    { key: "q", label: t("quotesVerified"), value: issue.audit.quotesVerified },
                    { key: "u", label: t("unresolved"), value: issue.audit.unresolved },
                  ]}
                />
                <p className="text-fg-secondary mt-3 text-[11px]">
                  {issue.audit.readyForHumanReview ? t("ready") : t("notReady")}
                </p>
                <ul className="text-unresolved mt-2 space-y-1 text-[10px]">
                  {issue.audit.issues.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </>
            ) : null}
          </Panel>
          <Panel title={t("corpusLimitations")}>
            <ul className="text-fg-secondary list-disc space-y-1 pl-4 text-[11px]">
              {workspace.limitations.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </Panel>
          <Panel title={t("willNotDo")}>
            <p className="text-fg-secondary text-[11px]">{t("willNotDoBody")}</p>
          </Panel>
        </aside>
      </div>
    </AppShell>
  );
}

export function RealArgumentLabScreen({ lab }: { lab: ArgumentLabView }) {
  const t = useTranslations("phase12");
  const perspectives = ["defence_analyst", "spo_red_team", "neutral_reviewer"];
  return (
    <AppShell
      showDemoFlag={false}
      footer={lab.notice}
      crumbs={[{ label: t("appealResearch"), href: "/appeal" }, { label: lab.issue.key }]}
    >
      <ScreenHeader
        eyebrow={t("argumentLab")}
        title={lab.title}
        description={t("argumentLabNote")}
        realData
      />
      <div className="mx-auto w-full max-w-[1440px] space-y-4 p-3 md:p-4">
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_300px]">
          <SectionCard title={t("sourceBackedOutline")}>
            <p className="font-serif text-[13px] leading-relaxed">{lab.draft}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {lab.citations.map((source) => (
                <SourceLink key={source.citation.display} source={source} />
              ))}
            </div>
          </SectionCard>
          <Panel title={t("citationHealth")}>
            <KeyValue
              rows={[
                { key: "c", label: t("resolved"), value: lab.citations.length },
                { key: "u", label: t("unsupported"), value: lab.unsupportedSentences.length },
                { key: "r", label: t("redTeam"), value: t(`redTeamResult.${lab.result}`) },
              ]}
            />
          </Panel>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {perspectives.map((perspective) => (
            <SectionCard key={perspective} title={t(`perspective.${perspective}`)}>
              <ul className="space-y-3">
                {lab.stages
                  .filter((row) => row.perspective === perspective)
                  .map((row) => (
                    <li key={`${perspective}-${row.sequence}`} className="text-[11px]">
                      <span className="rounded-badge bg-surface-raised mb-1 inline-block px-2 py-0.5 text-[10px]">
                        {t(`reviewCategory.${row.category}`)}
                      </span>
                      <p className="text-fg-body">{row.text}</p>
                      {row.source ? (
                        <div className="mt-2">
                          <SourceLink source={row.source} />
                        </div>
                      ) : null}
                    </li>
                  ))}
              </ul>
            </SectionCard>
          ))}
        </div>
        <NoteStrip tone="legal">{lab.notice}</NoteStrip>
      </div>
    </AppShell>
  );
}

export function RealStatementComparisonScreen({
  comparison,
}: {
  comparison: StatementComparisonView;
}) {
  const t = useTranslations("phase12");
  return (
    <AppShell showDemoFlag={false} footer={t("comparisonNeutral")}>
      <ScreenHeader
        eyebrow={comparison.key}
        title={t("statementComparison")}
        description={t("comparisonNeutral")}
        realData
      />
      <div className="mx-auto w-full max-w-[1200px] space-y-4 p-3 md:p-4">
        <SectionCard
          title={comparison.title}
          aside={<VerificationBadge state={comparison.verification} size="sm" />}
        >
          <span className="rounded-badge bg-surface-raised px-2 py-1 text-[10px]">
            {t(`comparison.${comparison.classification}`)}
          </span>
          <div className="mt-3 grid gap-4 md:grid-cols-2">
            {([comparison.statementA, comparison.statementB] as const).map((statement, index) => (
              <RecordBlock
                key={index}
                sourceType={statement.source.citation.sourceType}
                title={index === 0 ? t("statementA") : t("statementB")}
              >
                {statement.speaker ? (
                  <p className="text-fg-muted text-[10px]">{statement.speaker}</p>
                ) : null}
                <p className="mt-2 font-serif text-[12px] leading-relaxed">{statement.excerpt}</p>
                <div className="mt-2">
                  <SourceLink source={statement.source} />
                </div>
              </RecordBlock>
            ))}
          </div>
          <p className="text-fg-secondary mt-3 text-[11px]">{comparison.explanation}</p>
        </SectionCard>
        <NoteStrip tone="legal">{t("noCredibilityInference")}</NoteStrip>
      </div>
    </AppShell>
  );
}
