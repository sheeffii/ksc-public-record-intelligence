import { useTranslations } from "next-intl";
import Link from "next/link";
import { buttonVariants } from "@/components/primitives/Button";
import { EmptyState } from "@/components/primitives/States";
import { AppShell } from "@/components/shell/AppShell";

/**
 * Unknown route. Entity-level 404s (ROUTE_MAP.md §8 — naming the identifier
 * and distinguishing "not public" from "not found") arrive with the data layer.
 */
export default function NotFound() {
  const t = useTranslations("notFound");
  return (
    <AppShell showDemoFlag={false}>
      <div className="mx-auto w-full max-w-3xl px-4 py-8">
        <EmptyState
          title={t("title")}
          reason={t("generic")}
          action={
            <Link href="/search" className={buttonVariants({ variant: "secondary", size: "sm" })}>
              {t("action")}
            </Link>
          }
        />
      </div>
    </AppShell>
  );
}
