import type { ReferenceCounts } from "@ksc/shared";
import { useTranslations } from "next-intl";

const COUNT_KEYS = [
  "documentMentions",
  "transcriptMentions",
  "exhibitRefs",
  "findings",
  "witnessesWhoReferred",
  "incidents",
  "citationsResolved",
] as const satisfies readonly (keyof ReferenceCounts)[];

export function ReferenceCountStrip({ counts }: { counts: ReferenceCounts }) {
  const t = useTranslations("referenceCounts");
  return (
    <section data-reference-counts aria-labelledby="record-references-title">
      <div className="mb-2">
        <h2 id="record-references-title" className="section-label">
          {t("title")}
        </h2>
        <p className="governance-text">{t("disclaimer")}</p>
      </div>
      <dl className="border-border rounded-card bg-surface grid grid-cols-2 overflow-hidden border md:grid-cols-4 xl:grid-cols-7">
        {COUNT_KEYS.map((key) => (
          <div
            key={key}
            className="border-border-faint border-r border-b px-3 py-2 last:border-r-0"
          >
            <dd className="text-fg tabular text-[18px] font-bold tracking-[-0.02em]">
              {counts[key]}
            </dd>
            <dt className="text-fg-muted text-[10px]">{t(key)}</dt>
          </div>
        ))}
      </dl>
    </section>
  );
}
