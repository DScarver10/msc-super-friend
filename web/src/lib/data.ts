import "server-only";

import fs from "node:fs";
import path from "node:path";

import { doctrineMockItems, toolkitMockItems } from "@/data/mockData";

export type UiItem = {
  id: string;
  title: string;
  description: string;
  tag: string;
  type: "external" | "local";
  href: string;
  filename?: string;
};

type CsvRow = Record<string, string>;

const ACRONYMS = ["AFI", "DHA", "DOD", "AFMS", "MSC", "PDF"];

function pathExists(filePath: string): boolean {
  return fs.existsSync(filePath);
}

function resolveContentFile(relativePath: string): string | null {
  const candidates = [
    path.resolve(process.cwd(), "frontend", "content", relativePath),
    path.resolve(process.cwd(), "..", "frontend", "content", relativePath),
  ];

  for (const candidate of candidates) {
    if (pathExists(candidate)) {
      return candidate;
    }
  }

  return null;
}

function cleanText(value: string | null | undefined): string {
  if (!value) {
    return "";
  }
  return value.replace(/\s+/g, " ").trim();
}

function toSentenceCase(value: string | null | undefined): string {
  const cleaned = cleanText(value);
  if (!cleaned) {
    return "";
  }

  const lettersOnly = cleaned.replace(/[^A-Za-z]/g, "");
  let result = cleaned;

  if (lettersOnly && lettersOnly === lettersOnly.toUpperCase()) {
    const lower = cleaned.toLowerCase();
    result = lower.charAt(0).toUpperCase() + lower.slice(1);
  }

  for (const acronym of ACRONYMS) {
    result = result.replace(new RegExp(`\\b${acronym.toLowerCase()}\\b`, "gi"), acronym);
  }

  return result;
}

function toLinkInfo(rawHref: string | null | undefined): Pick<UiItem, "type" | "href" | "filename"> | null {
  const href = cleanText(rawHref);
  if (!href) {
    return null;
  }

  if (/^https?:\/\//i.test(href)) {
    return { type: "external", href };
  }

  const filename = path.basename(href);
  if (!filename) {
    return null;
  }

  return {
    type: "local",
    href: `/docs/${encodeURIComponent(filename)}`,
    filename,
  };
}

function normalizeFallback(items: Array<Omit<UiItem, "filename"> & { filename?: string }>): UiItem[] {
  return items.reduce<UiItem[]>((acc, item) => {
    const linkInfo = toLinkInfo(item.href);
    if (!linkInfo) {
      return acc;
    }

    acc.push({
      ...item,
      type: linkInfo.type,
      href: linkInfo.href,
      filename: linkInfo.filename,
    });

    return acc;
  }, []);
}

function parseCsv(csvText: string): CsvRow[] {
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = "";
  let inQuotes = false;

  for (let i = 0; i < csvText.length; i += 1) {
    const ch = csvText[i];
    const next = csvText[i + 1];

    if (ch === '"') {
      if (inQuotes && next === '"') {
        cell += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (ch === "," && !inQuotes) {
      row.push(cell);
      cell = "";
      continue;
    }

    if ((ch === "\n" || ch === "\r") && !inQuotes) {
      if (ch === "\r" && next === "\n") {
        i += 1;
      }
      row.push(cell);
      rows.push(row);
      row = [];
      cell = "";
      continue;
    }

    cell += ch;
  }

  if (cell.length > 0 || row.length > 0) {
    row.push(cell);
    rows.push(row);
  }

  if (rows.length < 2) {
    return [];
  }

  const headers = rows[0].map((h) => cleanText(h));
  return rows.slice(1).map((values) => {
    const mapped: CsvRow = {};
    headers.forEach((header, idx) => {
      mapped[header] = cleanText(values[idx]);
    });
    return mapped;
  });
}

export function getDoctrineItems(): UiItem[] {
  const fallback = normalizeFallback(doctrineMockItems);
  const csvPath = resolveContentFile("afi41_seed.csv");
  if (!csvPath) {
    return fallback;
  }

  try {
    const csvText = fs.readFileSync(csvPath, "utf-8");
    const rows = parseCsv(csvText);

    const items = rows.flatMap((row, idx): UiItem[] => {
      const pub = toSentenceCase(row.pub);
      const title = toSentenceCase(row.title);
      const tag = toSentenceCase(row.msc_functional_area) || "Doctrine";
      const linkInfo = toLinkInfo(row.official_publication_pdf);

      if (!linkInfo) {
        return [];
      }

      const combinedTitle = cleanText(pub ? `${pub} - ${title}` : title) || `Doctrine Item ${idx + 1}`;
      const description = `${tag} doctrine reference.`;

      return [
        {
          id: row.id || `doctrine-${idx + 1}`,
          title: combinedTitle,
          description,
          tag,
          type: linkInfo.type,
          href: linkInfo.href,
          filename: linkInfo.filename,
        },
      ];
    });

    return items.length > 0 ? items : fallback;
  } catch {
    return fallback;
  }
}

export function getToolkitItems(): UiItem[] {
  const fallback = normalizeFallback(toolkitMockItems);
  const jsonPath = resolveContentFile("toolkit.json");
  if (!jsonPath) {
    return fallback;
  }

  try {
    const parsed = JSON.parse(fs.readFileSync(jsonPath, "utf-8")) as Array<Record<string, unknown>>;

    const items = parsed.flatMap((entry, idx): UiItem[] => {
      const officialLinks = Array.isArray(entry.official_links) ? entry.official_links : [];
      const webLinks = Array.isArray(entry.web_links) ? entry.web_links : [];
      const files = Array.isArray(entry.files) ? entry.files : [];

      const preferredHref =
        (officialLinks[0] as { url?: string } | undefined)?.url ||
        (webLinks[0] as { url?: string } | undefined)?.url ||
        (files[0] as { path?: string } | undefined)?.path ||
        "";

      const linkInfo = toLinkInfo(preferredHref);
      if (!linkInfo) {
        return [];
      }

      const title = toSentenceCase((entry.title as string) || "") || `Toolkit Item ${idx + 1}`;
      const description =
        toSentenceCase((entry.summary as string) || (entry.description as string) || "") ||
        "Toolkit reference item.";
      const firstTag = Array.isArray(entry.tags) ? String(entry.tags[0] || "") : "";
      const tag =
        toSentenceCase((entry.type as string) || firstTag || (entry.category as string) || "") || "Toolkit";

      return [
        {
          id: String(entry.id || `toolkit-${idx + 1}`),
          title,
          description,
          tag,
          type: linkInfo.type,
          href: linkInfo.href,
          filename: linkInfo.filename,
        },
      ];
    });

    return items.length > 0 ? items : fallback;
  } catch {
    return fallback;
  }
}



