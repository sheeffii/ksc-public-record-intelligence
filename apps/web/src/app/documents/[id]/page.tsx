import { SourceReader } from "@/components/reader/SourceReader";
import { DocumentReaderScreen } from "@/components/screens/phase5";
import { getRepository, resolveApiBaseUrl, resolveDataSource } from "@/data";
import { createReaderClient } from "@/data/reader";
import { MAX_HIGHLIGHT_LENGTH } from "@/lib/exact-source";
import { notFound } from "next/navigation";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const int = (value: string | undefined) =>
  value && /^\d+$/.test(value) ? Number(value) : undefined;

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
    line?: string;
    segment?: string;
    hl?: string;
    anchor?: string;
  }>;
}) {
  const { id } = await params;
  const query = await searchParams;
  const decoded = query.document ?? decodeURIComponent(id);
  const sourcePage = int(query.page);
  const pdfPageIndex = int(query.pdfPage);
  const para = int(query.para);
  const line = int(query.line);
  const segmentId = query.segment && UUID.test(query.segment) ? query.segment : undefined;
  const highlight = query.hl && query.hl.length <= MAX_HIGHLIGHT_LENGTH ? query.hl : undefined;
  if (
    resolveDataSource({ NEXT_PUBLIC_DATA_SOURCE: process.env.NEXT_PUBLIC_DATA_SOURCE }) === "mock"
  ) {
    return <DocumentReaderScreen id={decoded} initialPage={sourcePage ?? pdfPageIndex} />;
  }
  const repository = getRepository();
  const anchor =
    query.anchor && UUID.test(query.anchor) ? await repository.getSourceAnchor(query.anchor) : null;
  const document = await repository.getDocument(
    decoded,
    anchor?.officialVersionRef ?? query.version,
    anchor ? undefined : sourcePage,
    anchor?.pdfPageIndex ?? pdfPageIndex,
  );
  if (!document) notFound();
  // Fail closed: an anchor is only ever shown on its own exact version.
  if (anchor && document.versionRef !== anchor.officialVersionRef) notFound();
  const publicApi = resolveApiBaseUrl(
    { NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL },
    false,
  ).replace(/\/+$/, "");
  if (document.versionRef && document.artifactStatus === "fetched") {
    document.artifactUrl = `${publicApi}/api/v1/document-versions/${document.versionRef}/artifact`;
  }
  const versionRef = document.versionRef;
  const reader = createReaderClient(
    resolveApiBaseUrl(
      {
        NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
        API_INTERNAL_URL: process.env.API_INTERNAL_URL,
      },
      true,
    ),
  );
  const outline = versionRef ? await reader.outline(versionRef) : null;

  // Resolve the one PDF page this link names, in order of precision. A
  // transcript page/line or segment resolves through the version's own
  // segments; nothing is guessed from another version.
  let focusSegmentId = anchor?.transcriptSegmentId;
  let initialPdfPage = anchor?.pdfPageIndex ?? pdfPageIndex;
  if (
    outline &&
    versionRef &&
    (segmentId || (sourcePage !== undefined && initialPdfPage === undefined))
  ) {
    const located = await reader.segments(versionRef, {
      segment: segmentId,
      page: segmentId ? undefined : sourcePage,
      line: segmentId ? undefined : line,
      limit: 1,
    });
    const hit = located?.items[0];
    if (hit) {
      initialPdfPage ??= hit.pdfPageIndex;
      if (segmentId || line !== undefined) focusSegmentId ??= hit.id;
    }
  }
  initialPdfPage ??=
    document.paragraphs.find((paragraph) => paragraph.pdfPageIndex !== undefined)?.pdfPageIndex ??
    0;
  if (outline && versionRef && line !== undefined && sourcePage !== undefined && !focusSegmentId) {
    const located = await reader.segments(versionRef, { page: sourcePage, line, limit: 1 });
    focusSegmentId = located?.items[0]?.id;
  }

  const [initialContext, initialSegments, initialChunks] = versionRef
    ? await Promise.all([
        reader.context(versionRef, initialPdfPage).catch(() => null),
        outline
          ? reader.segments(versionRef, { pdfPageIndex: initialPdfPage, limit: 200 })
          : Promise.resolve(null),
        outline ? Promise.resolve([]) : reader.chunks(versionRef, initialPdfPage),
      ])
    : [null, null, []];

  return (
    <SourceReader
      // A new version or link target is a new Reader: no page, focus or
      // highlight state survives a client-side navigation between versions.
      key={`${versionRef ?? decoded}|${initialPdfPage}|${anchor?.id ?? ""}|${focusSegmentId ?? ""}`}
      routeId={id}
      document={document}
      apiBaseUrl={publicApi}
      initialPdfPage={initialPdfPage}
      initialPara={anchor?.paragraphNumber ?? para}
      initialLine={anchor?.lineFrom ?? line}
      highlight={anchor?.exactText ?? highlight}
      sourceAnchor={anchor ?? undefined}
      focusSegmentId={focusSegmentId}
      outline={outline}
      initialSegments={initialSegments}
      initialChunks={initialChunks}
      initialContext={initialContext}
    />
  );
}
