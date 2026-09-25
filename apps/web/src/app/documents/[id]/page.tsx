import { DocumentReaderScreen } from "@/components/screens/phase5";
import { getRepository, resolveDataSource } from "@/data";
import { MAX_HIGHLIGHT_LENGTH } from "@/lib/exact-source";
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
    para?: string;
    hl?: string;
  }>;
}) {
  const { id } = await params;
  const query = await searchParams;
  const decoded = query.document ?? decodeURIComponent(id);
  const sourcePage = query.page && /^\d+$/.test(query.page) ? Number(query.page) : undefined;
  const pdfPageIndex =
    query.pdfPage && /^\d+$/.test(query.pdfPage) ? Number(query.pdfPage) : undefined;
  const para = query.para && /^\d+$/.test(query.para) ? Number(query.para) : undefined;
  const highlight = query.hl && query.hl.length <= MAX_HIGHLIGHT_LENGTH ? query.hl : undefined;
  if (
    resolveDataSource({ NEXT_PUBLIC_DATA_SOURCE: process.env.NEXT_PUBLIC_DATA_SOURCE }) === "mock"
  ) {
    return <DocumentReaderScreen id={decoded} initialPage={sourcePage ?? pdfPageIndex} />;
  }
  const repository = getRepository();
  const [document, contextNetwork] = await Promise.all([
    repository.getDocument(decoded, query.version, sourcePage, pdfPageIndex),
    repository.getNetwork(decoded),
  ]);
  if (!document) notFound();
  return (
    <DocumentReaderScreen
      id={decoded}
      initialDocument={document}
      initialPage={sourcePage}
      initialPdfPage={pdfPageIndex}
      initialPara={para}
      highlight={highlight}
      contextNetwork={contextNetwork}
    />
  );
}
