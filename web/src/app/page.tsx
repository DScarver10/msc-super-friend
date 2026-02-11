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

const MSC_MEDIA = [
  {
    href: "https://www.facebook.com/groups/1894257714034507/",
    label: "Facebook",
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" className="h-5 w-5">
        <path d="M13.5 8.5V6.9c0-.8.2-1.2 1.3-1.2H16V3h-1.9c-2.3 0-3.6 1-3.6 3.5v2h-2v2.8h2V21h3V11.3h2.2l.3-2.8h-2.5Z" />
      </svg>
    ),
  },
  {
    href: "https://www.linkedin.com/company/usafmsc",
    label: "LinkedIn",
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" className="h-5 w-5">
        <path d="M6.5 8.6A1.8 1.8 0 1 1 6.5 5a1.8 1.8 0 0 1 0 3.6ZM5 10h3v9H5v-9Zm5 0h2.9v1.2h.1c.4-.7 1.4-1.5 2.9-1.5 3.1 0 3.7 2 3.7 4.7V19h-3v-4.1c0-1-.1-2.2-1.5-2.2s-1.7 1-1.7 2.2V19h-3v-9Z" />
      </svg>
    ),
  },
  {
    href: "https://seat41a.com/",
    label: "Podcast",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true" className="h-5 w-5">
        <circle cx="12" cy="10" r="2.7" />
        <path d="M8 14a5.5 5.5 0 0 1 8 0M5.8 16.3a8.8 8.8 0 0 1 12.4 0M11 14.8v4.3a1 1 0 0 0 2 0v-4.3" />
      </svg>
    ),
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

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">MSC Media</p>
        <div className="mt-3 flex flex-nowrap items-center gap-3 overflow-x-auto pb-1">
          {MSC_MEDIA.map((item) => (
            <a
              key={item.label}
              href={item.href}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={item.label}
              className="inline-flex shrink-0 items-center gap-2 whitespace-nowrap rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400"
            >
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-white text-slate-700 shadow-sm">
                {item.icon}
              </span>
              {item.label}
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
