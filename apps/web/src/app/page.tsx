import { getTranslations } from "next-intl/server";
import { unstable_cache } from "next/cache";
import Link from "next/link";
import {
  DocumentIcon,
  NetworkIcon,
  SearchIcon,
  SparkIcon,
  UserIcon,
} from "@/components/primitives/icons";
import { Panel } from "@/components/primitives/Panel";
import { VerificationBadge } from "@/components/provenance";
import { AppShell } from "@/components/shell/AppShell";
import { getRepository, resolveApiBaseUrl, resolveDataSource } from "@/data";
import { PRIMARY_NAV } from "@/lib/routes";
import { cn } from "@/lib/utils";

type IngestionSummary = {
  source_records: number;
  versions: number;
  versions_parsed: number;
  items_failed: number;
  quarantine_open: number;
  pages_parsed: number;
  transcript_segments_parsed: number;
  citations_resolved: number;
};

async function getIngestionSummary(): Promise<IngestionSummary | null> {
  const env = {
    NEXT_PUBLIC_DATA_SOURCE: process.env.NEXT_PUBLIC_DATA_SOURCE,
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    API_INTERNAL_URL: process.env.API_INTERNAL_URL,
  };
  if (resolveDataSource(env) !== "api") return null;
  try {
    const response = await fetch(`${resolveApiBaseUrl(env, true)}/api/v1/ingestion/status`, {
      headers: { accept: "application/json" },
    });
    if (!response.ok) return null;
    const payload = (await response.json()) as { counts: IngestionSummary };
    return payload.counts;
  } catch {
    return null;
  }
}

const getHomeData = unstable_cache(
  async () => {
    const repository = getRepository();
    const [documents, people, witnesses, exhibits, findings, ingestion] = await Promise.all([
      repository.getDirectory("documents"),
      repository.getDirectory("people"),
      repository.getDirectory("witnesses"),
      repository.getDirectory("exhibits"),
      repository.getDirectory("findings"),
      getIngestionSummary(),
    ]);
    return { documents, people, witnesses, exhibits, findings, ingestion };
  },
  ["production-home-data"],
  { revalidate: 30 },
);

