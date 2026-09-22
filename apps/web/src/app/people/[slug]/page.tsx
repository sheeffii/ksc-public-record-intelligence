import { RealPersonScreen } from "@/components/screens/phase5";
import { getRepository } from "@/data";
import { notFound } from "next/navigation";

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const person = await getRepository().getPerson(decodeURIComponent(slug));
  if (!person) notFound();
  return <RealPersonScreen person={person} />;
}
