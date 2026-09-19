import { PublicScreen } from "@/components/screens/phase5";

export default async function Page({ params }: { params: Promise<{ topic: string }> }) {
  const { topic } = await params;
  return <PublicScreen topic={topic} />;
}
