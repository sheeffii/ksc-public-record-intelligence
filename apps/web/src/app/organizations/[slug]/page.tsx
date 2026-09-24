import { RealOrganizationScreen } from "@/components/screens/phase5";
import { getRepository } from "@/data";
import { notFound } from "next/navigation";

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const decoded = decodeURIComponent(slug);
  const repository = getRepository();
  const organization = await repository.getOrganization(decoded);
  if (!organization) notFound();
  const [mentions, occurrences, network] = await Promise.all([
    repository.getEntityMentions("organization", organization.slug),
    repository.search(organization.name),
    repository.getNetwork(organization.slug),
  ]);
  return (
    <RealOrganizationScreen
      organization={organization}
      mentions={mentions}
      occurrences={occurrences}
      network={network}
    />
  );
}
