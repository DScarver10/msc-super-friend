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
  pub?: string | null;
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

function normalizeKey(value: string): string {
  return (value || "").toLowerCase().replace(/[^a-z0-9]/g, "");
}

function buildDocAliases(filename: string): string[] {
  const lower = filename.toLowerCase();
  const noExt = path.parse(lower).name;
  const aliases = new Set<string>([lower, noExt, normalizeKey(lower), normalizeKey(noExt)]);

  const policyMatch = noExt.match(/^([a-z]+)\s*(\d{1,2})[-_ ]?(\d{2,4}(?:\.\d+)?)$/i);
  if (policyMatch) {
    const prefix = policyMatch[1].toUpperCase();
    const partA = policyMatch[2];
    const partB = policyMatch[3];
    aliases.add(`${prefix} ${partA}-${partB}`.toLowerCase());
    aliases.add(`${prefix}${partA}-${partB}`.toLowerCase());
    aliases.add(normalizeKey(`${prefix}${partA}-${partB}`));
    aliases.add(normalizeKey(`${prefix} ${partA}-${partB}`));
  }

  return Array.from(aliases).filter(Boolean);
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

function exactMatchCount(text: string, query: string): number {
  const haystack = (text || "").toLowerCase();
  const needle = (query || "").toLowerCase().trim();
  if (!needle) {
    return 0;
  }
  let count = 0;
  let idx = haystack.indexOf(needle);
  while (idx !== -1) {
    count += 1;
    idx = haystack.indexOf(needle, idx + needle.length);
  }
  return count;
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

  const aliases = buildDocAliases(filename);
  const records = await loadMetaRecords();
  const matches = records.filter((record) => {
    const source = `${record.source_id || ""} ${record.title || ""} ${record.pub || ""} ${record.url || ""} ${
      record.local_path || ""
    }`.toLowerCase();
    const sourceNorm = normalizeKey(source);
    return aliases.some((alias) => source.includes(alias) || sourceNorm.includes(normalizeKey(alias)));
  });

  const exactScored = matches
    .map((record) => {
      const text = (record.text || "").trim();
      const score = exactMatchCount(text, query);
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

  if (exactScored.length > 0) {
    return NextResponse.json({
      query,
      count: exactScored.length,
      match_type: "exact",
      results: exactScored,
    });
  }

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
    match_type: "token",
    results: scored,
  });
}
