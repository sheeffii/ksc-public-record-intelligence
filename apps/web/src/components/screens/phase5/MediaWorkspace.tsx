import { useTranslations } from "next-intl";
import type { CourtMediaStatus, MediaWorkspaceView, SearchResult } from "@/data/contract";
import { AppShell } from "@/components/shell/AppShell";
import { Panel } from "@/components/primitives/Panel";
import { ScreenHeader, WorkspaceGrid } from "./ScreenChrome";

const STATUS_KEYS: readonly CourtMediaStatus[] = [
  "external_only",
  "mentioned",
  "tendered",
  "admitted",
  "rejected",
  "discussed",
  "relied_upon",
  "unknown",
];

export function MediaWorkspace({
  workspace,
  courtResults,
  query = "",
  scope = "external",
}: {
  workspace: MediaWorkspaceView;
  courtResults?: readonly SearchResult[];
  query?: string;
  scope?: "court" | "external" | "both";
}) {
  const t = useTranslations("media");
  return (
    <AppShell showDemoFlag={false} footer={t("boundary")}>
      <ScreenHeader
        realData
        eyebrow={t("eyebrow")}
        title={t("title")}
        description={t("description")}
      />
      <WorkspaceGrid
        left={
          <Panel title={t("searchModes")}>
            <form action="/media" className="space-y-3">
              <label className="text-fg-secondary block text-[11px]">
                <span className="mb-1 block">{t("query")}</span>
                <input
                  name="q"
                  defaultValue={query}
                  className="border-border bg-surface-raised text-fg rounded-control h-8 w-full border px-2"
                />
              </label>
              <label className="text-fg-secondary block text-[11px]">
                <span className="mb-1 block">{t("mode")}</span>
                <select
                  name="scope"
                  defaultValue={scope}
                  className="border-border bg-surface-raised text-fg rounded-control h-8 w-full border px-2"
                >
                  <option value="court">{t("courtOnly")}</option>
                  <option value="external">{t("externalOnly")}</option>
                  <option value="both">{t("both")}</option>
                </select>
              </label>
              <button className="bg-accent rounded-control h-8 px-3 text-[11px] font-semibold text-white">
                {t("search")}
              </button>
            </form>
            <div className="border-border-subtle mt-4 border-t pt-3">
              <p className="section-label mb-2">{t("statusFilter")}</p>
              <div className="flex flex-wrap gap-1">
                {STATUS_KEYS.map((status) => (
                  <a
                    key={status}
                    href={`/media?scope=external&status=${status}`}
                    className="border-border text-fg-secondary rounded-badge border px-2 py-1 text-[9px]"
                  >
                    {t(`status.${status}`)}
                  </a>
                ))}
              </div>
            </div>
          </Panel>
        }
        right={
          <Panel title={t("coverageLimitations")}>
            <ul className="text-fg-secondary list-disc space-y-2 pl-4 text-[11px] leading-relaxed">
              {workspace.limitations.map((limitation) => (
                <li key={limitation}>{limitation}</li>
              ))}
            </ul>
          </Panel>
        }
      >
        <div className="space-y-3">
          <div className="border-exhibit bg-exhibit-bg rounded-card border-l-2 px-3 py-2">
            <p className="text-exhibit text-[10px] font-bold tracking-wide">{t("boundaryBadge")}</p>
            <p className="text-fg-body mt-1 text-[11px]">{t("boundary")}</p>
          </div>

          {scope !== "court" ? (
            <Panel title={t("externalResults")} label={`${workspace.coverage.items}`}>
              <div className="space-y-2">
                {workspace.items.map((item) => (
                  <article
                    key={item.id}
                    className="border-border-subtle border-b pb-3 last:border-0"
                  >
                    <div className="flex flex-wrap gap-1">
                      <span className="bg-exhibit-bg text-exhibit rounded-badge px-2 py-1 text-[9px] font-bold">
                        {t("externalBadge")}
                      </span>
                      {item.courtStatuses.map((status) => (
                        <span
                          key={status}
                          className="border-border rounded-badge border px-2 py-1 text-[9px] font-semibold"
                        >
                          {t(`status.${status}`)}
                        </span>
                      ))}
                    </div>
                    <h2 className="text-fg mt-2 text-[14px] font-semibold">{item.title}</h2>
                    <p className="text-fg-secondary mt-1 text-[11px]">
                      {item.publisher} · {item.sourceType} · {item.publishedAt ?? t("dateUnknown")}
                    </p>
                    <a
                      href={item.canonicalUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="text-accent mt-2 inline-block text-[11px] font-semibold"
                    >
                      {t("openExternalSource")} ↗
                    </a>
                  </article>
                ))}
                {workspace.items.length === 0 ? (
                  <p className="text-fg-muted text-[11px]">{t("noResults")}</p>
                ) : null}
              </div>
            </Panel>
          ) : null}

          {scope !== "court" && workspace.comparisons.length ? (
            <Panel title={t("comparisons")}>
              <div className="space-y-3">
                {workspace.comparisons.map((comparison) => (
                  <article
                    key={comparison.id}
                    className="border-border-subtle border-b pb-3 last:border-0"
                  >
                    <span className="bg-surface-raised text-fg-secondary rounded-badge px-2 py-1 text-[9px] font-bold">
                      {t(`classification.${comparison.classification}`)}
                    </span>
                    <h2 className="text-fg mt-2 text-[13px] font-semibold">{comparison.title}</h2>
                    <div className="mt-2 grid gap-2 md:grid-cols-2">
                      <blockquote className="border-exhibit text-fg-body border-l-2 pl-2 font-serif text-[11px] leading-relaxed">
                        {comparison.statementA}
                      </blockquote>
                      {comparison.statementB ? (
                        <blockquote className="border-exhibit text-fg-body border-l-2 pl-2 font-serif text-[11px] leading-relaxed">
                          {comparison.statementB}
                        </blockquote>
                      ) : null}
                    </div>
                    <p className="text-fg-secondary mt-2 text-[11px]">{comparison.explanation}</p>
                  </article>
                ))}
              </div>
            </Panel>
          ) : null}

          {scope !== "external" ? (
            <Panel title={t("courtResults")} label={`${courtResults?.length ?? 0}`}>
              <div className="space-y-2">
                {(courtResults ?? []).map((result) => (
                  <article
                    key={`${result.category}-${result.id}`}
                    className="border-border-subtle border-b pb-2 last:border-0"
                  >
                    <span className="bg-court-bg text-court rounded-badge px-2 py-1 text-[9px] font-bold">
                      {t("courtBadge")}
                    </span>
                    <p className="text-fg mt-2 text-[12px] font-semibold">{result.title}</p>
                    <p className="identifier text-fg-muted mt-1 text-[10px]">{result.id}</p>
                  </article>
                ))}
                {(courtResults?.length ?? 0) === 0 ? (
                  <p className="text-fg-muted text-[11px]">{t("noResults")}</p>
                ) : null}
              </div>
            </Panel>
          ) : null}
        </div>
      </WorkspaceGrid>
    </AppShell>
  );
}
