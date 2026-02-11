import type { Metadata, Viewport } from "next";
import Image from "next/image";
import Link from "next/link";
import { BottomNav } from "@/components/BottomNav";
import { ServiceWorkerRegister } from "@/components/ServiceWorkerRegister";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "MSC Super Companion",
    template: "%s | MSC Super Companion",
  },
  description: "Next.js frontend for MSC Super Companion",
  manifest: "/manifest.webmanifest",
  icons: {
    icon: [
      { url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [{ url: "/icons/icon-192.png" }],
  },
};

export const viewport: Viewport = {
  themeColor: "#0b3c5d",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const appVersion = (process.env.NEXT_PUBLIC_APP_VERSION || "").trim() || "1.0.0";

  return (
    <html lang="en">
      <body className="bg-msc-bg text-slate-900">
        <ServiceWorkerRegister />
        <div className="mx-auto min-h-screen max-w-5xl px-4 py-4 pb-24 sm:px-6 sm:pb-6">
          <header className="mb-4 rounded-xl border border-slate-200 bg-[linear-gradient(135deg,_#ffffff,_#f8fafc)] px-3 py-1.5 shadow-sm">
            <div className="flex items-center justify-center">
              <Link
                href="/"
                aria-label="Go to homepage"
                className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 rounded-md"
              >
                <Image
                  src="/msc.png"
                  alt="MSC Super Companion"
                  width={640}
                  height={140}
                  priority
                  className="h-56 w-full max-w-[1400px] rounded-md object-contain sm:h-64 sm:max-w-[1640px]"
                />
              </Link>
            </div>
          </header>
          <main>{children}</main>
          <footer className="mt-8 border-t border-slate-300 pt-4 pb-2 text-center text-xs text-slate-500">
            MSC Super Companion | Version {appVersion}
          </footer>
        </div>
        <BottomNav />
      </body>
    </html>
  );
}