export default async function HomePage() {
  const [t, tNav, tFooter, tb, t15, t18] = await Promise.all([
    getTranslations("home"),
    getTranslations("nav"),
    getTranslations("footer"),
    getTranslations("phase5b"),
    getTranslations("phase15"),
    getTranslations("phase18"),
  ]);
  const { documents, people, witnesses, exhibits, findings, ingestion } = await getHomeData();
  const corpusStats = [
    { key: "documents", label: tNav("documents"), value: documents.length, href: "/documents" },
    { key: "pages", label: t18("parsedPages"), value: ingestion?.pages_parsed, href: "/documents" },
    {
      key: "segments",
      label: t18("transcriptSegments"),
      value: ingestion?.transcript_segments_parsed,
      href: "/search",
    },
    { key: "people", label: tNav("people"), value: people.length, href: "/people" },
    { key: "witnesses", label: tNav("witnesses"), value: witnesses.length, href: "/witnesses" },
    { key: "exhibits", label: tNav("exhibits"), value: exhibits.length, href: "/exhibits" },
    {
      key: "citations",
      label: t18("resolvedCitations"),
      value: ingestion?.citations_resolved,
      href: "/search",
    },
  ] as const;
  const recentDocuments = [...documents]
    .filter((row) => row.date !== "—")
    .sort((a, b) => b.date.localeCompare(a.date))
    .slice(0, 5);
  const exploreKeys = [
    "people",
    "witnesses",
    "documents",
    "exhibits",
    "timeline",
    "network",
    "findings",
    "ai",
  ] as const;
  const explore = exploreKeys.flatMap((key) => {
    const item = PRIMARY_NAV.find((candidate) => candidate.key === key);
    return item ? [item] : [];
  });
  const t21 = await getTranslations("phase21");
  const exploreIcon = (key: (typeof exploreKeys)[number]) => {
    if (key === "people" || key === "witnesses") return <UserIcon size={20} />;
    if (key === "network") return <NetworkIcon size={20} />;
    if (key === "ai") return <SparkIcon size={20} />;
    return <DocumentIcon size={20} />;
  };

  return (
    <AppShell footer={tFooter("sourceNote")}>
      <section className="border-border-subtle bg-bg-deep border-b px-4 py-12 md:py-14">
        <div className="mx-auto flex w-full max-w-[760px] flex-col items-center text-center">
          <p className="section-label text-accent mb-4">{t21("homeEyebrow")}</p>
          <h1 className="text-fg text-[40px] leading-tight font-bold tracking-[-0.03em]">
            {t("title")}
          </h1>
          <p className="text-fg-secondary mt-3 max-w-[650px] text-[14px] leading-relaxed">
            {t("subtitle")}
          </p>
          <form
            action="/search"
            method="get"
            role="search"
            className="border-border bg-surface shadow-palette/20 mt-8 flex w-full gap-2 rounded-[10px] border p-2"
          >
            <label className="relative min-w-0 flex-1">
              <span className="sr-only">{tNav("openSearch")}</span>
              <SearchIcon
                size={16}
                className="text-fg-muted pointer-events-none absolute top-1/2 left-3 -translate-y-1/2"
              />
              <input
                type="search"
                name="q"
                placeholder={t("searchPlaceholder")}
                autoComplete="off"
                className="text-fg placeholder:text-fg-muted h-10 w-full bg-transparent pr-3 pl-9 text-[13px]"
              />
            </label>
            <button
              type="submit"
              className="rounded-inset border-accent bg-accent hover:bg-accent-bright text-bg-deep h-10 border px-5 text-[13px] font-semibold"
            >
              {t("searchButton")}
            </button>
          </form>
          {recentDocuments.length ? (
            <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
              <span className="text-fg-muted text-[11px]">{t21("quickTry")}:</span>
              {recentDocuments.slice(0, 4).map((row) => (
                <Link
                  key={row.id}
                  href={`/search?q=${encodeURIComponent(row.id)}`}
                  className="border-border bg-surface-raised text-fg-secondary hover:border-accent hover:text-fg rounded-full border px-3 py-1 text-[10.5px]"
                >
                  {row.id}
                </Link>
              ))}
            </div>
          ) : null}
        </div>
      </section>

      <section aria-labelledby="corpus-overview" className="border-border-subtle border-b">
        <div className="mx-auto w-full max-w-[1440px] px-4 pt-3">
          <div className="flex items-baseline gap-3">
            <h2 id="corpus-overview" className="section-label text-doc">
              {t21("corpusAtGlance")}
            </h2>
            <p className="governance-text">{t15("sourceBacked")}</p>
          </div>
          <div className="mt-2 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7">
            {corpusStats.map((stat) => {
              return (
                <Link
                  key={stat.key}
                  href={stat.href}
                  className="border-border-subtle hover:bg-surface-raised flex min-h-20 flex-col justify-center border-r px-4 py-3 first:border-l"
                >
                  <span className="text-fg tabular text-[22px] font-bold">{stat.value ?? "—"}</span>
                  <span className="text-fg-muted text-[10.5px]">{stat.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      <section className="mx-auto flex w-full max-w-[1440px] flex-col gap-5 px-4 py-6">
        <div>
          <h2 className="section-label mb-3">{t21("researchEntryPoints")}</h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {explore.map((item) => (
              <Link
                key={item.key}
                href={item.href}
                className={cn(
                  "rounded-card border-border bg-surface hover:bg-surface-raised flex min-h-[102px] flex-col justify-between border p-4",
                  item.isAi && "border-ai-border bg-ai-surface border-dashed",
                )}
              >
                <span className={item.isAi ? "text-ai" : "text-accent"}>
                  {exploreIcon(item.key as (typeof exploreKeys)[number])}
                </span>
                <span>
                  <span
                    className={cn(
                      "block text-[13px] font-semibold",
                      item.isAi ? "text-ai" : "text-fg",
                    )}
                  >
                    {tNav(item.key)}
                  </span>
                  <span className="text-fg-muted mt-1 block text-[10.5px]">
                    {t21(`exploreDescriptions.${item.key}`)}
                  </span>
                </span>
              </Link>
            ))}
          </div>
        </div>

        <div className="grid gap-3 lg:grid-cols-3">
          <Panel
            title={t21("recentRecords")}
            actions={
              <Link href="/documents" className="text-accent text-[10.5px]">
                {t21("viewAll")} →
              </Link>
            }
          >
            {recentDocuments.map((row) => (
              <Link
                key={row.id}
                href={row.href}
                className="border-border-faint block border-b py-2"
              >
                <span className="identifier text-doc">{row.id}</span>
                <span className="text-fg ml-2 text-[11px]">{row.title}</span>
              </Link>
            ))}
            {!documents.length ? (
              <p className="text-fg-secondary text-[11px]">{t15("empty.documents")}</p>
            ) : null}
          </Panel>
          <Panel
            title={tb("recentFindings")}
            actions={
              <Link href="/findings" className="text-accent text-[10.5px]">
                {t21("viewAll")} →
              </Link>
            }
          >
            {findings.slice(0, 5).map((row) => (
              <Link
                key={row.id}
                href={row.href}
                className="border-border-faint flex items-center justify-between gap-2 border-b py-2"
              >
                <span className="min-w-0">
                  <span className="identifier text-court">{row.id}</span>
                  <span className="text-fg ml-2 text-[11px]">{row.title}</span>
                </span>
                <VerificationBadge state={row.verification} size="sm" />
              </Link>
            ))}
            {!findings.length ? (
              <p className="text-fg-secondary text-[11px]">{t15("empty.findings")}</p>
            ) : null}
          </Panel>
          <Panel title={t21("ingestionStatus")}>
            {ingestion ? (
              <div className="space-y-3 text-[11px]">
                <div className="flex justify-between gap-3">
                  <span className="text-fg-secondary">{t15("sourceRecords")}</span>
                  <span className="text-fg tabular font-semibold">{ingestion.source_records}</span>
                </div>
                <div>
                  <div className="flex justify-between gap-3">
                    <span className="text-fg-secondary">{t15("parsedVersions")}</span>
                    <span className="text-fg tabular font-semibold">
                      {ingestion.versions_parsed}/{ingestion.versions}
                    </span>
                  </div>
                  <div
                    role="progressbar"
                    aria-label={t15("parsedVersions")}
                    aria-valuemin={0}
                    aria-valuemax={ingestion.versions}
                    aria-valuenow={ingestion.versions_parsed}
                    className="bg-surface-raised mt-1 h-1 overflow-hidden rounded-full"
                  >
                    <div
                      className="bg-accent h-full"
                      style={{
                        width: `${ingestion.versions ? (ingestion.versions_parsed / ingestion.versions) * 100 : 0}%`,
                      }}
                    />
                  </div>
                </div>
                <div className="flex justify-between gap-3">
                  <span className="text-fg-secondary">{t15("openIngestionIssues")}</span>
                  <span className="text-fg tabular font-semibold">
                    {ingestion.items_failed + ingestion.quarantine_open}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-fg-secondary text-[11px]">{t15("ingestionUnavailable")}</p>
            )}
          </Panel>
        </div>
      </section>
    </AppShell>
  );
}
