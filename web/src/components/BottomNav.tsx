"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

type Tab = {
  href: string;
  label: string;
  match: string[];
  icon: (className?: string) => ReactNode;
};

function baseIconPath(className?: string) {
  return `h-5 w-5 ${className || ""}`;
}

const HomeIcon = (className?: string) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={baseIconPath(className)}>
    <path d="M3 10.5 12 3l9 7.5" />
    <path d="M5 9.5V21h14V9.5" />
  </svg>
);

const BookIcon = (className?: string) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={baseIconPath(className)}>
    <path d="M4 5a2 2 0 0 1 2-2h14v17H6a2 2 0 0 0-2 2V5Z" />
    <path d="M8 7h8M8 11h8" />
  </svg>
);

const ToolkitIcon = (className?: string) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={baseIconPath(className)}>
    <path d="M3 8h18v11H3z" />
    <path d="M9 8V6a3 3 0 0 1 6 0v2" />
    <path d="M10.5 13h3" />
  </svg>
);

const AskIcon = (className?: string) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={baseIconPath(className)}>
    <path d="M4 5h16v11H8l-4 3V5Z" />
    <path d="M8 9h8M8 12h5" />
  </svg>
);

const SettingsIcon = (className?: string) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={baseIconPath(className)}>
    <path d="M12 9.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5Z" />
    <path d="M19.4 15a1 1 0 0 0 .2 1.1l.1.1a2 2 0 0 1-2.8 2.8l-.1-.1a1 1 0 0 0-1.1-.2 1 1 0 0 0-.6.9V20a2 2 0 1 1-4 0v-.2a1 1 0 0 0-.6-.9 1 1 0 0 0-1.1.2l-.1.1a2 2 0 0 1-2.8-2.8l.1-.1a1 1 0 0 0 .2-1.1 1 1 0 0 0-.9-.6H4a2 2 0 1 1 0-4h.2a1 1 0 0 0 .9-.6 1 1 0 0 0-.2-1.1l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1 1 0 0 0 1.1.2 1 1 0 0 0 .6-.9V4a2 2 0 1 1 4 0v.2a1 1 0 0 0 .6.9 1 1 0 0 0 1.1-.2l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1 1 0 0 0-.2 1.1 1 1 0 0 0 .9.6H20a2 2 0 1 1 0 4h-.2a1 1 0 0 0-.9.6Z" />
  </svg>
);

const tabs: Tab[] = [
  { href: "/", label: "Home", match: ["/"], icon: HomeIcon },
  { href: "/doctrine-library", label: "Doctrine", match: ["/doctrine-library"], icon: BookIcon },
  { href: "/msc-toolkit", label: "Toolkit", match: ["/msc-toolkit"], icon: ToolkitIcon },
  { href: "/ask-super-friend", label: "Ask", match: ["/ask-super-friend"], icon: AskIcon },
  { href: "/settings", label: "Settings", match: ["/settings", "/privacy", "/about"], icon: SettingsIcon },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200 bg-white/95 backdrop-blur sm:hidden">
      <ul className="mx-auto flex max-w-5xl items-center justify-between px-2 py-1">
        {tabs.map((tab) => {
          const active = tab.match.some((m) => pathname === m || (m !== "/" && pathname.startsWith(`${m}/`)));
          const textClass = active ? "text-msc-burgundy" : "text-msc-slate";
          return (
            <li key={tab.href} className="flex-1">
              <Link
                href={tab.href}
                className={`flex min-h-14 w-full flex-col items-center justify-center gap-1 rounded-lg text-xs font-medium ${textClass}`}
              >
                {tab.icon()}
                <span>{tab.label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
