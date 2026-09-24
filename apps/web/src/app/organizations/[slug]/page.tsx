import { RealOrganizationScreen } from "@/components/screens/phase5";
import { getRepository } from "@/data";
import { notFound } from "next/navigation";

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const decoded = decodeURIComponent(slug);
  const repository = getRepository();
  const organization = await repository.getOrganization(decoded);
  if (!organization) notFound();
  const [occurrences, network] = await Promise.all([
    repository.search(organization.name),
    repository.getNetwork(organization.slug),
  ]);
  return (
    <RealOrganizationScreen
      organization={organization}
      occurrences={occurrences}
      network={network}
    />
  );
}
