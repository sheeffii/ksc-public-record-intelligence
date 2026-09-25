"use client";

import type { CitableSourceType } from "@ksc/shared";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { Panel } from "@/components/primitives/Panel";
import { GapNotice } from "@/components/primitives/States";
import {
  AiAnalysisBlock,
  ProvenanceBoundary,
  RecordBlock,
  SourceBadge,
  VerificationBadge,
} from "@/components/provenance";
import { AppShell } from "@/components/shell/AppShell";
import { createApiRepository } from "@/data";
import type {
  AiResearchBlock,
  AiResearchRun,
  AiResearchSource,
  AiRunSummaryView,
} from "@/data/contract";
import { ScreenHeader } from "./ScreenChrome";
import { KeyValue, SectionCard, ToolButton } from "./Workspace";

const SOURCE_TYPE: Record<AiResearchSource["category"], CitableSourceType> = {
  court_finding: "court",
  witness_testimony: "witness",
  spo_argument: "spo",
  defence_argument: "defence",
  document_exhibit: "exhibit",
  court_response: "court",
  human_note: "exhibit",
};

function SourcePreview({ source }: { source: AiResearchSource }) {
  const t = useTranslations("phase11");
  const [open, setOpen] = useState(false);
  return (
    <span className="relative inline-flex">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="rounded-chip border-border bg-surface-raised text-fg inline-flex min-h-7 items-center border px-2 text-[10px] font-semibold"
      >
        {source.display}
      </button>
      {open ? (
        <span
          role="dialog"
          aria-label={source.display}
          className="shadow-palette border-border bg-surface rounded-card absolute top-full left-0 z-30 mt-2 block w-[min(420px,82vw)] border p-3 text-left"
        >
          <strong className="text-fg block text-[11px]">{source.display}</strong>
          <span className="text-fg-secondary my-2 block max-h-52 overflow-auto font-serif text-[11px] leading-relaxed">
            {source.excerpt}
          </span>
          <Link href={source.targetPath} className="text-accent text-[11px] font-semibold">
            {t("openSource")} →
          </Link>
        </span>
      ) : null}
    </span>
  );
}

function SourceFooter({ sources }: { sources: readonly AiResearchSource[] }) {
  return (
    <div className="flex flex-wrap gap-2">
      {sources.map((source) => (
        <SourcePreview key={source.id} source={source} />
      ))}
    </div>
  );
}

function RecordAnswerBlock({ block }: { block: AiResearchBlock }) {
  const t = useTranslations("phase11");
  const source = block.sources[0];
  const sourceType = source ? SOURCE_TYPE[source.category] : "court";
  return (
    <RecordBlock sourceType={sourceType} title={t(`blockKinds.${block.kind}`)}>
      <blockquote className="font-serif leading-relaxed">{block.text}</blockquote>
      <div className="mt-3">
        <SourceFooter sources={block.sources} />
      </div>
    </RecordBlock>
  );
}

