"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { useState } from "react";
import { ChevronRightIcon, DocumentIcon, InfoIcon, ShareIcon, StarIcon } from "@/components/icons";

type ToastState = {
  message: string;
  tone: "ok" | "warn";
} | null;

function SettingsRow({
  icon,
  label,
  onClick,
  href,
}: {
  icon: ReactNode;
  label: string;
  onClick?: () => void;
  href?: string;
}) {
  const content = (
    <div className="flex w-full items-center justify-between p-4">
      <div className="flex items-center gap-3">
        <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-msc-slate">{icon}</span>
        <span className="text-sm font-medium text-slate-900">{label}</span>
      </div>
      <ChevronRightIcon className="h-4 w-4 text-msc-muted" />
    </div>
  );

  if (href) {
    return (
      <Link href={href} className="block border-b border-slate-200 last:border-b-0">
        {content}
      </Link>
    );
  }

  return (
    <button type="button" onClick={onClick} className="w-full border-b border-slate-200 text-left last:border-b-0">
      {content}
    </button>
  );
}

export default function SettingsPage() {
  const [toast, setToast] = useState<ToastState>(null);
  const rateUrl = (process.env.NEXT_PUBLIC_RATE_URL || "").trim();
  const appVersion = (process.env.NEXT_PUBLIC_APP_VERSION || "").trim() || "dev";

  async function handleShare() {
    const url = typeof window !== "undefined" ? window.location.origin : "";
    const shareData = {
      title: "MSC Super Friend",
      text: "MSC Super Friend",
      url,
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
        setToast({ message: "Share sheet opened.", tone: "ok" });
      } else if (navigator.clipboard && url) {
        await navigator.clipboard.writeText(url);
        setToast({ message: "App URL copied to clipboard.", tone: "ok" });
      } else {
        setToast({ message: "Share is unavailable on this device.", tone: "warn" });
      }
    } catch {
      setToast({ message: "Share was canceled or unavailable.", tone: "warn" });
    }
  }

  function handleRate() {
    if (!rateUrl) {
      setToast({ message: "Rate URL is not configured yet.", tone: "warn" });
      return;
    }
    window.open(rateUrl, "_blank", "noopener,noreferrer");
  }

  return (
    <section className="space-y-4">
      <h2 className="text-lg font-semibold text-msc-navy sm:text-xl">Settings</h2>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <SettingsRow icon={<StarIcon className="h-4 w-4" />} label="Rate app" onClick={handleRate} />
        <SettingsRow icon={<ShareIcon className="h-4 w-4" />} label="Share app" onClick={handleShare} />
        <SettingsRow icon={<DocumentIcon className="h-4 w-4" />} label="Privacy policy" href="/privacy" />
        <SettingsRow icon={<InfoIcon className="h-4 w-4" />} label="About" href="/about" />
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600 shadow-sm">
        <p className="font-medium text-slate-700">Version</p>
        <p>{appVersion}</p>
      </div>

      {toast ? (
        <div
          role="status"
          className={`rounded-lg border px-3 py-2 text-sm ${
            toast.tone === "ok" ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-amber-200 bg-amber-50 text-amber-700"
          }`}
        >
          {toast.message}
        </div>
      ) : null}
    </section>
  );
}
