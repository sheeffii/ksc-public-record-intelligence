import { DocumentReaderScreen } from "@/components/screens/phase5";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <DocumentReaderScreen id={decodeURIComponent(id)} />;
}
