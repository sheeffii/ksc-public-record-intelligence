"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import type { EvidenceMatrixRowView, FindingCitationView, FindingView } from "@/data";
import { EmptyState } from "@/components/primitives/States";
import { Panel } from "@/components/primitives/Panel";
import { CitationChip, RecordBlock, VerificationBadge } from "@/components/provenance";
import { AppShell } from "@/components/shell/AppShell";
import { ScreenHeader } from "./ScreenChrome";
import { KeyValue, SectionCard } from "./Workspace";

function SourceLink({ source, label }: { source?: FindingCitationView; label: string }) {
  const t = useTranslations("phase10");
  if (!source) return <span className="text-unresolved text-[10px]">{t("unresolved")}</span>;
  return (
    <span className="flex flex-wrap items-center gap-2">
      <CitationChip citation={source.citation} navigable={false} size="sm" />
      {source.resolutionState === "resolved" && source.targetPath ? (
        <Link className="text-accent text-[10px] font-semibold" href={source.targetPath}>
          {label}
        </Link>
      ) : (
        <span className="text-unresolved text-[10px]">
          {t("unresolved")}: {source.rawText}
        </span>
      )}
      {source.sourcePath ? (
        <Link className="text-fg-secondary text-[10px]" href={source.sourcePath}>
          {t("openCourtCitation")}
        </Link>
      ) : null}
    </span>
  );
}

function MatrixSourceLink({ row }: { row: EvidenceMatrixRowView }) {
  const t = useTranslations("phase10");
  return (
    <span className="flex flex-wrap items-center gap-2">
      {row.sourceAnchor ? (
        <Link className="text-accent text-[10px] font-semibold" href={row.sourceAnchor.targetPath}>
          {t("openExactSource")}
        </Link>
      ) : (
        <span className="text-unresolved text-[10px]">{t("anchorUnavailable")}</span>
      )}
      {row.citation?.targetPath && row.citation.targetPath !== row.sourceAnchor?.targetPath ? (
        <Link className="text-fg-secondary text-[10px]" href={row.citation.targetPath}>
          {t("openCitedMaterial")}
        </Link>
      ) : null}
      {row.pathFromNodeId && row.pathToNodeId ? (
        <Link
          className="text-fg-secondary text-[10px]"
          href={`/network/path?from=${row.pathFromNodeId}&to=${row.pathToNodeId}`}
        >
          {t("viewEvidencePath")}
        </Link>
      ) : null}
    </span>
  );
}

