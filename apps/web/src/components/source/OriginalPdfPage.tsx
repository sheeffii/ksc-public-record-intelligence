"use client";

import { useEffect, useRef, useState } from "react";
import type { SourceRegionView } from "@/data";

export type PdfFit = "width" | "page" | "custom";

/** Validated regions to draw on the current page, in canonical PDF points. */
export interface PdfHighlight {
  key: string;
  regions: readonly SourceRegionView[];
  pageWidth: number;
  pageHeight: number;
  label: string;
}

type PdfDocument = Awaited<ReturnType<(typeof import("pdfjs-dist"))["getDocument"]>["promise"]>;

// One loading task per artifact URL: page changes reuse the already-opened
// document (and its ranged byte cache) instead of re-fetching the PDF.
const documents = new Map<string, Promise<PdfDocument>>();
const MAX_OPEN_DOCUMENTS = 3;

async function openDocument(url: string): Promise<PdfDocument> {
  const cached = documents.get(url);
  if (cached) return cached;
  const pending = (async () => {
    const pdfjs = await import("pdfjs-dist");
    pdfjs.GlobalWorkerOptions.workerSrc = new URL(
      "pdfjs-dist/build/pdf.worker.min.mjs",
      import.meta.url,
    ).toString();
    return pdfjs.getDocument({ url, withCredentials: false }).promise;
  })();
  documents.set(url, pending);
  pending.catch(() => documents.delete(url));
  while (documents.size > MAX_OPEN_DOCUMENTS) {
    const oldest = documents.keys().next().value as string;
    const evicted = documents.get(oldest);
    documents.delete(oldest);
    void evicted?.then((pdf) => pdf.destroy()).catch(() => undefined);
  }
  return pending;
}

export function OriginalPdfPage({
  url,
  pageIndex,
  fit,
  zoom,
  highlight,
  pageSize,
  onPointClick,
  onPageCount,
  onScale,
  onError,
}: {
  url: string;
  pageIndex: number;
  fit: PdfFit;
  zoom: number;
  highlight?: PdfHighlight;
  /** Persisted canonical page size, needed to map a click back to PDF points. */
  pageSize?: { width: number; height: number };
  /** Click position in canonical top-left PDF points (reverse synchronization). */
  onPointClick?: (x: number, y: number) => void;
  onPageCount: (count: number) => void;
  onScale: (scale: number) => void;
  onError: (message: string) => void;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [viewport, setViewport] = useState<{ width: number; height: number; page: number }>();
  const [layoutRevision, setLayoutRevision] = useState(0);

  useEffect(() => {
    if (!hostRef.current || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(() => setLayoutRevision((value) => value + 1));
    observer.observe(hostRef.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    let cancelled = false;
    let cancelRender: (() => void) | undefined;
    const render = async () => {
      try {
        const pdf = await openDocument(url);
        if (cancelled) return;
        onPageCount(pdf.numPages);
        const safePage = Math.min(Math.max(1, pageIndex + 1), pdf.numPages);
        const page = await pdf.getPage(safePage);
        const base = page.getViewport({ scale: 1 });
        const hostWidth = Math.max(280, (hostRef.current?.clientWidth ?? base.width) - 2);
        const hostHeight = Math.max(420, Math.min(window.innerHeight - 220, 900));
        const scale =
          fit === "width"
            ? hostWidth / base.width
            : fit === "page"
              ? Math.min(hostWidth / base.width, hostHeight / base.height)
              : zoom;
        const nextViewport = page.getViewport({ scale });
        onScale(scale);
        const canvas = canvasRef.current;
        if (!canvas || cancelled) return;
        const ratio = window.devicePixelRatio || 1;
        canvas.width = Math.floor(nextViewport.width * ratio);
        canvas.height = Math.floor(nextViewport.height * ratio);
        canvas.style.width = `${nextViewport.width}px`;
        canvas.style.height = `${nextViewport.height}px`;
        const context = canvas.getContext("2d");
        if (!context) throw new Error("Canvas rendering is unavailable");
        const task = page.render({
          canvas,
          canvasContext: context,
          viewport: nextViewport,
          transform: ratio === 1 ? undefined : [ratio, 0, 0, ratio, 0, 0],
        });
        cancelRender = () => task.cancel();
        await task.promise;
        if (!cancelled) {
          setViewport({ width: nextViewport.width, height: nextViewport.height, page: pageIndex });
        }
      } catch (error) {
        if (cancelled) return;
        if (error instanceof Error && error.name === "RenderingCancelledException") return;
        onError(error instanceof Error ? error.message : "PDF rendering failed");
      }
    };
    void render();
    return () => {
      cancelled = true;
      cancelRender?.();
    };
  }, [url, pageIndex, fit, zoom, layoutRevision, onPageCount, onScale, onError]);

  const rendered = viewport && viewport.page === pageIndex ? viewport : undefined;
  const highlightKey = highlight?.key;
  useEffect(() => {
    if (!rendered || !highlightKey) return;
    hostRef.current
      ?.querySelector("[data-source-region]")
      ?.scrollIntoView?.({ block: "center", inline: "nearest" });
  }, [rendered, highlightKey]);

  return (
    <div ref={hostRef} className="relative flex min-h-[520px] w-full justify-center overflow-auto">
      <div
        className="shadow-page relative shrink-0"
        data-pdf-rendered={rendered ? "true" : "false"}
        style={rendered ? { width: rendered.width, height: rendered.height } : undefined}
      >
        <canvas
          ref={canvasRef}
          aria-label={`PDF page ${pageIndex + 1}`}
          className="bg-surface block"
          onClick={(event) => {
            if (!onPointClick || !rendered || !pageSize) return;
            const box = event.currentTarget.getBoundingClientRect();
            onPointClick(
              ((event.clientX - box.left) / box.width) * pageSize.width,
              ((event.clientY - box.top) / box.height) * pageSize.height,
            );
          }}
        />
        {highlight && rendered
          ? highlight.regions.map((region, index) => (
              <span
                key={`${highlight.key}-${index}`}
                data-source-region
                title={highlight.label}
                className="ring-accent bg-surface-high/40 pointer-events-none absolute rounded-sm ring-2"
                style={{
                  left: `${(region.x / highlight.pageWidth) * rendered.width}px`,
                  top: `${(region.y / highlight.pageHeight) * rendered.height}px`,
                  width: `${(region.width / highlight.pageWidth) * rendered.width}px`,
                  height: `${(region.height / highlight.pageHeight) * rendered.height}px`,
                }}
              />
            ))
          : null}
      </div>
    </div>
  );
}
