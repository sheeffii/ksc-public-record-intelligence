import { DirectoryScreen } from "@/components/screens/phase5";
import { getTranslations } from "next-intl/server";

export default async function Page() {
  const t = await getTranslations("screens");
  return <DirectoryScreen kind="witnesses" screenTitle={t("witnesses")} />;
}
