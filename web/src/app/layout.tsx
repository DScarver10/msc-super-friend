import type { Metadata } from "next";
import Link from "next/link";
import Image from "next/image";
import { BottomNav } from "@/components/BottomNav";
import { GearIcon } from "@/components/icons";
import { ServiceWorkerRegister } from "@/components/ServiceWorkerRegister";
import "./globals.css";

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
              <Image
                src="/msc.png"
                alt="MSC Super Friend"
                width={640}
                height={140}
                priority
                className="h-auto w-full max-w-[340px] rounded-md sm:max-w-[420px]"
              />
              <Link
                href="/settings"
                className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-msc-slate hover:text-msc-burgundy"
                aria-label="Settings"
              >
                <GearIcon className="h-5 w-5" />
              </Link>
            </div>
          </header>
          <main>{children}</main>
          <footer className="mt-8 border-t border-slate-300 pt-4 pb-2 text-center text-xs text-slate-500">
            Built for MSCs | Version 1.0
          </footer>
        </div>
        <BottomNav />
      </body>
    </html>
  );
}
