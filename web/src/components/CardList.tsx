"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";

export type CardListItem = {
  id: string;
  title: string;
  description: string;
  tag: string;
  type: "external" | "local";
  href: string;
  filename?: string;
};

type CardListProps = {
  items: CardListItem[];
  emptyMessage?: string;
  highlightTerm?: string;
  activeIndex?: number;
};

function HighlightedText({ text, term }: { text: string; term: string }) {
  if (!term.trim()) {
    return <>{text}</>;
  }
  const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const re = new RegExp(`(${escaped})`, "ig");
  const parts = text.split(re);
  return (
    <>
      {parts.map((part, i) =>
        part.toLowerCase() === term.toLowerCase() ? (
          <mark key={`${part}-${i}`} className="rounded bg-amber-200 px-0.5 text-black">
            {part}
          </mark>
        ) : (
          <span key={`${part}-${i}`}>{part}</span>
        ),
      )}
    </>
  );
}

export function CardList({ items, emptyMessage = "No items yet.", highlightTerm = "", activeIndex = -1 }: CardListProps) {
  const refs = useRef<Array<HTMLLIElement | null>>([]);

  useEffect(() => {
    if (activeIndex < 0 || activeIndex >= items.length) {
      return;
    }
    const target = refs.current[activeIndex];
    if (!target) {
      return;
    }
    target.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [activeIndex, items.length]);

  return (
    <section className="space-y-3">
      {items.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-300 bg-white p-4 text-sm text-slate-500">
          {emptyMessage}
        </div>
      ) : (
        <ul className="space-y-2">
          {items.map((item, index) => {
            const isBurgundy = index % 2 === 1;
            const isActive = index === activeIndex;
            const bgClass = isBurgundy ? "bg-[#5a0013]" : "bg-slate-100";
            const textClass = isBurgundy ? "text-white" : "text-slate-900";
            const descClass = isBurgundy ? "text-slate-200" : "text-slate-600";
            const pillClass = isBurgundy ? "bg-white/15 text-white" : "bg-slate-200 text-slate-700";
            const activeClass = isActive ? "ring-2 ring-amber-400 ring-offset-2" : "";
            const cardClass = `block w-full rounded-lg border border-slate-200 p-4 shadow-sm transition hover:opacity-95 active:scale-[0.998] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 focus-visible:ring-offset-1 ${bgClass} ${textClass} ${activeClass}`;
            const content = (
              <div className="flex items-start gap-3">
                <span className={`mt-0.5 inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${pillClass}`}>
                  <HighlightedText text={item.tag} term={highlightTerm} />
                </span>
                <div className="min-w-0">
                  <p className="text-sm font-bold sm:text-base">
                    <HighlightedText text={item.title} term={highlightTerm} />
                  </p>
                  {item.description ? (
                    <p className={`mt-1 text-xs sm:text-sm ${descClass}`}>
                      <HighlightedText text={item.description} term={highlightTerm} />
                    </p>
                  ) : null}
                  <p className={`mt-2 text-[11px] font-semibold uppercase tracking-wide ${descClass}`}>
                    {item.type === "external" ? "Open external source" : "Open in-app viewer"}
                  </p>
                </div>
              </div>
            );

            return (
              <li
                key={item.id}
                ref={(el) => {
                  refs.current[index] = el;
                }}
              >
                {item.type === "external" ? (
                  <a href={item.href} target="_blank" rel="noopener noreferrer" className={cardClass}>
                    {content}
                  </a>
                ) : (
                  <Link href={item.href} className={cardClass}>
                    {content}
                  </Link>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
