import { DocumentPage } from "../page";

export default async function LegacyDocumentPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string; rest: string[] }>;
  searchParams: Parameters<typeof DocumentPage>[0]["searchParams"];
}) {
  const { id, rest } = await params;
  return <DocumentPage id={[id, ...rest].join("/")} searchParams={searchParams} />;
}
