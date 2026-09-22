import { RealIncidentScreen } from "@/components/screens/phase5";
import { getRepository } from "@/data";
import { notFound } from "next/navigation";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const incident = await getRepository().getIncident(decodeURIComponent(id));
  if (!incident) notFound();
  return <RealIncidentScreen incident={incident} />;
}
