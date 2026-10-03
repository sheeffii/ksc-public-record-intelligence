import { RealPublicScreen } from "@/components/screens/phase5";
import { getRepository } from "@/data";

export default async function Page() {
  const repository = getRepository();
  const [findings, documents, witnesses, people, exhibits, incidents] = await Promise.all([
    repository.getDirectory("findings"),
    repository.queryDirectory("documents", { limit: 25, offset: 0 }),
    repository.getDirectory("witnesses"),
    repository.getDirectory("people"),
    repository.queryDirectory("exhibits", { limit: 25, offset: 0 }),
    repository.getDirectory("incidents"),
  ]);
  return (
    <RealPublicScreen
      rowsByKind={{
        findings,
        documents: documents.rows,
        witnesses,
        people,
        exhibits: exhibits.rows,
        incidents,
      }}
      totals={{ documents: documents.unfilteredTotal, exhibits: exhibits.unfilteredTotal }}
    />
  );
}
