import { RealPublicScreen } from "@/components/screens/phase5";
import { getRepository } from "@/data";

export default async function Page() {
  const repository = getRepository();
  const [findings, documents, witnesses, people, exhibits, incidents] = await Promise.all([
    repository.getDirectory("findings"),
    repository.getDirectory("documents"),
    repository.getDirectory("witnesses"),
    repository.getDirectory("people"),
    repository.getDirectory("exhibits"),
    repository.getDirectory("incidents"),
  ]);
  return (
    <RealPublicScreen
      rowsByKind={{ findings, documents, witnesses, people, exhibits, incidents }}
    />
  );
}
