"use client";

import type { AnswerBlockKind, SourceType } from "@ksc/shared";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useState } from "react";
import { Panel } from "@/components/primitives/Panel";
import { EmptyState, GapNotice } from "@/components/primitives/States";
import {
  AiAnalysisBlock,
  CitationChip,
  CitationPreview,
  ProvenanceBoundary,
  RecordBlock,
  SourceBadge,
  VerificationBadge,
} from "@/components/provenance";
import { AppShell } from "@/components/shell/AppShell";
import { courtCitation, exhibitCitation, mockRepository, transcriptCitation } from "@/mock";
import { ActionLink, DemoNotice, ScreenHeader } from "./ScreenChrome";
import {
  KeyValue,
  NoteStrip,
  SectionCard,
  Segmented,
  Stepper,
  ToolButton,
  Toolbar,
} from "./Workspace";

const sourceForAnswer: Record<
  Exclude<AnswerBlockKind, "ai">,
  Exclude<SourceType, "ai" | "incident" | "location" | "organisation">
> = {
  court: "court",
  evidence: "exhibit",
  testimony: "witness",
  spo: "spo",
  defence: "defence",
  court_response: "court",
  human_note: "exhibit",
};

// -------------------------------------------------------------- appeal ----

const CATEGORIES = [
  "evidence",
  "law",
  "fact",
  "reasoning",
  "liability",
  "procedure",
  "sentencing",
  "other",
] as const;
type Category = (typeof CATEGORIES)[number];
type ReviewState = "kept" | "dismissed" | "awaiting";
const ISSUES: readonly { id: string; category: Category; title: string; paras: string }[] = [
  {
    id: "ISS-DEMO-01",
    category: "evidence",
    title: "Extent of the passage relied upon (demo)",
    paras: "¶45–46",
  },
  {
    id: "ISS-DEMO-02",
    category: "reasoning",
    title: "Treatment of a qualifying passage (demo)",
    paras: "¶120",
  },
  {
    id: "ISS-DEMO-03",
    category: "evidence",
    title: "Closed-session material not in the public record (demo)",
    paras: "¶131",
  },
];

