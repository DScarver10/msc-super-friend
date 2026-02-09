import "server-only";

import fs from "node:fs";
import path from "node:path";

import { toolkitMockItems } from "@/data/mockData";

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

const ACRONYMS = [
  "AFI",
  "DAFI",
  "AFMAN",
  "DAFMAN",
  "JTR",
  "DHA",
  "DAF",
  "DOD",
  "AFMS",
  "MSC",
  "PDF",
  "TOPA",
  "RMO",
  "MEPRS",
  "MEPERS",
];
const TITLECASE_SMALL_WORDS = new Set(["a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "of", "on", "or", "the", "to", "with"]);

function pathExists(filePath: string): boolean {
  return fs.existsSync(filePath);
}

function resolveContentFile(relativePath: string): string | null {
  const candidates = [
    path.resolve(process.cwd(), "public", "data", relativePath),
    path.resolve(process.cwd(), "web", "public", "data", relativePath),
    path.resolve(process.cwd(), "src", "data", relativePath),
    path.resolve(process.cwd(), "web", "src", "data", relativePath),
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

function titleCaseWordSegment(segment: string, isEdgeWord: boolean): string {
  if (!segment) {
    return segment;
  }

  const lower = segment.toLowerCase();
  const matchedAcronym = ACRONYMS.find((acronym) => acronym.toLowerCase() === lower);
  if (matchedAcronym) {
    return matchedAcronym;
  }

  if (!isEdgeWord && TITLECASE_SMALL_WORDS.has(lower)) {
    return lower;
  }

  if (!/[a-z]/i.test(segment)) {
    return segment;
  }

  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

function toPublicationTitleCase(value: string | null | undefined): string {
  const cleaned = cleanText(value);
  if (!cleaned) {
    return "";
  }

  const words = cleaned.split(/\s+/);
  return words
    .map((word, wordIndex) => {
      const isEdgeWord = wordIndex === 0 || wordIndex === words.length - 1;
      const parts = word.split(/([/-])/);
      return parts
        .map((part) => {
          if (part === "/" || part === "-") {
            return part;
          }
          return titleCaseWordSegment(part, isEdgeWord);
        })
        .join("");
    })
    .join(" ");
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
    href: buildLocalDocUrl(filename),
    filename,
  };
}

function apiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_BASE_URL || "").trim().replace(/\/$/, "");
}

function buildLocalDocUrl(filename: string): string {
  const base = apiBaseUrl();
  if (!base) {
    return `/docs/${encodeURIComponent(filename)}`;
  }
  return `${base}/docs/${encodeURIComponent(filename)}`;
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
  const csvPath = resolveContentFile("afi41_seed.csv");
  if (!csvPath) {
    return [];
  }

  try {
    const csvText = fs.readFileSync(csvPath, "utf-8");
    const rows = parseCsv(csvText);

    const items = rows.flatMap((row, idx): UiItem[] => {
      const pub = toPublicationTitleCase(row.pub);
      const title = toPublicationTitleCase(row.title);
      const tag = toSentenceCase(row.msc_functional_area) || "Doctrine";
      const linkInfo = toLinkInfo(row.official_publication_pdf);

      if (!linkInfo) {
        return [];
      }

      const combinedTitle = cleanText(pub ? `${pub} - ${title}` : title) || `Doctrine Item ${idx + 1}`;
      const description = "";

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

    return items;
  } catch {
    return [];
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

    if (items.length === 0) {
      return fallback;
    }

    const byTitle = (needle: string) => items.find((item) => item.title.toLowerCase().includes(needle.toLowerCase()));
    const used = new Set<string>();
    const pick = (needle: string, titleOverride?: string): UiItem | null => {
      const found = byTitle(needle);
      if (!found || used.has(found.id)) {
        return null;
      }
      used.add(found.id);
      return {
        ...found,
        title: titleOverride || found.title,
      };
    };

    const ordered: UiItem[] = [
      {
        id: "toolkit-afms-landing",
        title: "AFMS MSC Landing Page",
        description: "Official AFMS Medical Service Corps page.",
        tag: "Official",
        type: "external",
        href: "https://www.airforcemedicine.af.mil/About-Us/Medical-Branches/Medical-Service-Corps/",
      },
      {
        id: "toolkit-dha-strategy",
        title: "DHA Strategy Overview",
        description: "DHA strategic priorities and organizational direction.",
        tag: "Strategy",
        type: "external",
        href: "https://www.dha.mil/About-DHA/DHA-Strategy",
      },
    ];

    const selected = [
      pick("DHA Policies", "DHA Policy Reference Center"),
      pick("DoD Issuances", "DoD Instructions Directory"),
      pick("MSC Mentor Guide"),
      pick("AFMEDCOM Quick Reference", "AFMED Quick Reference"),
      pick("AFSC Officer Quick Reference", "AFSC Officer Quick Reference"),
      pick("AFSC Enlisted Quick Reference", "AFSC Enlisted Quick Reference"),
      pick("AFMS Manpower Reference Guide"),
      pick("MSC Accession Guide", "AY26 Accession Guide"),
      pick("DHA Network Structure"),
      pick("MSC Career Progression", "MSC Career Path"),
    ].filter((item): item is UiItem => item !== null);

    return [...ordered, ...selected];
  } catch {
    return fallback;
  }
}



