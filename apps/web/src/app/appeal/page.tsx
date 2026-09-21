import { AppealScreen, RealAppealScreen } from "@/components/screens/phase5";
import { getRepository, resolveDataSource } from "@/data";

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
  const repository = getRepository();
  const workspace = await repository.listAppealIssues();
  const requested = (await searchParams).issue;
  const key = requested ?? workspace.issues[0]?.key;
  const issue = key ? await repository.getAppealIssue(key) : null;
  return <RealAppealScreen workspace={workspace} issue={issue ?? undefined} />;
}
