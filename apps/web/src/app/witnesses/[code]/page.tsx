import { RealWitnessScreen } from "@/components/screens/phase5";
import { getRepository } from "@/data";
import { notFound } from "next/navigation";

export default async function Page({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  const repository = getRepository();
  const decoded = decodeURIComponent(code);
  const dossier = await repository.getWitness(decoded);
  if (!dossier) notFound();
  const [mentions, occurrences, network, appearances] = await Promise.all([
    repository.getEntityMentions("witness", dossier.witness.code),
    repository.search(dossier.witness.code),
    repository.getNetwork(dossier.witness.code),
    repository.getAppearances("witness", dossier.witness.code),
  ]);
  return (
    <RealWitnessScreen
      dossier={dossier}
      mentions={mentions}
      occurrences={occurrences}
      network={network}
      appearances={appearances}
    />
  );
}
