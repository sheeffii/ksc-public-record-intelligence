import { DocumentReaderScreen } from "@/components/screens/phase5";
import { getRepository, resolveDataSource } from "@/data";
import { notFound } from "next/navigation";

export default async function Page({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{
    document?: string;
    version?: string;
    page?: string;
    pdfPage?: string;
  }>;
}) {
  const { id } = await params;
  const query = await searchParams;
  const decoded = query.document ?? decodeURIComponent(id);
  const coordinate = query.page ?? query.pdfPage;
  const initialPage = coordinate && /^\d+$/.test(coordinate) ? Number(coordinate) : undefined;
  if (
    resolveDataSource({ NEXT_PUBLIC_DATA_SOURCE: process.env.NEXT_PUBLIC_DATA_SOURCE }) === "mock"
  ) {
    return <DocumentReaderScreen id={decoded} initialPage={initialPage} />;
  }
  const document = await getRepository().getDocument(decoded, query.version);
  if (!document) notFound();
  return <DocumentReaderScreen id={decoded} initialDocument={document} initialPage={initialPage} />;
}
