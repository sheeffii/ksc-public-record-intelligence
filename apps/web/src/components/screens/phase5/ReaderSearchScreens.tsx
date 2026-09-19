"use client";

import { useTranslations } from "next-intl";
import Link from "next/link";
import { useMemo, useState } from "react";
import { Panel } from "@/components/primitives/Panel";
import {
  AiAnalysisBlock,
  CitationChip,
  ProvenanceBoundary,
  RecordBlock,
  SourceBadge,
  VerificationBadge,
} from "@/components/provenance";
import { AppShell } from "@/components/shell/AppShell";
import { courtCitation, mockRepository, transcriptCitation } from "@/mock";
import { ActionLink, DemoNotice, ScreenHeader, WorkspaceGrid } from "./ScreenChrome";

export function DocumentReaderScreen({ id }: { id: string }) {
  const t = useTranslations("phase5");
  const footer = useTranslations("footer");
  const document = mockRepository.getDocument(id);
  const transcript = id.startsWith("T-");
  return (
    <AppShell
      mode="light"
      crumbs={[{ label: document.type }, { label: id }]}
      footer={footer("sourceNote")}
    >
      <ScreenHeader
        eyebrow={document.type}
        title={document.title}
        description={`${id} · ${document.language}`}
        actions={
          <>
            <button
              type="button"
              className="border-border bg-surface-raised text-fg rounded-control h-8 border px-3 text-[11px]"
            >
              {t("copyCitation")}
            </button>
            <ActionLink href="/findings/F-DEMO-01">{t("courtFindings")}</ActionLink>
          </>
        }
      />
      <div className="grid min-h-[720px] min-w-0 flex-1 lg:grid-cols-[240px_minmax(0,1fr)_300px]">
        <aside className="border-border bg-surface-alt border-b p-3 lg:border-r lg:border-b-0">
          <details open className="group">
            <summary className="text-fg mb-3 cursor-pointer text-[11px] font-semibold lg:hidden">
              {t("metadata")} · {t("documentStructure")}
            </summary>
            <Panel title={t("metadata")}>
              <dl className="grid grid-cols-2 gap-2 text-[11px]">
                <dt className="section-label">ID</dt>
                <dd className="identifier">{id}</dd>
                <dt className="section-label">{t("page")}</dt>
                <dd>{document.page}</dd>
                <dt className="section-label">{t("documentStructure")}</dt>
                <dd>3</dd>
              </dl>
            </Panel>
            <Panel className="mt-3" title={t("documentStructure")}>
              <nav className="space-y-1">
                {document.paragraphs.map((p) => (
                  <a
                    key={p.number}
                    href={`#para-${p.number}`}
                    className="text-accent block text-[11px]"
                  >
                    ¶{p.number}
                  </a>
                ))}
              </nav>
            </Panel>
          </details>
        </aside>
        <main className="bg-bg flex min-w-0 justify-center overflow-auto p-4 md:p-8">
          <article className="shadow-page bg-surface text-fg-body min-h-[760px] w-full max-w-[600px] px-6 py-8 md:px-[60px] md:py-[52px]">
            <div className="border-border-faint text-fg-muted mb-8 flex justify-between border-b pb-2 text-[9px] uppercase">
              <span>{document.title}</span>
              <span>
                {t("page")} {document.page}
              </span>
            </div>
            <div className="border-demo-border bg-demo-bg rounded-card mb-5 border px-3 py-2 text-[10px]">
              {t("mockNotice")}
            </div>
            {transcript ? (
              <TranscriptPage />
            ) : (
              document.paragraphs.map((paragraph) => (
                <p
                  id={`para-${paragraph.number}`}
                  key={paragraph.number}
                  className="mb-5 scroll-mt-24 font-serif text-[12.5px] leading-[1.75]"
                >
                  <a
                    href={`#para-${paragraph.number}`}
                    className="text-court mr-3 font-sans text-[10px] font-semibold"
                  >
                    ¶{paragraph.number}
                  </a>
                  {paragraph.text}
                </p>
              ))
            )}
            <div className="border-doc bg-doc-bg rounded-card mt-8 border px-3 py-2 text-[11px]">
              <SourceBadge type="court" />{" "}
              <Link href="/findings/F-DEMO-01" className="text-doc ml-2 font-semibold">
                {t("courtFindings")} · F-DEMO-01 →
              </Link>
            </div>
          </article>
        </main>
        <aside className="border-border bg-surface-alt border-t p-3 lg:border-t-0 lg:border-l">
          <details open>
            <summary className="text-fg mb-3 cursor-pointer text-[11px] font-semibold lg:hidden">
              {t("researchContext")}
            </summary>
            <Panel title={t("researchContext")}>
              <div className="space-y-3">
                <RecordBlock sourceType="court" citations={[courtCitation]}>
                  Generic context from the record.
                </RecordBlock>
                <ProvenanceBoundary />
                <AiAnalysisBlock citations={[courtCitation]}>
                  Mock summary for interface demonstration only.
                </AiAnalysisBlock>
              </div>
            </Panel>
            <Panel className="mt-3" title={t("sourcesUsed")}>
              <CitationChip citation={document.citation} />
            </Panel>
          </details>
        </aside>
      </div>
    </AppShell>
  );
}

