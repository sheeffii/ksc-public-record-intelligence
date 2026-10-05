import { useTranslations } from "next-intl";
import { Panel } from "@/components/primitives/Panel";
import { AppShell } from "@/components/shell/AppShell";
import { ScreenHeader } from "./ScreenChrome";

export function AiResearchAccess({ error }: { error?: string }) {
  const t = useTranslations("phase11");
  const access = useTranslations("aiAccess");
  return (
    <AppShell showDemoFlag={false}>
      <ScreenHeader
        eyebrow={t("eyebrow")}
        title={t("title")}
        description={access("description")}
        realData
      />
      <div className="mx-auto w-full max-w-lg p-4">
        <Panel title={access("title")}>
          <form action="/api/ai/access" method="post" className="space-y-3">
            <label htmlFor="researcher-token" className="text-fg block text-sm">
              {access("tokenLabel")}
            </label>
            <input
              id="researcher-token"
              name="token"
              type="password"
              autoComplete="off"
              required
              className="border-border bg-surface text-fg rounded-inset w-full border px-3 py-2"
            />
            {error ? (
              <p role="alert" className="text-fg-secondary text-sm">
                {access(error === "unavailable" ? "unavailable" : "invalid")}
              </p>
            ) : null}
            <button
              type="submit"
              className="rounded-control border-accent bg-accent text-bg-deep min-h-11 border px-4 text-sm font-semibold"
            >
              {access("continue")}
            </button>
          </form>
        </Panel>
      </div>
    </AppShell>
  );
}