export function RealFindingDetailScreen({ finding }: { finding: FindingView }) {
  const t = useTranslations("phase10");
  const paraRange = finding.paraTo
    ? `¶¶${finding.paraFrom}-${finding.paraTo}`
    : `¶${finding.paraFrom}`;
  const parties = finding.arguments.filter((argument) => argument.party !== "court");
  const responses = Array.from(
    new Map(finding.courtResponses.map((response) => [response.response.key, response])).values(),
  );
  const relationshipGroups = ["supports", "qualifies", "contrary", "context"] as const;
  const matrixRows = finding.matrix.rows;
  const witnessRows = matrixRows.filter((row) => row.sourceCategory === "witness_testimony");

  return (
    <AppShell
      crumbs={[{ label: t("findings"), href: "/findings" }, { label: finding.key }]}
      showDemoFlag={false}
    >
      <ScreenHeader
        eyebrow={
          <span className="identifier">
            {finding.key} · {finding.adjudicativeRecord.documentType} · {paraRange}
          </span>
        }
        title={t("title")}
        description={t("realDataNotice")}
        realData
      />
      <div className="mx-auto grid w-full max-w-[1440px] gap-4 p-3 md:p-4 xl:grid-cols-[minmax(0,1fr)_330px]">
        <div className="min-w-0 space-y-4">
          <SectionCard id="court-finding" number="01" title={t("courtFinding")}>
            <RecordBlock
              sourceType="court"
              title={`${finding.adjudicativeRecord.ref} · ${paraRange}`}
            >
              <div className="space-y-3">
                <p className="font-serif whitespace-pre-line">{finding.text}</p>
                <VerificationBadge state={finding.verification} size="sm" />
                <SourceLink source={finding.source} label={t("openExactPassage")} />
              </div>
            </RecordBlock>
          </SectionCard>

          <SectionCard id="structure" number="02" title={t("judgmentStructure")}>
            <p className="text-fg-secondary mb-3 text-[11px]">
              {finding.adjudicativeRecord.title} · {finding.adjudicativeRecord.versionRef}
            </p>
            {finding.adjudicativeRecord.sections.length ? (
              <ul className="mb-3 space-y-1 text-[11px]">
                {finding.adjudicativeRecord.sections.map((section) => (
                  <li key={`${section.heading}-${section.paraFrom}`}>
                    {section.heading}
                    {section.paraFrom ? ` · ¶${section.paraFrom}` : ""}
                  </li>
                ))}
              </ul>
            ) : null}
            <ol className="divide-border-faint divide-y">
              {finding.adjudicativeRecord.paragraphs.map((paragraph) => (
                <li key={paragraph.number} className="grid gap-2 py-3 sm:grid-cols-[50px_1fr]">
                  <span className="identifier text-accent">¶{paragraph.number}</span>
                  <p className="font-serif text-[12px] leading-relaxed">{paragraph.text}</p>
                </li>
              ))}
            </ol>
          </SectionCard>

          <SectionCard id="matrix" number="03" title={t("evidenceMatrix")}>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[680px] text-left text-[11px]">
                <thead className="text-fg-secondary border-border-subtle border-b">
                  <tr>
                    <th className="px-2 py-2">{t("relationship")}</th>
                    <th className="px-2 py-2">{t("sourceCategory")}</th>
                    <th className="px-2 py-2">{t("matrixPassage")}</th>
                    <th className="px-2 py-2">{t("exactSource")}</th>
                    <th className="px-2 py-2">{t("verification")}</th>
                  </tr>
                </thead>
                <tbody className="divide-border-faint divide-y">
                  {matrixRows.map((row) => (
                    <tr key={row.id}>
                      <td className="px-2 py-3">{t(`linkTypes.${row.relation}`)}</td>
                      <td className="px-2 py-3">{t(`sourceCategories.${row.sourceCategory}`)}</td>
                      <td className="px-2 py-3">
                        <p className="line-clamp-3 font-serif">{row.exactText}</p>
                        {row.sourceScope === "court_summary" ? (
                          <p className="text-unresolved mt-1 text-[10px]">
                            {t("courtSummaryPassage")}
                          </p>
                        ) : null}
                      </td>
                      <td className="px-2 py-3">
                        <MatrixSourceLink row={row} />
                      </td>
                      <td className="px-2 py-3">
                        <p className="text-[10px]">{t(`reviewStatuses.${row.reviewStatus}`)}</p>
                        <VerificationBadge state={row.verification} size="sm" />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {matrixRows.length === 0 ? (
              <EmptyState title={t("noExplicitEvidence")} reason={finding.corroborationNote} />
            ) : null}
            <p className="text-fg-secondary mt-3 text-[10px]">
              {t("matrixCoverage", {
                rows: finding.matrix.coverage.rows,
                anchors: finding.matrix.coverage.sourceAnchors,
              })}
            </p>
          </SectionCard>

          <SectionCard id="other-material" number="04" title={t("otherMaterial")}>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {relationshipGroups.map((kind) => {
                const count = finding.evidence.filter((link) => link.linkType === kind).length;
                return (
                  <Panel key={kind} title={t(`linkTypes.${kind}`)}>
                    <span className="identifier text-lg">{count}</span>
                  </Panel>
                );
              })}
            </div>
            <p className="text-fg-secondary mt-3 text-[11px]">{finding.corroborationNote}</p>
          </SectionCard>

          <SectionCard id="party-positions" number="05" title={t("partyPositions")}>
            <div className="grid gap-3 md:grid-cols-2">
              {parties.map((argument) => (
                <RecordBlock
                  key={argument.key}
                  sourceType={argument.party === "spo" ? "spo" : "defence"}
                  title={argument.title}
                >
                  <div className="space-y-3">
                    <p className="font-serif">{argument.text}</p>
                    <p className="text-fg-secondary text-[10px]">
                      {argument.sourceScope === "court_summary"
                        ? t("courtSummaryOnly", {
                            ref: argument.underlyingSourceRef ?? t("unresolved"),
                          })
                        : t("directSource")}
                    </p>
                    <SourceLink source={argument.source} label={t("openExactPassage")} />
                  </div>
                </RecordBlock>
              ))}
            </div>
          </SectionCard>

          <SectionCard id="witness-testimony" number="06" title={t("witnessTestimony")}>
            {witnessRows.length ? (
              <div className="space-y-3">
                {witnessRows.map((row) => (
                  <RecordBlock key={row.id} sourceType="witness" title={row.title}>
                    <p className="font-serif">{row.exactText}</p>
                    <MatrixSourceLink row={row} />
                  </RecordBlock>
                ))}
              </div>
            ) : (
              <EmptyState title={t("noWitnessPassages")} reason={t("noWitnessInference")} />
            )}
          </SectionCard>

          <SectionCard id="court-response" number="07" title={t("courtResponse")}>
            <div className="space-y-3">
              {responses.map((response) => (
                <RecordBlock
                  key={response.response.key}
                  sourceType="court"
                  title={response.response.title}
                >
                  <div className="space-y-3">
                    <p className="font-serif whitespace-pre-line">{response.response.text}</p>
                    <SourceLink source={response.source} label={t("openExactPassage")} />
                  </div>
                </RecordBlock>
              ))}
            </div>
          </SectionCard>

          <SectionCard id="human-notes" number="08" title={t("humanNotes")}>
            {finding.humanNotes.length ? (
              finding.humanNotes.map((note) => (
                <Panel key={`${note.author}-${note.title}`} title={note.title}>
                  <p className="text-[11px]">{note.body}</p>
                  <p className="text-fg-secondary mt-2 text-[10px]">
                    {t("humanNoteBy", { author: note.author })}
                  </p>
                </Panel>
              ))
            ) : (
              <p className="text-fg-secondary text-[11px]">{t("noHumanNotes")}</p>
            )}
          </SectionCard>
        </div>

        <aside className="min-w-0 space-y-4">
          <Panel title={t("recordStatus")}>
            <KeyValue
              rows={[
                {
                  key: "r",
                  label: t("recordType"),
                  value: finding.adjudicativeRecord.documentType,
                },
                {
                  key: "v",
                  label: t("version"),
                  value: finding.adjudicativeRecord.versionRef ?? "—",
                },
                { key: "p", label: t("visibility"), value: finding.adjudicativeRecord.visibility },
                { key: "e", label: t("legalElement"), value: finding.legalElement ?? "—" },
              ]}
            />
          </Panel>
          <Panel title={t("sourceAudit")}>
            <KeyValue
              rows={[
                { key: "t", label: t("citationsTotal"), value: finding.audit.citationsTotal },
                { key: "r", label: t("citationsResolved"), value: finding.audit.citationsResolved },
                {
                  key: "u",
                  label: t("citationsUnresolved"),
                  value: finding.audit.citationsUnresolved,
                },
                { key: "m", label: t("sourcesMissing"), value: finding.audit.sourcesMissing },
                {
                  key: "x",
                  label: t("relationshipsUnverified"),
                  value: finding.audit.relationshipsUnverified,
                },
              ]}
            />
            <ul className="mt-3 space-y-2">
              {finding.audit.issues.map((issue) => (
                <li key={`${issue.code}-${issue.detail}`} className="text-unresolved text-[10px]">
                  {issue.detail}
                </li>
              ))}
            </ul>
          </Panel>
          <Panel title={t("aiAnalysis")}>
            <p className="text-fg-secondary text-[11px]">{t("aiNotGenerated")}</p>
          </Panel>
          <Panel title={t("interpretationLimit")}>
            <p className="text-fg-secondary text-[11px]">{t("noInference")}</p>
          </Panel>
        </aside>
      </div>
    </AppShell>
  );
}