export function AiResearchReal({
  initialRun,
  sessions,
  apiBaseUrl,
}: {
  initialRun: AiResearchRun | null;
  sessions: readonly AiRunSummaryView[];
  apiBaseUrl: string;
}) {
  const t = useTranslations("phase11");
  const footer = useTranslations("footer");
  const router = useRouter();
  const [run, setRun] = useState(initialRun);
  const [question, setQuestion] = useState(initialRun?.question ?? "");
  const [loading, setLoading] = useState(false);
  const [requestError, setRequestError] = useState(false);
  const [saved, setSaved] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (loading || question.trim().length < 3) return;
    setLoading(true);
    setRequestError(false);
    setRun(null);
    try {
      const next = await createApiRepository({ baseUrl: apiBaseUrl }).createAiRun(question);
      setRun(next);
      router.push(`/ai/${next.id}`);
    } catch {
      setRequestError(true);
    } finally {
      setLoading(false);
    }
  }

  async function saveNote() {
    if (!run || run.answerWithheld) return;
    await createApiRepository({ baseUrl: apiBaseUrl }).saveAiRunAsNote(
      run.id,
      `${t("noteTitle")}: ${run.question}`,
    );
    setSaved(true);
  }

  const recordBlocks = run?.blocks.filter((block) => block.kind !== "ai") ?? [];
  const aiBlocks = run?.blocks.filter((block) => block.kind === "ai") ?? [];
  return (
    <AppShell footer={footer("sourceNote")} showDemoFlag={false}>
      <ScreenHeader
        eyebrow={t("eyebrow")}
        title={t("title")}
        description={t("description")}
        realData
      />
      <div className="mx-auto grid w-full max-w-[1440px] min-w-0 flex-1 gap-3 p-3 md:p-4 lg:grid-cols-[214px_minmax(0,1fr)] xl:grid-cols-[214px_minmax(0,1fr)_292px]">
        <aside className="min-w-0 space-y-3">
          <Panel title={t("sessions")}>
            <ul className="max-h-[calc(100dvh-310px)] space-y-2 overflow-y-auto pr-1 text-[11px]">
              {sessions.map((session) => (
                <li key={session.id}>
                  <Link href={`/ai/${session.id}`} className="text-accent line-clamp-2">
                    {session.question}
                  </Link>
                  <span className="text-fg-muted block text-[10px]">
                    {session.createdAt.slice(0, 10)}
                  </span>
                </li>
              ))}
            </ul>
            <div className="mt-3">
              <ToolButton href="/ai">{t("newQuestion")}</ToolButton>
            </div>
          </Panel>
          <Panel title={t("scope")}>
            <span className="rounded-badge bg-surface-raised px-1.5 py-0.5 text-[10px]">
              {t("controlledCorpus")}
            </span>
          </Panel>
        </aside>

        <div className="min-w-0 space-y-3">
          <form onSubmit={submit} className="flex flex-wrap gap-2">
            <label className="sr-only" htmlFor="ai-question">
              {t("questionLabel")}
            </label>
            <input
              id="ai-question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder={t("questionPlaceholder")}
              className="border-border bg-surface text-fg rounded-inset h-11 min-w-[240px] flex-1 border px-4 text-[13px]"
            />
            <button
              type="submit"
              disabled={loading || question.trim().length < 3}
              className="rounded-control border-accent bg-accent text-bg-deep h-11 min-w-24 border px-4 text-[11px] font-semibold disabled:opacity-50"
            >
              {loading ? t("retrieving") : t("ask")}
            </button>
          </form>

          {requestError ? (
            <GapNotice
              kind="unresolved-citation"
              reference={t("systemGap")}
              extent={t("noAnswerExtent")}
              reason={t("requestFailed")}
            />
          ) : null}

          {loading ? (
            <SectionCard title={t("retrievedSources")}>
              <p className="text-fg-secondary text-[11px]">{t("sourcesBeforeAnswer")}</p>
            </SectionCard>
          ) : null}

          {run ? (
            <>
              <SectionCard
                title={t("retrievedSources")}
                aside={
                  <span className="text-fg-muted tabular text-[10px]">{run.sources.length}</span>
                }
              >
                <ul className="space-y-2">
                  {run.sources.map((source) => (
                    <li key={source.id} className="flex flex-wrap items-center gap-2">
                      <SourceBadge type={SOURCE_TYPE[source.category]} size="sm" />
                      <span className="text-fg text-[10px] font-semibold">
                        {t(`categories.${source.category}`)}
                      </span>
                      <SourcePreview source={source} />
                      <VerificationBadge state={source.verification} size="sm" />
                      {source.sourceScope === "court_summary" ? (
                        <span className="text-fg-muted text-[10px]">
                          {t("courtSummaryMissing", { ref: source.underlyingSourceRef ?? "—" })}
                        </span>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </SectionCard>

              {run.answerWithheld ? (
                <Panel title={t("answerWithheld")}>
                  <p className="text-fg-body text-[12px]">{t("withheldBody")}</p>
                  <div className="mt-3 space-y-2">
                    {run.gaps.map((gap) => (
                      <GapNotice
                        key={gap}
                        kind="unresolved-citation"
                        reference={t("controlledCorpus")}
                        extent={t("noAnswerExtent")}
                        reason={gap}
                      />
                    ))}
                  </div>
                </Panel>
              ) : (
                <>
                  {recordBlocks.map((block) => (
                    <RecordAnswerBlock key={block.id} block={block} />
                  ))}
                  <ProvenanceBoundary />
                  {aiBlocks.map((block) => (
                    <AiAnalysisBlock key={block.id} title={t("blockKinds.ai")}>
                      <p>{block.text}</p>
                      <div className="mt-3">
                        <SourceFooter sources={block.sources} />
                      </div>
                    </AiAnalysisBlock>
                  ))}
                  <div className="flex flex-wrap gap-2">
                    <ToolButton onClick={saveNote}>
                      {saved ? t("noteSaved") : t("saveNote")}
                    </ToolButton>
                    <ToolButton href="/network">{t("viewGraph")}</ToolButton>
                  </div>
                </>
              )}
            </>
          ) : !loading ? (
            <Panel title={t("emptyTitle")}>
              <p className="text-fg-secondary text-[12px]">{t("emptyBody")}</p>
            </Panel>
          ) : null}
        </div>

        <aside className="min-w-0 space-y-3 lg:col-span-2 xl:col-span-1">
          <Panel title={t("citationStatus")}>
            <KeyValue
              rows={[
                { key: "p", label: t("produced"), value: run?.citationStatus.produced ?? 0 },
                { key: "r", label: t("resolved"), value: run?.citationStatus.resolved ?? 0 },
                {
                  key: "q",
                  label: t("quotesMatched"),
                  value: run?.citationStatus.quotationsMatched ?? 0,
                },
                { key: "u", label: t("unresolved"), value: run?.citationStatus.unresolved ?? 0 },
              ]}
            />
          </Panel>
          <Panel title={t("runAudit")}>
            <KeyValue
              rows={[
                { key: "provider", label: t("provider"), value: run?.provider ?? "—" },
                { key: "model", label: t("model"), value: run?.model ?? "—" },
                { key: "prompt", label: t("promptVersion"), value: run?.promptVersion ?? "—" },
              ]}
            />
          </Panel>
          <Panel title={t("knownGaps")}>
            <p className="text-fg-secondary text-[11px]">{t("knownGapsBody")}</p>
          </Panel>
        </aside>
      </div>
    </AppShell>
  );
}
