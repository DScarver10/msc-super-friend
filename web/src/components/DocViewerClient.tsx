"use client";

import { FormEvent, useMemo, useState } from "react";

type DocViewerClientProps = {
  filename: string;
  src: string;
  localUnavailable: boolean;
};

function buildNativeViewerUrl(fileUrl: string, search: string): string {
  const base = fileUrl;
  const trimmed = search.trim();
  if (!trimmed) {
    return base;
  }
  return `${base}#search=${encodeURIComponent(trimmed)}`;
}

export function DocViewerClient({ filename, src, localUnavailable }: DocViewerClientProps) {
  const [query, setQuery] = useState("");
  const [appliedQuery, setAppliedQuery] = useState("");
  const viewerUrl = useMemo(() => buildNativeViewerUrl(src, appliedQuery), [src, appliedQuery]);

  function runSearch(event: FormEvent) {
    event.preventDefault();
    setAppliedQuery(query.trim());
  }

  return (
    <div className="space-y-4">
      <form onSubmit={runSearch} className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
        <label htmlFor="doc-search" className="mb-2 block text-sm font-medium text-slate-900">
          Find in document
        </label>
        <div className="flex flex-wrap items-center gap-2">
          <input
            id="doc-search"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search this document for exact references"
            className="min-w-[220px] flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-500 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-200"
          />
          <button
            type="submit"
            disabled={!query.trim()}
            className="inline-flex min-h-10 items-center rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-500"
          >
            Find
          </button>
        </div>
        <div className="mt-2 rounded-lg border border-slate-200 bg-slate-50 p-2 text-xs text-slate-700">
          This Find bar passes your search term to the viewer when supported. For most accurate word finding, tap
          <span className="font-semibold"> Open in new tab</span> and use browser find:
          Safari <span className="font-semibold">Share to Find on Page</span>, Chrome
          <span className="font-semibold"> menu to Find in page</span>.
        </div>
        {appliedQuery ? (
          <p className="mt-2 text-xs text-slate-500">
            Applied find term: <span className="font-semibold">{appliedQuery}</span>
          </p>
        ) : null}
      </form>

      {localUnavailable ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          This document is unavailable in the local docs bundle. Use the controls above to retry or open an external source.
        </div>
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <object data={viewerUrl} type="application/pdf" className="h-[82vh] min-h-[680px] w-full">
            <iframe
              title={`Viewer: ${filename}`}
              src={viewerUrl}
              className="h-[82vh] min-h-[680px] w-full border-0"
              loading="lazy"
            />
          </object>
        </div>
      )}
    </div>
  );
}
