import { RealPersonScreen } from "@/components/screens/phase5";
import { getRepository } from "@/data";
import { notFound } from "next/navigation";

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const repository = getRepository();
  const decoded = decodeURIComponent(slug);
  const person = await repository.getPerson(decoded);
  if (!person) notFound();
  const [mentions, occurrences, network] = await Promise.all([
    repository.getEntityMentions("person", person.slug),
    repository.search(person.displayName),
    repository.getNetwork(person.slug),
  ]);
  return (
    <RealPersonScreen
      person={person}
      mentions={mentions}
      occurrences={occurrences}
      network={network}
    />
  );
}
