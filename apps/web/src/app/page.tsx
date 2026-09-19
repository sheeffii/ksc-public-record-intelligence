import { useTranslations } from "next-intl";
import Link from "next/link";
import { SearchIcon } from "@/components/primitives/icons";
import { Panel } from "@/components/primitives/Panel";
import { CitationChip, VerificationBadge } from "@/components/provenance";
import { AppShell } from "@/components/shell/AppShell";
import { DemoDataFlag } from "@/components/shell/DemoDataFlag";
import { PRIMARY_NAV } from "@/lib/routes";
import { cn } from "@/lib/utils";
import { courtCitation, mockRepository } from "@/mock";

/** Seven live counts (PAGE_SPECS.md §02). None exists yet, so each renders a dash — never 0. */
const STAT_KEYS = [
  "documents",
  "people",
  "witnesses",
  "exhibits",
  "findings",
  "incidents",
  "network",
] as const;

/**
 * Homepage (Artboard 02) — foundation version. Hero, search, explore grid.
 * No figure on this screen is fabricated: counts are pending dashes until the
 * records database holds anything, and the demo flag stays until every figure
 * is a live read.
 */
export default function HomePage() {
  const t = useTranslations("home");
  const tNav = useTranslations("nav");
  const tFooter = useTranslations("footer");
  const tPhase = useTranslations("phase5");
  const demoCounts: Record<(typeof STAT_KEYS)[number], number> = {
    documents: mockRepository.getDirectory("documents").length,
    people: mockRepository.getDirectory("people").length,
    witnesses: mockRepository.getDirectory("witnesses").length,
    exhibits: mockRepository.getDirectory("exhibits").length,
    findings: mockRepository.getDirectory("findings").length,
    incidents: mockRepository.getDirectory("incidents").length,
    network: mockRepository.getNetwork().edges.length,
  };

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
              className="rounded-inset border-accent bg-accent hover:bg-accent-bright h-11 border px-4 text-[13px] font-semibold text-white"
            >
              {t("searchButton")}
            </button>
          </form>
          <p className="text-fg-muted max-w-2xl text-[11px] leading-relaxed">{t("principle")}</p>
        </div>
      </section>

      <section className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-6">
        <div className="rounded-card border-demo-border bg-demo-bg/40 text-fg-body flex flex-wrap items-center gap-3 border px-3 py-2 text-[11.5px]">
          <DemoDataFlag compact />
          <span>{tPhase("mockNotice")}</span>
        </div>

        <div>
          <div className="mb-2 flex items-baseline justify-between gap-3">
            <h2 className="section-label">{t("explore")}</h2>
            <p className="text-fg-muted text-[10.5px]">{tPhase("mockNotice")}</p>
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7">
            {STAT_KEYS.map((key) => {
              const item = PRIMARY_NAV.find((n) => n.key === key);
              return (
                <Link
                  key={key}
                  href={item?.href ?? "/"}
                  className="rounded-card border-border bg-surface hover:bg-surface-raised flex flex-col gap-1 border px-3 py-2.5"
                >
                  <span className="text-fg tabular text-[22px] font-bold tracking-[-0.02em]">
                    {demoCounts[key]}
                  </span>
                  <span className="text-fg-muted text-[10.5px]">{tNav(key)}</span>
                </Link>
              );
            })}
          </div>
        </div>

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
        <div className="grid gap-3 lg:grid-cols-3">
          <Panel title={tPhase("documents")}>
            {mockRepository.getDirectory("documents").map((row) => (
              <Link
                key={row.id}
                href={row.href}
                className="border-border-faint block border-b py-2"
              >
                <span className="identifier text-doc">{row.id}</span>
                <span className="text-fg ml-2 text-[11px]">{row.title}</span>
              </Link>
            ))}
          </Panel>
          <Panel title={tPhase("courtFindings")}>
            <div className="flex items-center justify-between">
              <Link href="/findings/F-DEMO-01" className="text-fg text-[11px] font-semibold">
                Illustrative finding
              </Link>
              <VerificationBadge state="verified" />
            </div>
            <div className="mt-3">
              <CitationChip citation={courtCitation} />
            </div>
          </Panel>
          <Panel title={tPhase("verificationStatus")}>
            <p className="text-fg text-[12px] font-semibold">Mock repository ready</p>
            <p className="text-fg-secondary mt-2 text-[11px]">
              No court documents ingested · all displayed records are generic demo content.
            </p>
          </Panel>
        </div>
      </section>
    </AppShell>
  );
}
