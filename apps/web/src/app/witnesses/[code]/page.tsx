import { RealWitnessScreen } from "@/components/screens/phase5";
import { getRepository } from "@/data";
import { notFound } from "next/navigation";

export default async function Page({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  const dossier = await getRepository().getWitness(decodeURIComponent(code));
  if (!dossier) notFound();
  return <RealWitnessScreen dossier={dossier} />;
}
