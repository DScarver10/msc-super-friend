"use client";

import { FormEvent, useMemo, useState } from "react";

type SearchHit = {
  chunk_id: string;
  title: string;
  snippet: string;
  page: number | null;
  section: string | null;
  subsection: string | null;
};

type SearchResponse = {
  query: string;
  count: number;
  results: SearchHit[];
};

type DocViewerClientProps = {
  filename: string;
  src: string;
  localUnavailable: boolean;
};

function buildViewerUrl(base: string, page: number | null, query: string): string {
  const parts: string[] = [];
  if (page !== null && Number.isFinite(page)) {
    parts.push(`page=${page}`);
  }
  if (query.trim()) {
    parts.push(`search=${encodeURIComponent(query.trim())}`);
  }
  if (parts.length === 0) {
    return base;
  }
  return `${base}#${parts.join("&")}`;
}

export function DocViewerClient({ filename, src, localUnavailable }: DocViewerClientProps) {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [results, setResults] = useState<SearchHit[]>([]);
  const [activeIndex, setActiveIndex] = useState<number>(-1);

  const viewerUrl = useMemo(() => {
    if (activeIndex < 0 || activeIndex >= results.length) {
      return buildViewerUrl(src, null, query);
    }
    return buildViewerUrl(src, results[activeIndex].page, query);
  }, [activeIndex, query, results, src]);

  async function runSearch(event: FormEvent) {
    event.preventDefault();
    const trimmed = query.trim();
    setSearchError(null);
    setResults([]);
    setActiveIndex(-1);
    if (!trimmed) {
      return;
    }

    setIsSearching(true);
    try {
      const response = await fetch(`/api/docs/${encodeURIComponent(filename)}/search?q=${encodeURIComponent(trimmed)}`);
      if (!response.ok) {
        throw new Error("Unable to search this document.");
      }
      const payload = (await response.json()) as SearchResponse;
      const hits = Array.isArray(payload.results) ? payload.results : [];
      setResults(hits);
      setActiveIndex(hits.length > 0 ? 0 : -1);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Search unavailable.";
      setSearchError(message);
    } finally {
      setIsSearching(false);
    }
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
            disabled={isSearching || !query.trim()}
            className="inline-flex min-h-10 items-center rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-500"
          >
            {isSearching ? "Searching..." : "Search"}
          </button>
        </div>
        {searchError ? <p className="mt-2 text-sm text-red-700">{searchError}</p> : null}
        {query.trim() && !isSearching ? (
          <p className="mt-2 text-xs text-slate-500">
            {results.length > 0
              ? `Found ${results.length} matches. Select a result to jump to the closest page in the viewer.`
              : "No exact matches found in indexed chunks for this document."}
          </p>
        ) : null}
      </form>

      {results.length > 0 ? (
        <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
          <ul className="max-h-64 space-y-2 overflow-auto">
            {results.map((hit, index) => {
              const locator = [
                hit.page !== null ? `p.${hit.page}` : null,
                hit.section ? `section ${hit.section}` : null,
                hit.subsection ? `subsection ${hit.subsection}` : null,
              ]
                .filter(Boolean)
                .join(" | ");
              const active = index === activeIndex;
              return (
                <li key={hit.chunk_id}>
                  <button
                    type="button"
                    onClick={() => setActiveIndex(index)}
                    className={`w-full rounded-lg border px-3 py-2 text-left text-sm transition ${
                      active
                        ? "border-amber-300 bg-amber-50 text-slate-900"
                        : "border-slate-200 bg-white text-slate-800 hover:bg-slate-50"
                    }`}
                  >
                    <p className="font-semibold">{hit.title}</p>
                    {locator ? <p className="mt-0.5 text-xs text-slate-500">{locator}</p> : null}
                    <p className="mt-1 text-xs text-slate-700">{hit.snippet}</p>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}

      {localUnavailable ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          This document is unavailable in the local docs bundle. Use the controls above to retry or open an external source.
        </div>
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <iframe
            title={`Viewer: ${filename}`}
            src={viewerUrl}
            className="h-[78vh] w-full border-0"
            loading="lazy"
            style={{ overflow: "auto", WebkitOverflowScrolling: "touch" }}
          />
        </div>
      )}
    </div>
  );
}

