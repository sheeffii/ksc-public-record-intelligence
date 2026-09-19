import { useTranslations } from "next-intl";

/** Fail-closed notice rendered before all protected-witness content. */
export function ProtectionNotice() {
  const t = useTranslations("protection");
  return (
    <aside
      data-protection-notice
      className="rounded-card border-witness bg-witness-bg border px-3 py-3"
      aria-labelledby="protection-notice-title"
    >
      <h2 id="protection-notice-title" className="text-witness text-[12px] font-semibold">
        {t("title")}
      </h2>
      <p className="text-fg-body mt-1 text-[11px] leading-relaxed">{t("body")}</p>
    </aside>
  );
}
