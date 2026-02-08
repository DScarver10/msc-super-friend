import Link from "next/link";
import { BackArrowIcon } from "@/components/icons";

export default function AboutPage() {
  const version = (process.env.NEXT_PUBLIC_APP_VERSION || "").trim() || "dev";

  return (
    <article className="space-y-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
      <Link href="/settings" className="inline-flex items-center gap-1 text-sm font-medium text-msc-navy">
        <BackArrowIcon className="h-4 w-4" />
        Back
      </Link>

      <header className="space-y-2">
        <h2 className="text-xl font-semibold text-msc-navy">About</h2>
        <p className="text-sm leading-6 text-slate-700">
          MSC Super Friend - Your trusted friend for navigating policy, guidance, and everyday tools.
        </p>
      </header>

      <section className="space-y-1 text-sm text-slate-600">
        <p>
          <span className="font-semibold text-slate-800">Build version:</span> {version}
        </p>
        <p>
          <Link href="/privacy" className="font-medium text-msc-navy underline underline-offset-2">
            Privacy Policy
          </Link>
        </p>
      </section>
    </article>
  );
}

