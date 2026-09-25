import { DocumentReaderScreen } from "@/components/screens/phase5";
import { getRepository, resolveApiBaseUrl, resolveDataSource } from "@/data";
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
    anchor?: string;
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
  const anchor = query.anchor ? await repository.getSourceAnchor(query.anchor) : null;
  const [document, contextNetwork] = await Promise.all([
    repository.getDocument(
      decoded,
      anchor?.officialVersionRef ?? query.version,
      anchor?.pageNumber ?? sourcePage,
      anchor?.pdfPageIndex ?? pdfPageIndex,
    ),
    repository.getNetwork(decoded),
  ]);
  if (!document) notFound();
  if (document.versionRef && document.artifactStatus === "fetched") {
    const publicApi = resolveApiBaseUrl(
      { NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL },
      false,
    ).replace(/\/+$/, "");
    document.artifactUrl = `${publicApi}/api/v1/document-versions/${document.versionRef}/artifact`;
  }
  return (
    <DocumentReaderScreen
      id={decoded}
      initialDocument={document}
      initialPage={anchor?.pageNumber ?? sourcePage}
      initialPdfPage={anchor?.pdfPageIndex ?? pdfPageIndex}
      initialPara={anchor?.paragraphNumber ?? para}
      highlight={anchor?.exactText ?? highlight}
      contextNetwork={contextNetwork}
      sourceAnchor={anchor ?? undefined}
    />
  );
}
