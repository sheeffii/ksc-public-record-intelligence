import { AppealScreen, RealAppealScreen } from "@/components/screens/phase5";
import { getRepository, resolveDataSource } from "@/data";
import { unstable_cache } from "next/cache";

const getAppealWorkspace = unstable_cache(
  () => getRepository().listAppealIssues(),
  ["production-appeal-workspace"],
  { revalidate: 30 },
);

const getAppealIssue = unstable_cache(
  (key: string) => getRepository().getAppealIssue(key),
  ["production-appeal-issue"],
  { revalidate: 30 },
);

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ issue?: string }>;
}) {
  if (
    resolveDataSource({ NEXT_PUBLIC_DATA_SOURCE: process.env.NEXT_PUBLIC_DATA_SOURCE }) === "mock"
  ) {
    return <AppealScreen />;
  }
  const workspace = await getAppealWorkspace();
  const requested = (await searchParams).issue;
  const key = requested ?? workspace.issues[0]?.key;
  const issue = key ? await getAppealIssue(key) : null;
  return <RealAppealScreen workspace={workspace} issue={issue ?? undefined} />;
}
