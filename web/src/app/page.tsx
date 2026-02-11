import Link from "next/link";

const QUICK_LINKS = [
  {
    href: "/doctrine-library",
    title: "Doctrine Library",
    description: "Browse official publications and open the in-app document viewer.",
    tone: "bg-slate-100 text-slate-900",
  },
  {
    href: "/msc-toolkit",
    title: "MSC Toolkit",
    description: "Access high-value references and quick links for daily operations.",
    tone: "bg-[#5a0013] text-white",
  },
  {
    href: "/ask-super-friend",
    title: "Ask Super Companion",
    description: "Ask a policy question and review citations in one place.",
    tone: "bg-msc-navy text-white",
  },
];

export default function HomePage() {
  return (
    <section className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-3">
        {QUICK_LINKS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`rounded-xl border border-slate-200 p-4 shadow-sm transition hover:opacity-95 ${item.tone}`}
          >
            <p className="text-base font-semibold">{item.title}</p>
            <p className="mt-2 text-sm opacity-90">{item.description}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
