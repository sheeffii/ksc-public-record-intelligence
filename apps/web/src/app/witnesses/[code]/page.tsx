import { RealWitnessScreen } from "@/components/screens/phase5";
import { getRepository } from "@/data";
import { notFound } from "next/navigation";

export default async function Page({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  const witness = await getRepository().getWitness(decodeURIComponent(code));
  if (!witness) notFound();
  return <RealWitnessScreen witness={witness} />;
}
