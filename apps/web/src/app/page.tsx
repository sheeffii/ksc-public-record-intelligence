import { getTranslations } from "next-intl/server";
import { unstable_cache } from "next/cache";
import Link from "next/link";
import { SearchIcon } from "@/components/primitives/icons";
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

  return (
    <AppShell footer={tFooter("sourceNote")}>
      <section className="border-border-subtle bg-bg-deep border-b px-4 py-10">
        <div className="mx-auto flex w-full max-w-5xl flex-col items-start gap-4">
          <h1 className="text-fg text-[40px] leading-tight font-bold tracking-[-0.03em]">
            {t("title")}
          </h1>
          <p className="text-fg-secondary max-w-2xl text-[14px] leading-relaxed">{t("subtitle")}</p>
          <form action="/search" method="get" role="search" className="flex w-full max-w-2xl gap-2">
            <label className="relative flex-1">
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
                className="rounded-inset border-border bg-surface text-fg placeholder:text-fg-muted h-11 w-full border pr-3 pl-9 text-[13px]"
              />
            </label>
            <button
              type="submit"
              className="rounded-inset border-accent bg-accent hover:bg-accent-bright text-bg-deep h-11 border px-4 text-[13px] font-semibold"
            >
              {t("searchButton")}
            </button>
          </form>
          <p className="text-fg-muted max-w-2xl text-[11px] leading-relaxed">{t("principle")}</p>
        </div>
      </section>

      <section className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-6">
        <p className="text-fg-secondary text-[11.5px]">{t15("sourceBacked")}</p>
        <div>
          <div className="mb-2 flex items-baseline justify-between gap-3">
            <h2 className="section-label">{t18("corpusOverview")}</h2>
            <p className="text-fg-muted text-[10.5px]">{t15("sourceBacked")}</p>
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7">
            {corpusStats.map((stat) => {
              return (
                <Link
                  key={stat.key}
                  href={stat.href}
                  className="rounded-card border-border bg-surface hover:bg-surface-raised flex flex-col gap-1 border px-3 py-2.5"
                >
                  <span className="text-fg tabular text-[22px] font-bold">{stat.value ?? "—"}</span>
                  <span className="text-fg-muted text-[10.5px]">{stat.label}</span>
                </Link>
              );
            })}
          </div>
        </div>

        <div>
          <h2 className="section-label mb-2">{t18("researchPaths")}</h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {PRIMARY_NAV.map((item) => (
              <Panel
                key={item.key}
                as="div"
                className={cn(
                  "hover:bg-surface-raised",
                  item.isAi && "border-ai-border border-dashed",
                )}
              >
                <Link href={item.href} className="flex h-full flex-col gap-1">
                  <span
                    className={cn("text-[14px] font-semibold", item.isAi ? "text-ai" : "text-fg")}
                  >
                    {tNav(item.key)}
                  </span>
                  <span className="text-fg-muted font-mono text-[10.5px]">{item.href}</span>
                </Link>
              </Panel>
            ))}
          </div>
        </div>

        <div className="grid gap-3 lg:grid-cols-3">
          <Panel title={t18("recentDocuments")}>
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
          <Panel title={tb("recentFindings")}>
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
          <Panel title={tb("ingestion")}>
            {ingestion ? (
              <dl className="space-y-2 text-[11px]">
                <div className="flex justify-between gap-3">
                  <dt className="text-fg-secondary">{t15("sourceRecords")}</dt>
                  <dd className="text-fg tabular font-semibold">{ingestion.source_records}</dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt className="text-fg-secondary">{t15("parsedVersions")}</dt>
                  <dd className="text-fg tabular font-semibold">
                    {ingestion.versions_parsed}/{ingestion.versions}
                  </dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt className="text-fg-secondary">{t15("openIngestionIssues")}</dt>
                  <dd className="text-fg tabular font-semibold">
                    {ingestion.items_failed + ingestion.quarantine_open}
                  </dd>
                </div>
              </dl>
            ) : (
              <p className="text-fg-secondary text-[11px]">{t15("ingestionUnavailable")}</p>
            )}
          </Panel>
        </div>
      </section>
    </AppShell>
  );
}
