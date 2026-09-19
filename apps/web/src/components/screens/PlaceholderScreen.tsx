import { useTranslations } from "next-intl";
import Link from "next/link";
import { buttonVariants } from "@/components/primitives/Button";
import { EmptyState } from "@/components/primitives/States";
import { AppShell } from "@/components/shell/AppShell";
import { getRoute, type ScreenKey } from "@/lib/routes";
import { cn } from "@/lib/utils";

export interface PlaceholderScreenProps {
  screen: ScreenKey;
  /** The record's own identifier from the URL, rendered verbatim, never translated. */
  identifier?: string;
}

/**
 * Phase 4 route placeholder. Renders the full application shell for an
 * approved route and states honestly that the screen is not built. It shows
 * no figures, so it carries no DemoDataFlag beyond the case stripe.
 */
export function PlaceholderScreen({ screen, identifier }: PlaceholderScreenProps) {
  const t = useTranslations("placeholder");
  const tScreens = useTranslations("screens");
  const route = getRoute(screen);
  const title = tScreens(screen);

  return (
    <AppShell mode={route.mode} crumbs={[{ label: title }]} showDemoFlag={false}>
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-4 py-8">
        <header className="flex flex-col gap-1">
          <p className="section-label">{t("phaseLabel")}</p>
          <h1 className="text-fg text-[28px] font-bold tracking-[-0.02em]">{title}</h1>
          {identifier ? (
            <p className="text-fg-secondary text-[12px]">
              {t("identifier")}: <span className="identifier text-fg">{identifier}</span>
            </p>
          ) : null}
        </header>

        <dl className="grid grid-cols-[max-content_1fr] gap-x-6 gap-y-1.5 text-[12px]">
          <dt className="section-label self-center">{t("route")}</dt>
          <dd className="text-fg-body font-mono">{route.pattern}</dd>
          <dt className="section-label self-center">{t("spec")}</dt>
          <dd className="text-fg-body">
            {route.artboard ? t("artboard", { id: route.artboard }) : t("notDesigned")}
          </dd>
          <dt className="section-label self-center">{t("mode")}</dt>
          <dd className="text-fg-body">
            {route.mode === "light" ? t("modeLight") : t("modeDark")}
          </dd>
        </dl>

        <EmptyState
          title={t("absent")}
          reason={t("reason")}
          action={
            <Link href="/" className={cn(buttonVariants({ variant: "secondary", size: "sm" }))}>
              {t("action")}
            </Link>
          }
        />
      </div>
    </AppShell>
  );
}
