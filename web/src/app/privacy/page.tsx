import Link from "next/link";
import { BackArrowIcon } from "@/components/icons";

const lastUpdated = "February 8, 2026";

export default function PrivacyPage() {
  return (
    <article className="space-y-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
      <Link href="/settings" className="inline-flex items-center gap-1 text-sm font-medium text-msc-navy">
        <BackArrowIcon className="h-4 w-4" />
        Back
      </Link>

      <header>
        <h2 className="text-xl font-semibold text-msc-navy">Privacy Policy</h2>
        <p className="mt-1 text-sm text-slate-500">Last updated: {lastUpdated}</p>
      </header>

      <section className="space-y-2 text-sm leading-6 text-slate-700">
        <h3 className="text-base font-semibold text-slate-900">Scope</h3>
        <p>
          MSC Super Friend is a reference assistant for policy and guidance navigation. It is designed for public-source
          content only.
        </p>
      </section>

      <section className="space-y-2 text-sm leading-6 text-slate-700">
        <h3 className="text-base font-semibold text-slate-900">Data handling</h3>
        <p>
          Questions may be sent to backend services for retrieval and response generation. Avoid entering protected or
          sensitive personal information.
        </p>
        <p>Public sources only; do not enter PHI/PII.</p>
      </section>

      <section className="space-y-2 text-sm leading-6 text-slate-700">
        <h3 className="text-base font-semibold text-slate-900">Links and references</h3>
        <p>External links may direct to government or public sites outside this application. Review those sites separately.</p>
      </section>
    </article>
  );
}

