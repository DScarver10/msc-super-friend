import type { Metadata } from "next";
import Link from "next/link";
import { BottomNav } from "@/components/BottomNav";
import { GearIcon } from "@/components/icons";
import { ServiceWorkerRegister } from "@/components/ServiceWorkerRegister";
import "./globals.css";

const tabs = [
  { href: "/doctrine-library", label: "Doctrine Library" },
  { href: "/msc-toolkit", label: "MSC Toolkit" },
  { href: "/ask-super-friend", label: "Ask Super Friend" },
];

export const metadata: Metadata = {
  title: {
    default: "MSC Super Friend",
    template: "%s | MSC Super Friend",
  },
  description: "Next.js frontend for MSC Super Friend",
  themeColor: "#0b3c5d",
  manifest: "/manifest.webmanifest",
  icons: {
    icon: [
      { url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [{ url: "/icons/icon-192.png" }],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-msc-bg text-slate-900">
        <ServiceWorkerRegister />
        <div className="mx-auto min-h-screen max-w-5xl px-4 py-4 pb-24 sm:px-6 sm:pb-6">
          <header className="mb-4 rounded-xl border border-slate-200 bg-msc-card p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <h1 className="text-xl font-semibold text-msc-navy sm:text-2xl">MSC Super Friend</h1>
              <Link
                href="/settings"
                className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-msc-slate hover:text-msc-burgundy"
                aria-label="Settings"
              >
                <GearIcon className="h-5 w-5" />
              </Link>
            </div>
            <nav className="mt-4 overflow-x-auto">
              <ul className="flex min-w-max gap-2">
                {tabs.map((tab) => (
                  <li key={tab.href}>
                    <Link
                      href={tab.href}
                      className="inline-flex rounded-full border border-slate-300 bg-slate-100 px-4 py-2 text-sm font-medium text-msc-slate hover:border-msc-navy hover:text-msc-navy"
                    >
                      {tab.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          </header>
          <main>{children}</main>
        </div>
        <BottomNav />
      </body>
    </html>
  );
}
