import { DirectoryScreen } from "@/components/screens/phase5";
import { loadServerDirectory } from "@/data/directory-page";
import { getTranslations } from "next-intl/server";

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const t = await getTranslations("screens");
  const { rows, server } = await loadServerDirectory("documents", await searchParams);
  return (
    <DirectoryScreen
      kind="documents"
      screenTitle={t("documents")}
      initialRows={rows}
      server={server}
    />
  );
}
