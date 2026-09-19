import { PersonDossierScreen } from "@/components/screens/phase5";

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <PersonDossierScreen slug={decodeURIComponent(slug)} />;
}
