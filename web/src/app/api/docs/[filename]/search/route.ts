import fs from "node:fs/promises";
import path from "node:path";

import { NextRequest, NextResponse } from "next/server";

type MetaRecord = {
  chunk_id: string;
  source_id?: string;
  title?: string;
  text?: string;
  url?: string;
  local_path?: string;
  page?: number | null;
  section?: string | null;
  subsection?: string | null;
};

function safeFilename(value: string): string | null {
  const normalized = path.basename(value).trim();
  if (!normalized || normalized.includes("..")) {
    return null;
  }
  return normalized;
}

async function loadMetaRecords(): Promise<MetaRecord[]> {
  const candidates = [
    path.resolve(process.cwd(), "backend", "data", "index", "meta.json"),
    path.resolve(process.cwd(), "..", "backend", "data", "index", "meta.json"),
  ];

  for (const candidate of candidates) {
    try {
      const raw = await fs.readFile(candidate, "utf-8");
      const parsed = JSON.parse(raw) as MetaRecord[];
      if (Array.isArray(parsed)) {
        return parsed;
      }
    } catch {
      // Try next location.
    }
  }

  return [];
}

function scoreChunk(text: string, queryTerms: string[]): number {
  const haystack = text.toLowerCase();
  let score = 0;
  for (const term of queryTerms) {
    if (!term) {
      continue;
    }
    let idx = haystack.indexOf(term);
    while (idx !== -1) {
      score += 1;
      idx = haystack.indexOf(term, idx + term.length);
    }
  }
  return score;
}

function buildSnippet(text: string, query: string, maxLen = 260): string {
  const clean = text.replace(/\s+/g, " ").trim();
  if (!clean) {
    return "";
  }
  const normalized = clean.toLowerCase();
  const needle = query.toLowerCase();
  const hitIndex = normalized.indexOf(needle);
  if (hitIndex < 0) {
    return clean.slice(0, maxLen);
  }

  const start = Math.max(0, hitIndex - 80);
  const end = Math.min(clean.length, hitIndex + needle.length + 120);
  const snippet = clean.slice(start, end).trim();
  return `${start > 0 ? "... " : ""}${snippet}${end < clean.length ? " ..." : ""}`;
}

export async function GET(request: NextRequest, context: { params: { filename: string } }) {
  const filename = safeFilename(decodeURIComponent(context.params.filename));
  if (!filename) {
    return NextResponse.json({ error: "Invalid file name." }, { status: 400 });
  }

  const query = (request.nextUrl.searchParams.get("q") || "").trim();
  if (!query) {
    return NextResponse.json({ query: "", count: 0, results: [] });
  }

  const terms = query
    .toLowerCase()
    .split(/\s+/)
    .map((term) => term.trim())
    .filter((term) => term.length >= 2);

  const basenameNoExt = path.parse(filename).name.toLowerCase();
  const records = await loadMetaRecords();
  const matches = records.filter((record) => {
    const source = `${record.source_id || ""} ${record.url || ""} ${record.local_path || ""}`.toLowerCase();
    return source.includes(filename.toLowerCase()) || source.includes(basenameNoExt);
  });

  const scored = matches
    .map((record) => {
      const text = (record.text || "").trim();
      const score = scoreChunk(text, terms);
      return { record, score };
    })
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 20)
    .map(({ record }) => ({
      chunk_id: record.chunk_id,
      title: (record.title || filename).trim(),
      snippet: buildSnippet(record.text || "", query),
      page: typeof record.page === "number" ? record.page : null,
      section: record.section || null,
      subsection: record.subsection || null,
    }));

  return NextResponse.json({
    query,
    count: scored.length,
    results: scored,
  });
}

