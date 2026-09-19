import { useTranslations } from "next-intl";
import Link from "next/link";
import { LogoMark } from "@/components/primitives/icons";

/** Four-square mark + `KSC·PRI` wordmark. The short name is never translated. */
export function Logo() {
  const t = useTranslations("app");
  return (
    <Link
      href="/"
      aria-label={t("name")}
      className="rounded-control text-fg flex shrink-0 items-center gap-2 px-1"
    >
      <LogoMark size={20} className="text-accent" />
      <span className="text-[13px] font-bold tracking-[-0.02em]">{t("shortName")}</span>
    </Link>
  );
}
