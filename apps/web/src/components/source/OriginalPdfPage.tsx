"use client";

import { useEffect, useRef, useState } from "react";
import type { SourceAnchorView } from "@/data";

export type PdfFit = "width" | "page" | "custom";

export function OriginalPdfPage({
  url,
  pageIndex,
  fit,
  zoom,
  anchor,
  onPageCount,
  onScale,
  onError,
}: {
  url: string;
  pageIndex: number;
  fit: PdfFit;
  zoom: number;
  anchor?: SourceAnchorView;
  onPageCount: (count: number) => void;
  onScale: (scale: number) => void;
  onError: (message: string) => void;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [viewport, setViewport] = useState<{ width: number; height: number }>();
  const [layoutRevision, setLayoutRevision] = useState(0);

  useEffect(() => {
    if (!hostRef.current || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(() => setLayoutRevision((value) => value + 1));
    observer.observe(hostRef.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    let cancelled = false;
    let destroyLoadingTask: (() => Promise<void>) | undefined;
    const render = async () => {
      try {
        const pdfjs = await import("pdfjs-dist");
        pdfjs.GlobalWorkerOptions.workerSrc = new URL(
          "pdfjs-dist/build/pdf.worker.min.mjs",
          import.meta.url,
        ).toString();
        const loadingTask = pdfjs.getDocument({ url, withCredentials: false });
        destroyLoadingTask = () => loadingTask.destroy();
        const pdf = await loadingTask.promise;
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
        await page.render({
          canvas,
          canvasContext: context,
          viewport: nextViewport,
          transform: ratio === 1 ? undefined : [ratio, 0, 0, ratio, 0, 0],
        }).promise;
        if (!cancelled) setViewport({ width: nextViewport.width, height: nextViewport.height });
      } catch (error) {
        if (!cancelled) onError(error instanceof Error ? error.message : "PDF rendering failed");
      }
    };
    void render();
    return () => {
      cancelled = true;
      void destroyLoadingTask?.();
    };
  }, [url, pageIndex, fit, zoom, layoutRevision, onPageCount, onScale, onError]);

  const exact =
    anchor &&
    (anchor.precision === "exact_geometry" || anchor.precision === "ocr_geometry") &&
    anchor.pdfPageIndex === pageIndex &&
    anchor.pageWidth &&
    anchor.pageHeight;

  return (
    <div ref={hostRef} className="relative flex min-h-[520px] w-full justify-center overflow-auto">
      <div
        className="shadow-page relative shrink-0"
        data-pdf-rendered={viewport ? "true" : "false"}
        style={viewport}
      >
        <canvas
          ref={canvasRef}
          aria-label={`PDF page ${pageIndex + 1}`}
          className="bg-surface block"
        />
        {exact && viewport
          ? anchor.regions.map((region, index) => (
              <span
                key={`${region.x}-${region.y}-${index}`}
                data-source-region
                className="ring-accent bg-surface-high/40 pointer-events-none absolute rounded-sm ring-2"
                style={{
                  left: `${(region.x / anchor.pageWidth!) * viewport.width}px`,
                  top: `${(region.y / anchor.pageHeight!) * viewport.height}px`,
                  width: `${(region.width / anchor.pageWidth!) * viewport.width}px`,
                  height: `${(region.height / anchor.pageHeight!) * viewport.height}px`,
                }}
              />
            ))
          : null}
      </div>
    </div>
  );
}
