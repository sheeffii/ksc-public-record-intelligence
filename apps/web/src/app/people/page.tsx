import { DirectoryScreen } from "@/components/screens/phase5";
import { getRepository } from "@/data";
import { getTranslations } from "next-intl/server";

export default async function Page() {
  const t = await getTranslations("screens");
  const rows = await getRepository().getDirectory("people");
  return <DirectoryScreen kind="people" screenTitle={t("people")} initialRows={rows} />;
}