function TranscriptPage() {
  const t = useTranslations("phase5");
  return (
    <div className="font-serif text-[11.5px] leading-[1.85]">
      <div className="mb-3 font-sans">
        <SourceBadge type="witness" />
        <span className="text-fg-muted ml-2">{t("examination")}</span>
      </div>
      {[
        [12, "COUNSEL:", `${t("question")}: Generic sample question.`],
        [15, "W01234:", `${t("answer")}: Generic sample answer.`],
        [18, "COUNSEL:", `${t("question")}: Follow-up sample question.`],
      ].map(([line, speaker, text]) => (
        <div key={String(line)} className="grid grid-cols-[28px_82px_1fr] gap-2">
          <span className="tabular text-fg-muted">{line}</span>
          <strong className="font-sans text-[10px]">{speaker}</strong>
          <span>{text}</span>
        </div>
      ))}
      <div className="mt-4 flex gap-2">
        <CitationChip citation={transcriptCitation} />
        <button type="button" className="text-accent text-[10px]">
          {t("addNote")}
        </button>
      </div>
    </div>
  );
}

export function SearchScreen({ initialQuery = "" }: { initialQuery?: string }) {
  const t = useTranslations("phase5");
  const footer = useTranslations("footer");
  const [query, setQuery] = useState(initialQuery);
  const results = useMemo(() => mockRepository.search(query), [query]);
  const groups = Map.groupBy(results, (result) => result.category);
  return (
    <AppShell footer={footer("sourceNote")}>
      <ScreenHeader
        eyebrow={t("search")}
        title={t("searchRecords")}
        description={t("resultOrdering")}
      />
      <WorkspaceGrid
        left={
          <Panel title={t("filter")}>
            <div className="space-y-2">
              {[
                "people",
                "witnesses",
                "documents",
                "exhibits",
                "incidents",
                "findings",
                "locations",
              ].map((item) => (
                <label key={item} className="flex items-center gap-2 text-[11px]">
                  <input type="checkbox" defaultChecked />
                  {item}
                </label>
              ))}
            </div>
          </Panel>
        }
        right={
          <Panel title={t("queryInterpretation")}>
            <p className="text-fg text-[12px] font-semibold">{query || t("allRecords")}</p>
            <p className="text-fg-secondary mt-2 text-[11px]">{t("searchedVariants")}</p>
          </Panel>
        }
      >
        <div className="space-y-4">
          <DemoNotice />
          <label>
            <span className="sr-only">{t("searchRecords")}</span>
            <input
              autoFocus
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={t("commandHint")}
              className="border-border bg-surface text-fg rounded-inset h-11 w-full border px-4 text-[13px]"
            />
          </label>
          {[...groups.entries()].map(([category, rows]) => (
            <Panel key={category} title={`${category} · ${rows.length}`} padded={false}>
              {rows.map((result) => (
                <Link
                  key={result.id}
                  href={result.href}
                  className="border-border-faint hover:bg-surface-raised block border-b px-3 py-3"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <span className="text-fg text-[12px] font-semibold">{result.title}</span>
                      <p className="text-fg-secondary mt-1 text-[11px]">{result.context}</p>
                    </div>
                    {result.citation ? (
                      <CitationChip citation={result.citation} navigable={false} />
                    ) : null}
                  </div>
                </Link>
              ))}
            </Panel>
          ))}
        </div>
      </WorkspaceGrid>
    </AppShell>
  );
}

export function StatementComparisonScreen({ code }: { code: string }) {
  const t = useTranslations("phase5");
  const footer = useTranslations("footer");
  const columns = [
    {
      label: t("priorStatements"),
      text: "The earlier sample statement does not address the final time period.",
      citation: courtCitation,
    },
    {
      label: t("testimony"),
      text: "The sample testimony describes a narrower time period.",
      citation: transcriptCitation,
    },
    {
      label: t("crossExamination"),
      text: "The sample cross-examination asks about the difference in timing.",
      citation: transcriptCitation,
    },
  ];
  return (
    <AppShell
      crumbs={[{ label: code }, { label: t("statementComparison") }]}
      footer={footer("neutrality")}
    >
      <ScreenHeader
        eyebrow={code}
        title={t("statementComparison")}
        description={t("comparisonNeutral")}
        actions={<VerificationBadge state="ai-flagged" />}
      />
      <WorkspaceGrid
        left={
          <Panel title={t("results")}>
            <button className="text-accent text-[11px]">{t("timelineDifference")}</button>
          </Panel>
        }
        right={
          <Panel title={t("humanReview")}>
            <div className="space-y-2">
              {[
                "possibleContradiction",
                "qualification",
                "timelineDifference",
                "consistent",
                "notComparable",
              ].map((key) => (
                <button
                  key={key}
                  className="border-border bg-surface-raised text-fg rounded-control block w-full border px-2 py-1.5 text-left text-[10px]"
                >
                  {t(key)}
                </button>
              ))}
            </div>
          </Panel>
        }
      >
        <div className="space-y-4">
          <DemoNotice />
          <div className="grid gap-3 lg:grid-cols-3">
            {columns.map((column) => (
              <RecordBlock
                key={column.label}
                sourceType="witness"
                title={column.label}
                citations={[column.citation]}
              >
                <p className="font-serif">{column.text}</p>
              </RecordBlock>
            ))}
          </div>
          <ProvenanceBoundary />
          <AiAnalysisBlock
            title={t("neutralReview")}
            citations={[courtCitation, transcriptCitation]}
          >
            The wording differs in temporal scope. A human reviewer must decide whether the passages
            are comparable.
          </AiAnalysisBlock>
        </div>
      </WorkspaceGrid>
    </AppShell>
  );
}