export function AppealScreen() {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const [category, setCategory] = useState<Category | "all">("all");
  const [expanded, setExpanded] = useState<string | null>(ISSUES[0]!.id);
  const [review, setReview] = useState<Record<string, ReviewState>>({});
  const issues = ISSUES.filter((i) => category === "all" || i.category === category);
  const state = (id: string) => review[id] ?? "awaiting";
  return (
    <AppShell footer={t("noPrediction")}>
      <ScreenHeader
        eyebrow={t("appealReview")}
        title={t("potentialIssues")}
        description={tb("legalStrip")}
      />
      <div className="mx-auto grid w-full max-w-[1440px] min-w-0 flex-1 gap-3 p-3 md:p-4 lg:grid-cols-[236px_minmax(0,1fr)] xl:grid-cols-[236px_minmax(0,1fr)_276px]">
        <aside className="min-w-0 space-y-3">
          <Panel title={t("issueCategories")}>
            <label className="lg:hidden">
              <span className="sr-only">{t("issueCategories")}</span>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value as Category | "all")}
                className="border-border bg-surface-raised rounded-control h-8 w-full border px-2 text-[11px]"
              >
                <option value="all">{tb("allCategories")}</option>
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {tb(`categories.${c}`)}
                  </option>
                ))}
              </select>
            </label>
            <ul className="hidden space-y-0.5 lg:block">
              {[
                { key: "all", label: tb("allCategories") },
                ...CATEGORIES.map((c) => ({ key: c, label: tb(`categories.${c}`) })),
              ].map((c) => (
                <li key={c.key}>
                  <button
                    type="button"
                    onClick={() => setCategory(c.key as Category | "all")}
                    aria-current={category === c.key ? "true" : undefined}
                    className={`rounded-control flex w-full justify-between px-2 py-1 text-[11px] ${category === c.key ? "bg-surface-high text-fg" : "text-fg-secondary"}`}
                  >
                    <span>{c.label}</span>
                    <span className="tabular text-fg-muted">
                      {c.key === "all"
                        ? ISSUES.length
                        : ISSUES.filter((i) => i.category === c.key).length}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </Panel>
          <Panel title={tb("reviewState")}>
            <KeyValue
              rows={(["kept", "dismissed", "awaiting"] as const).map((s) => ({
                key: s,
                label: tb(`reviewStates.${s}`),
                value: ISSUES.filter((i) => state(i.id) === s).length,
              }))}
            />
          </Panel>
        </aside>
        <div className="min-w-0 space-y-3">
          <DemoNotice />
          {issues.length === 0 ? (
            <EmptyState
              title={tb("emptyCategory")}
              reason={tb("emptyCategoryReason")}
              action={
                <ToolButton onClick={() => setCategory("all")}>{tb("allCategories")}</ToolButton>
              }
            />
          ) : null}
          {issues.map((issue) => {
            const open = expanded === issue.id;
            return (
              <SectionCard
                key={issue.id}
                title={
                  <span>
                    <span className="identifier text-fg-muted mr-2 text-[10px]">
                      {issue.id} · {issue.paras}
                    </span>
                    {issue.title}
                  </span>
                }
                aside={
                  <div className="flex items-center gap-2">
                    <span className="rounded-badge bg-surface-raised px-1.5 py-0.5 text-[10px]">
                      {tb(`categories.${issue.category}`)}
                    </span>
                    <span className="rounded-badge bg-surface-raised px-1.5 py-0.5 text-[10px]">
                      {tb(`reviewStates.${state(issue.id)}`)}
                    </span>
                    <ToolButton onClick={() => setExpanded(open ? null : issue.id)}>
                      {open ? tb("collapseIssue") : tb("expandIssue")}
                    </ToolButton>
                  </div>
                }
              >
                {open ? (
                  <div className="space-y-3">
                    <RecordBlock
                      sourceType="court"
                      title={tb("issueSections.reasoning")}
                      citations={[courtCitation]}
                    >
                      <p className="font-serif">
                        “Generic demo wording of the reasoning at issue, quoted verbatim.”
                      </p>
                    </RecordBlock>
                    <div className="grid gap-3 md:grid-cols-2">
                      <RecordBlock
                        sourceType="defence"
                        title={tb("issueSections.defence")}
                        citations={[courtCitation]}
                      >
                        Demo defence position at trial.
                      </RecordBlock>
                      <RecordBlock
                        sourceType="spo"
                        title={tb("issueSections.spo")}
                        citations={[courtCitation]}
                      >
                        Demo SPO position at trial.
                      </RecordBlock>
                    </div>
                    <div>
                      <h3 className="section-label mb-1">{tb("issueSections.relied")}</h3>
                      <div className="flex flex-wrap gap-2">
                        <CitationChip citation={transcriptCitation} size="sm" />
                        <CitationChip citation={exhibitCitation} size="sm" />
                      </div>
                    </div>
                    <div>
                      <h3 className="section-label mb-1">{tb("issueSections.contrary")}</h3>
                      <ul className="space-y-1 text-[11px]">
                        {mockRepository
                          .getEvidence()
                          .filter((e) => e.direction !== "supports")
                          .map((e) => (
                            <li key={e.id} className="flex flex-wrap items-center gap-2">
                              <SourceBadge type={e.sourceType} size="sm" />
                              <span className="min-w-0 flex-1">{e.claim}</span>
                              <CitationChip citation={e.citation} size="sm" />
                            </li>
                          ))}
                      </ul>
                    </div>
                    <div>
                      <h3 className="section-label mb-1">{tb("issueSections.missing")}</h3>
                      <GapNotice
                        kind="closed-session"
                        reference="T. 32–40"
                        extent="9 pages"
                        reason={t("missingMaterial")}
                      />
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <ToolButton
                        primary
                        onClick={() => setReview((r) => ({ ...r, [issue.id]: "kept" }))}
                      >
                        {tb("markReviewedIssue")}
                      </ToolButton>
                      <ToolButton
                        onClick={() => setReview((r) => ({ ...r, [issue.id]: "dismissed" }))}
                      >
                        {tb("dismissWithNote")}
                      </ToolButton>
                      <ActionLink href="/appeal/argument/new">{t("sendToLab")}</ActionLink>
                    </div>
                  </div>
                ) : (
                  <p className="text-fg-secondary text-[11px]">
                    {tb("issueSections.reasoning")} · {tb("issueSections.relied")} ·{" "}
                    {tb("issueSections.contrary")}
                  </p>
                )}
              </SectionCard>
            );
          })}
          <NoteStrip tone="legal">{tb("legalStrip")}</NoteStrip>
        </div>
        <aside className="min-w-0 space-y-3 lg:col-span-2 xl:col-span-1">
          <Panel title={tb("coverage")}>
            <KeyValue
              rows={[
                { key: "p", label: tb("paragraphsIndexed"), value: 140 },
                { key: "f", label: tb("findingsExtracted"), value: 2 },
                { key: "c", label: t("citationStatus"), value: 4 },
                { key: "u", label: tb("unresolvedCount"), value: 0 },
              ]}
            />
          </Panel>
          <Panel title={tb("willNotDo")}>
            <ul className="text-fg-secondary list-disc space-y-1 pl-4 text-[11px]">
              <li>{tb("willNot1")}</li>
              <li>{tb("willNot2")}</li>
              <li>{tb("willNot3")}</li>
            </ul>
            <p className="text-fg mt-2 text-[11px]">{t("noPrediction")}</p>
          </Panel>
          <Panel title={tb("appealStatus")}>
            <KeyValue
              rows={[
                { key: "s", label: tb("appealStatus"), value: "demo" },
                {
                  key: "n",
                  label: tb("noticeRef"),
                  value: <span className="identifier">F-DEMO-NOTICE</span>,
                },
                { key: "o", label: tb("orders"), value: 0 },
              ]}
            />
          </Panel>
        </aside>
      </div>
    </AppShell>
  );
}

// --------------------------------------------------------- argument lab ---

const ACTIONS = [
  "researchSupport",
  "findContrary",
  "checkCitations",
  "findDefence",
  "findSpo",
  "findCourt",
] as const;
const STAGES = ["defenceAnalyst", "spoRedTeam", "neutralReviewer"] as const;
const NEUTRAL = [
  "unsupported",
  "missing",
  "ignored",
  "unanswered",
  "factual",
  "legal",
  "supported",
  "human",
] as const;

export function ArgumentLabScreen({ id }: { id: string }) {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const [draft, setDraft] = useState(
    "The demo passage supports the point as stated [F01234 · ¶45–46]. A second sentence has no citation yet.",
  );
  const [stage, setStage] = useState<(typeof STAGES)[number]>("defenceAnalyst");
  const [run, setRun] = useState<Set<string>>(new Set(["defenceAnalyst"]));
  const sentences = draft.split(/(?<=\.)\s+/).filter(Boolean);
  const unsupported = sentences.filter((s) => !/\[.+\]/.test(s));
  const words = draft.trim().split(/\s+/).filter(Boolean).length;
  return (
    <AppShell
      footer={tb("reviewerNote")}
      crumbs={[{ label: t("appealReview"), href: "/appeal" }, { label: id }]}
    >
      <ScreenHeader
        eyebrow={t("appealReview")}
        title={t("argumentEditor")}
        description={tb("draftStatus", { time: "2026-09-20 10:00" })}
        actions={
          <>
            <span className="tabular text-fg-muted text-[10px]">
              {tb("wordCount", { n: words })}
            </span>
            <ToolButton onClick={() => setRun(new Set(STAGES))} primary>
              {tb("redTeamThis")}
            </ToolButton>
          </>
        }
      />
      <div className="mx-auto grid w-full max-w-[1440px] min-w-0 gap-3 p-3 md:p-4 lg:grid-cols-[minmax(0,1fr)_292px]">
        <div className="min-w-0 space-y-3">
          <DemoNotice />
          <SectionCard
            title={t("argumentEditor")}
            aside={<span className="text-fg-muted text-[10px]">{tb("editorNote")}</span>}
          >
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              aria-label={t("argumentEditor")}
              rows={7}
              className="border-border bg-surface text-fg rounded-control w-full border p-3 font-serif text-[13px] leading-relaxed"
            />
            <ol className="mt-2 space-y-1 text-[11px]">
              {sentences.map((s, i) => (
                <li
                  key={i}
                  className={`flex flex-wrap items-center gap-2 ${/\[.+\]/.test(s) ? "" : "border-incident border-l-2 pl-2"}`}
                >
                  <span className="min-w-0 flex-1">{s}</span>
                  {/\[.+\]/.test(s) ? (
                    <CitationChip citation={courtCitation} size="sm" />
                  ) : (
                    <span className="text-incident text-[10px]">{tb("unsupportedSpan")}</span>
                  )}
                </li>
              ))}
            </ol>
          </SectionCard>
        </div>
        <aside className="min-w-0 space-y-3">
          <Panel title={tb("citationHealth")}>
            <KeyValue
              rows={[
                {
                  key: "c",
                  label: tb("health.citations"),
                  value: sentences.length - unsupported.length,
                },
                {
                  key: "r",
                  label: tb("health.resolving"),
                  value: sentences.length - unsupported.length,
                },
                { key: "q", label: tb("health.quotation"), value: 1 },
                { key: "u", label: tb("health.unsupportedSentences"), value: unsupported.length },
              ]}
            />
            {sentences.length - unsupported.length === 0 ? (
              <p className="text-fg-secondary mt-2 text-[11px]">{tb("noCitationsYet")}</p>
            ) : null}
          </Panel>
          <Panel title={t("actions")}>
            <div className="flex flex-col gap-1">
              {ACTIONS.map((a) => (
                <ToolButton key={a} onClick={() => undefined}>
                  {t(a)}
                </ToolButton>
              ))}
              <ToolButton onClick={() => setRun(new Set(STAGES))}>{tb("redTeamThis")}</ToolButton>
              <ToolButton
                onClick={() => {
                  setRun((r) => new Set([...r, "neutralReviewer"]));
                  setStage("neutralReviewer");
                }}
              >
                {tb("generateNeutral")}
              </ToolButton>
            </div>
          </Panel>
        </aside>
      </div>
      <div className="mx-auto w-full max-w-[1440px] min-w-0 space-y-3 px-3 pb-4 md:px-4">
        <Toolbar className="rounded-card border">
          <Stepper
            label={tb("stages")}
            active={stage}
            steps={STAGES.map((s) => ({
              key: s,
              label: t(s),
              state: tb(`stageState.${run.has(s) ? "done" : "idle"}`),
            }))}
          />
          <div className="ml-auto flex gap-2">
            <ToolButton onClick={() => setRun((r) => new Set([...r, stage]))}>
              {tb("rerun")}
            </ToolButton>
            <ToolButton onClick={() => undefined}>{tb("compareStages")}</ToolButton>
          </div>
        </Toolbar>
        <div className="md:hidden">
          <Segmented
            label={tb("stages")}
            value={stage}
            onChange={setStage}
            options={STAGES.map((s) => ({ key: s, label: t(s) }))}
          />
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          {STAGES.map((s) => (
            <div key={s} className={s === stage ? "" : "max-md:hidden"}>
              <SectionCard
                title={t(s)}
                aside={
                  <span className="text-fg-muted text-[10px]">
                    {tb(`stageState.${run.has(s) ? "done" : "idle"}`)}
                  </span>
                }
              >
                {!run.has(s) ? (
                  <p className="text-fg-secondary text-[11px]">{tb("stageState.idle")}</p>
                ) : s === "neutralReviewer" ? (
                  <ul className="space-y-2">
                    {NEUTRAL.slice(0, 4).map((n, i) => (
                      <li key={n} className="text-[11px]">
                        <span className="rounded-badge bg-surface-raised mr-2 px-1.5 py-0.5 text-[10px]">
                          {tb(`neutralCategories.${n}`)}
                        </span>
                        {i === 0 ? (unsupported[0] ?? "—") : "Demo gap between draft and record."}
                        <div className="mt-1 flex items-center gap-2">
                          <CitationChip
                            citation={i % 2 ? exhibitCitation : transcriptCitation}
                            size="sm"
                          />
                          <ToolButton
                            onClick={() =>
                              setDraft(
                                (d) =>
                                  `${d} [${(i % 2 ? exhibitCitation : transcriptCitation).display}]`,
                              )
                            }
                          >
                            {tb("apply")}
                          </ToolButton>
                        </div>
                      </li>
                    ))}
                    <li className="text-[11px]">
                      <span className="rounded-badge bg-surface-raised mr-2 px-1.5 py-0.5 text-[10px]">
                        {tb("neutralCategories.legal")}
                      </span>
                      {t("legalDecline")}
                    </li>
                  </ul>
                ) : (
                  <AiAnalysisBlock
                    citations={[s === "defenceAnalyst" ? transcriptCitation : courtCitation]}
                    previewCitations
                  >
                    {s === "defenceAnalyst"
                      ? "Demo counter-reading of the cited passage; cited, not asserted."
                      : "Demo response pointing to the paragraph the Panel relied on."}
                  </AiAnalysisBlock>
                )}
              </SectionCard>
            </div>
          ))}
        </div>
        <NoteStrip tone="legal">{tb("reviewerNote")}</NoteStrip>
      </div>
    </AppShell>
  );
}

// -------------------------------------------------------------- ai ---------

export function AiResearchScreen() {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const footer = useTranslations("footer");
  const answer = mockRepository.getAnswer();
  const sources = [courtCitation, exhibitCitation, transcriptCitation];
  const [question, setQuestion] = useState("Which demo sources address the illustrative event?");
  return (
    <AppShell footer={footer("sourceNote")}>
      <ScreenHeader eyebrow={t("askAi")} title={t("askAi")} description={tb("retrievedFirst")} />
      <div className="mx-auto grid w-full max-w-[1440px] min-w-0 flex-1 gap-3 p-3 md:p-4 lg:grid-cols-[214px_minmax(0,1fr)] xl:grid-cols-[214px_minmax(0,1fr)_292px]">
        <aside className="min-w-0 space-y-3">
          <Panel title={tb("sessions")}>
            <ul className="space-y-1 text-[11px]">
              <li>
                <Link href="/ai/session-1" className="text-accent">
                  session-1
                </Link>
                <span className="text-fg-muted block text-[10px]">2026-09-20</span>
              </li>
            </ul>
            <div className="mt-2">
              <ActionLink href="/ai">{tb("newSession")}</ActionLink>
            </div>
          </Panel>
          <Panel title={tb("scope")}>
            <span className="rounded-badge bg-surface-raised px-1.5 py-0.5 text-[10px]">
              {tb("wholeRecord")}
            </span>
          </Panel>
        </aside>
        <div className="min-w-0 space-y-3">
          <form onSubmit={(e) => e.preventDefault()} className="flex flex-wrap gap-2">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              aria-label={tb("askPlaceholder")}
              placeholder={tb("askPlaceholder")}
              className="border-border bg-surface text-fg rounded-inset h-11 min-w-[240px] flex-1 border px-4 text-[13px]"
            />
            <ToolButton primary onClick={() => undefined}>
              {t("askAi")}
            </ToolButton>
          </form>
          <DemoNotice />
          <SectionCard
            title={t("retrievedDocuments")}
            aside={<span className="tabular text-fg-muted text-[10px]">{sources.length}</span>}
          >
            <ul className="flex flex-wrap gap-2">
              {sources.map((c) => (
                <li key={c.display} className="flex items-center gap-1">
                  <SourceBadge type={c.sourceType} size="sm" />
                  <CitationChip citation={c} size="sm" />
                </li>
              ))}
            </ul>
          </SectionCard>
          {answer
            .filter((b) => b.kind !== "ai")
            .map((block) => (
              <RecordBlock
                key={block.kind}
                sourceType={sourceForAnswer[block.kind as Exclude<AnswerBlockKind, "ai">]}
                previewCitations
                citations={block.citations}
              >
                {block.text}
              </RecordBlock>
            ))}
          <ProvenanceBoundary />
          {answer
            .filter((b) => b.kind === "ai")
            .map((block) => (
              <AiAnalysisBlock key={block.kind} previewCitations citations={block.citations}>
                {block.text}
              </AiAnalysisBlock>
            ))}
          <div className="flex flex-wrap gap-2">
            <ActionLink href="/documents/F01234">{t("openAllSources")}</ActionLink>
            <ActionLink href="/network">{t("viewEvidenceGraph")}</ActionLink>
            <ActionLink href="/appeal/argument/new">{t("saveNote")}</ActionLink>
            <ActionLink href="/appeal/argument/new" primary>
              {t("createArgument")}
            </ActionLink>
          </div>
        </div>
        <aside className="min-w-0 space-y-3 lg:col-span-2 xl:col-span-1">
          <Panel title={t("sourcesUsed")}>
            <ul className="space-y-1">
              {sources.map((c) => (
                <li key={c.display} className="flex items-center justify-between gap-2 text-[11px]">
                  <CitationPreview citation={c} />
                  <VerificationBadge state="verified" size="sm" />
                </li>
              ))}
            </ul>
          </Panel>
          <Panel title={t("citationStatus")}>
            <KeyValue
              rows={[
                { key: "p", label: tb("citationCounts.produced"), value: 6 },
                { key: "r", label: tb("citationCounts.resolved"), value: 6 },
                { key: "m", label: tb("citationCounts.matched"), value: 6 },
                { key: "u", label: tb("citationCounts.unresolved"), value: 0 },
              ]}
            />
          </Panel>
          <Panel title={t("verificationStatus")}>
            <KeyValue
              rows={[
                { key: "h", label: tb("citationCounts.verified"), value: 2 },
                { key: "n", label: tb("citationCounts.unreviewed"), value: 4 },
              ]}
            />
          </Panel>
          <Panel title={tb("notAvailable")}>
            <p className="text-fg-secondary text-[11px]">{tb("notAvailableBody")}</p>
            <div className="mt-2">
              <GapNotice
                kind="closed-session"
                reference="T. 32–40"
                extent="9 pages"
                reason={tb("notAvailable")}
              />
            </div>
          </Panel>
        </aside>
      </div>
    </AppShell>
  );
}

// ---------------------------------------------------------- public mode ---

const ENTRIES = [
  ["whatDecided", "/findings", 2],
  ["whoTestified", "/witnesses", 26],
  ["whichEvidence", "/exhibits", 25],
  ["whatHappened", "/timeline", 5],
  ["howConnected", "/network", 4],
  ["readSource", "/documents", 26],
] as const;
const TERMS: Record<string, { def: string; article: string }> = {
  finding: {
    def: "A conclusion the Panel reached on the evidence.",
    article: "Art. 40 (demo reference)",
  },
  exhibit: { def: "An item admitted into evidence.", article: "Rule 138 (demo reference)" },
};

export function PublicScreen({ topic }: { topic?: string } = {}) {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const tFooter = useTranslations("footer");
  const [mode, setMode] = useState<"simple" | "research">("simple");
  const [term, setTerm] = useState<string | null>(null);
  const activeTopic = ENTRIES.find((e) => e[1].slice(1) === topic || e[0] === topic) ?? ENTRIES[0];
  return (
    <AppShell mode="light" footer={tFooter("sourceNote")}>
      <div className="flex min-w-0 flex-1 flex-col">
        <Toolbar className="bg-surface">
          <Segmented
            label={tb("modeToggle")}
            value={mode}
            onChange={setMode}
            options={[
              { key: "simple", label: tb("simple") },
              { key: "research", label: tb("research") },
            ]}
          />
          {mode === "research" ? <ActionLink href="/">{tb("research")} →</ActionLink> : null}
          <span className="text-fg-muted ml-auto text-[10px]">{t("simpleIntro")}</span>
        </Toolbar>
        <section className="bg-surface-alt px-4 py-8 md:py-12">
          <div className="mx-auto grid w-full max-w-[1100px] gap-6 md:grid-cols-[minmax(0,1fr)_320px]">
            <div>
              <h1 className="text-fg font-serif text-[30px] leading-tight md:text-[36px]">
                {tb("publicHero")}
              </h1>
              <p className="text-fg-secondary mt-3 max-w-2xl text-[14px] leading-relaxed">
                {tb("publicIntro")}
              </p>
            </div>
            <Panel title={t("beforeBegin")}>
              <ol className="text-fg-body list-decimal space-y-1 pl-4 text-[12px]">
                <li>{tb("beforeBegin1")}</li>
                <li>{tb("beforeBegin2")}</li>
                <li>{tb("beforeBegin3")}</li>
              </ol>
            </Panel>
          </div>
        </section>
        <div className="mx-auto w-full max-w-[1100px] space-y-6 px-4 py-6">
          <DemoNotice />
          <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
            {ENTRIES.map(([key, href, count]) => (
              <li key={key}>
                <Link
                  href={`/public/${href.slice(1)}`}
                  aria-current={activeTopic[0] === key ? "page" : undefined}
                  className={`border-border-subtle bg-surface rounded-card hover:border-accent block h-full border p-3 ${activeTopic[0] === key ? "border-accent" : ""}`}
                >
                  <span className="text-fg block text-[13px] font-semibold">{t(key)}</span>
                  <span className="tabular text-fg-muted mt-2 block text-[11px]">{count}</span>
                </Link>
              </li>
            ))}
          </ul>
          <div className="grid gap-4 md:grid-cols-2">
            <SectionCard title={tb("workedExample")}>
              <p className="section-label">{t(activeTopic[0])}</p>
              <p className="text-fg-body mt-2 text-[14px] leading-relaxed">
                {t("plainLanguage")}: the Panel reached a{" "}
                <button
                  type="button"
                  onClick={() => setTerm(term === "finding" ? null : "finding")}
                  aria-expanded={term === "finding"}
                  className="text-accent underline decoration-dotted underline-offset-2"
                >
                  finding
                </button>{" "}
                on the demo event using an{" "}
                <button
                  type="button"
                  onClick={() => setTerm(term === "exhibit" ? null : "exhibit")}
                  aria-expanded={term === "exhibit"}
                  className="text-accent underline decoration-dotted underline-offset-2"
                >
                  exhibit
                </button>{" "}
                and a witness account.
              </p>
              {term ? (
                <div
                  role="dialog"
                  aria-label={tb("termTooltip")}
                  className="border-border bg-surface-raised rounded-card max-md:rounded-t-sheet mt-2 border p-2 text-[11px] max-md:fixed max-md:right-0 max-md:bottom-14 max-md:left-0 max-md:z-30"
                >
                  <strong className="text-fg block">{term}</strong>
                  {TERMS[term]!.def}
                  <span className="text-fg-muted block">
                    {tb("governingArticle")}: {TERMS[term]!.article}
                  </span>
                  <Link href="/findings" className="text-accent font-semibold">
                    {tb("learnMore")} →
                  </Link>
                </div>
              ) : null}
              <RecordBlock sourceType="court" title={t("originalText")} citations={[courtCitation]}>
                <p className="font-serif">
                  “Generic demo wording of the original finding, shown beneath its explanation.”
                </p>
              </RecordBlock>
            </SectionCard>
            <div className="space-y-4">
              <SectionCard title={t("doesNotMean")}>
                <ul className="text-fg-body list-disc space-y-1 pl-4 text-[12px]">
                  <li>That any person not named in the finding was involved.</li>
                  <li>That the finding decides matters outside its paragraph range.</li>
                </ul>
              </SectionCard>
              <SectionCard title={tb("whereFrom")}>
                <ul className="space-y-1 text-[12px]">
                  <li>
                    <Link href="/witnesses/W01234" className="text-accent identifier">
                      W01234
                    </Link>{" "}
                    · {t("testimony")}
                  </li>
                  <li>
                    <Link href="/documents/P00123?page=4" className="text-accent identifier">
                      P00123
                    </Link>{" "}
                    · {t("exhibits")}
                  </li>
                  <li>
                    <CitationChip citation={courtCitation} size="sm" />
                  </li>
                </ul>
              </SectionCard>
              <div className="border-defence bg-surface rounded-card border border-l-[3px] p-3 text-[12px]">
                <strong className="text-fg block">{tb("otherSide")}</strong>
                <Link href="/findings/F-DEMO-01" className="text-accent font-semibold">
                  {tb("readOtherSide")} →
                </Link>
              </div>
              <ActionLink href={activeTopic[1]} primary>
                {tb("openSection")}
              </ActionLink>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
