"use client";

import { TouchEvent, useEffect, useMemo, useRef, useState } from "react";

import { CardList, type CardListItem } from "@/components/CardList";

type ResourceLibraryProps = {
  title: string;
  description: string;
  searchPlaceholder: string;
  items: CardListItem[];
  emptyMessage?: string;
};

export function ResourceLibrary({
  title,
  description,
  searchPlaceholder,
  items,
  emptyMessage = "No items found.",
}: ResourceLibraryProps) {
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const [feedback, setFeedback] = useState<"next" | "prev" | null>(null);
  const inputId = `resource-search-${title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
  const inputRef = useRef<HTMLInputElement | null>(null);
  const swipeStartX = useRef<number | null>(null);
  const feedbackTimer = useRef<number | null>(null);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) {
      return items;
    }
    return items.filter((item) => {
      const haystack = [item.title, item.description, item.tag, item.filename || "", item.type].join(" ").toLowerCase();
      return haystack.includes(needle);
    });
  }, [items, query]);

  useEffect(() => {
    setActiveIndex(filtered.length > 0 ? 0 : -1);
  }, [query, filtered.length]);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      const key = event.key.toLowerCase();
      if ((event.ctrlKey || event.metaKey) && key === "f") {
        event.preventDefault();
        inputRef.current?.focus();
        inputRef.current?.select();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  useEffect(
    () => () => {
      if (feedbackTimer.current) {
        window.clearTimeout(feedbackTimer.current);
      }
    },
    [],
  );

  function pulse(kind: "next" | "prev") {
    setFeedback(kind);
    if (feedbackTimer.current) {
      window.clearTimeout(feedbackTimer.current);
    }
    feedbackTimer.current = window.setTimeout(() => setFeedback(null), 180);
  }

  function goNext() {
    if (filtered.length === 0) {
      return;
    }
    pulse("next");
    setActiveIndex((prev) => (prev + 1) % filtered.length);
  }

  function goPrev() {
    if (filtered.length === 0) {
      return;
    }
    pulse("prev");
    setActiveIndex((prev) => (prev - 1 + filtered.length) % filtered.length);
  }

  const showNavigator = query.trim().length > 0 && filtered.length > 0;

  function onTouchStart(event: TouchEvent<HTMLDivElement>) {
    swipeStartX.current = event.changedTouches[0]?.clientX ?? null;
  }

  function onTouchEnd(event: TouchEvent<HTMLDivElement>) {
    if (!showNavigator || swipeStartX.current === null) {
      return;
    }
    const endX = event.changedTouches[0]?.clientX ?? swipeStartX.current;
    const delta = endX - swipeStartX.current;
    swipeStartX.current = null;
    if (Math.abs(delta) < 30) {
      return;
    }
    if (delta < 0) {
      goNext();
    } else {
      goPrev();
    }
  }

  return (
    <section className="space-y-4">
      <div className="space-y-2">
        <h2 className="text-lg font-semibold sm:text-xl">{title}</h2>
        <p className="text-sm text-slate-600">{description}</p>
      </div>

      <div className="sticky top-2 z-10 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
        <label htmlFor={inputId} className="sr-only">
          Search resources
        </label>
        <div className="flex items-center gap-2">
          <input
            id={inputId}
            ref={inputRef}
            type="text"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={searchPlaceholder}
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-500 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-200"
          />
          {query ? (
            <button
              type="button"
              onClick={() => setQuery("")}
              className="min-h-10 rounded-lg border border-slate-300 bg-white px-3 text-sm font-semibold text-slate-700 hover:bg-slate-100"
            >
              Clear
            </button>
          ) : null}
        </div>
        <div className="mt-2 flex items-center justify-between gap-2">
          <p className="text-xs text-slate-500">
            Showing {filtered.length} of {items.length}
          </p>
          {showNavigator ? (
            <div
              className={`flex items-center gap-2 rounded-md px-1 py-0.5 transition-colors duration-200 ${
                feedback ? "bg-amber-50" : ""
              }`}
              onTouchStart={onTouchStart}
              onTouchEnd={onTouchEnd}
            >
              <span className="text-xs text-slate-500">
                Match {activeIndex + 1} of {filtered.length}
              </span>
              <button
                type="button"
                onClick={goPrev}
                className={`min-h-10 rounded border border-slate-300 bg-white px-3 py-1 text-sm font-semibold text-slate-700 transition duration-150 hover:bg-slate-100 active:scale-[0.98] ${
                  feedback === "prev" ? "scale-[0.98] bg-amber-100" : ""
                }`}
              >
                Prev
              </button>
              <button
                type="button"
                onClick={goNext}
                className={`min-h-10 rounded border border-slate-300 bg-white px-3 py-1 text-sm font-semibold text-slate-700 transition duration-150 hover:bg-slate-100 active:scale-[0.98] ${
                  feedback === "next" ? "scale-[0.98] bg-amber-100" : ""
                }`}
              >
                Next
              </button>
            </div>
          ) : null}
        </div>
        {showNavigator ? (
          <p className="mt-1 text-xs text-slate-500 sm:hidden">Tip: swipe left/right on the match controls to navigate.</p>
        ) : null}
      </div>

      <CardList
        items={filtered}
        emptyMessage={emptyMessage}
        highlightTerm={query}
        activeIndex={showNavigator ? activeIndex : -1}
      />
    </section>
  );
}
