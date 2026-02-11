import fs from "node:fs/promises";
import path from "node:path";

import { NextRequest, NextResponse } from "next/server";

const CONTENT_TYPE_BY_EXT: Record<string, string> = {
  ".pdf": "application/pdf",
  ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  ".csv": "text/csv; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".txt": "text/plain; charset=utf-8",
};

function safeFilename(value: string): string | null {
  const normalized = path.basename(value).trim();
  if (!normalized || normalized.includes("..")) {
    return null;
  }
  return normalized;
}

export async function GET(
  request: NextRequest,
  context: { params: { filename: string } },
) {
  const filename = safeFilename(decodeURIComponent(context.params.filename));
  if (!filename) {
    return NextResponse.json({ error: "Invalid file name." }, { status: 400 });
  }

  const candidatePaths = [
    path.resolve(process.cwd(), "public", "docs", filename),
    path.resolve(process.cwd(), "web", "public", "docs", filename),
    path.resolve(process.cwd(), "backend", "data", "toolkit_docs", filename),
    path.resolve(process.cwd(), "..", "backend", "data", "toolkit_docs", filename),
  ];

  for (const candidate of candidatePaths) {
    try {
      const file = await fs.readFile(candidate);
      const ext = path.extname(filename).toLowerCase();
      const forceDownload = (request.nextUrl.searchParams.get("download") || "").trim() === "1";
      const disposition = forceDownload ? "attachment" : "inline";
      return new NextResponse(file, {
        status: 200,
        headers: {
          "Content-Type": CONTENT_TYPE_BY_EXT[ext] || "application/octet-stream",
          "Content-Disposition": `${disposition}; filename="${filename}"`,
          "Access-Control-Allow-Origin": "*",
          "Cache-Control": "public, max-age=3600",
        },
      });
    } catch {
      // Try next location.
    }
  }

  return NextResponse.json({ error: "Document not found." }, { status: 404 });
}
