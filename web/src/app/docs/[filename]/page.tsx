import fs from "node:fs";
import path from "node:path";

import Link from "next/link";
import { DocViewerClient } from "@/components/DocViewerClient";

type DocsPageProps = {
  params: {
    filename: string;
  };
  searchParams?: {
    from?: string;
  };
};

function resolveLocalDoc(filename: string): string | null {
  const safe = path.basename(filename).trim();
  if (!safe) {
    return null;
  }

  const candidatePaths = [
    path.resolve(process.cwd(), "public", "docs", safe),
    path.resolve(process.cwd(), "web", "public", "docs", safe),
    path.resolve(process.cwd(), "backend", "data", "toolkit_docs", safe),
    path.resolve(process.cwd(), "..", "backend", "data", "toolkit_docs", safe),
  ];

  const found = candidatePaths.find((candidate) => fs.existsSync(candidate));
  return found || null;
}

function buildSourceUrl(filename: string): string {
  return `/api/docs/${encodeURIComponent(filename)}`;
}

function buildDownloadUrl(filename: string): string {
  return `/api/docs/${encodeURIComponent(filename)}?download=1`;
}

export default function DocsViewerPage({ params, searchParams }: DocsPageProps) {
  const filename = decodeURIComponent(params.filename);
  const src = buildSourceUrl(filename);
  const downloadUrl = buildDownloadUrl(filename);
  const localDocPath = resolveLocalDoc(filename);
  const localUnavailable = !localDocPath;
  const from = (searchParams?.from || "").toLowerCase();
  const backHref = from === "toolkit" ? "/msc-toolkit" : "/doctrine-library";
  const backLabel = from === "toolkit" ? "Back to toolkit" : "Back to library";

  return (
    <section className="space-y-4">
      <header className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Document Viewer</p>
        <h2 className="mt-1 text-base font-semibold text-slate-900 sm:text-lg">{filename}</h2>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <a
            href={src}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-800"
          >
            Open in new tab
          </a>
          <a
            href={downloadUrl}
            download={filename}
            className="inline-flex items-center rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
          >
            Download
          </a>
          <Link
            href={backHref}
            className="inline-flex items-center rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
          >
            {backLabel}
          </Link>
        </div>
      </header>
      <DocViewerClient filename={filename} src={src} localUnavailable={localUnavailable} />
    </section>
  );
}
