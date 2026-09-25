import { RealExhibitScreen } from "@/components/screens/phase5";
import { getRepository } from "@/data";
import { notFound } from "next/navigation";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const decoded = decodeURIComponent(id);
  const repository = getRepository();
  const exhibit = await repository.getExhibit(decoded);
  if (!exhibit) notFound();
  const [mentions, occurrences, network, statusEvents] = await Promise.all([
    repository.getEntityMentions("exhibit", exhibit.id),
    repository.search(exhibit.id),
    repository.getNetwork(exhibit.id),
    repository.getExhibitStatusEvents(exhibit.id),
  ]);
  return (
    <RealExhibitScreen
      exhibit={exhibit}
      mentions={mentions}
      occurrences={occurrences}
      network={network}
      statusEvents={statusEvents}
    />
  );
}
