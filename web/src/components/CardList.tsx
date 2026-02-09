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
  title: string;
  items: CardListItem[];
  emptyMessage?: string;
};

export function CardList({ title, items, emptyMessage = "No items yet." }: CardListProps) {
  return (
    <section className="space-y-3">
      <h3 className="text-base font-medium text-slate-800">{title}</h3>
      {items.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-300 bg-white p-4 text-sm text-slate-500">
          {emptyMessage}
        </div>
      ) : (
        <ul className="space-y-2">
          {items.map((item, index) => {
            const isBurgundy = index % 2 === 1;
            const bgClass = isBurgundy ? "bg-[#5a0013]" : "bg-slate-100";
            const textClass = isBurgundy ? "text-white" : "text-slate-900";
            const descClass = isBurgundy ? "text-slate-200" : "text-slate-600";
            const pillClass = isBurgundy ? "bg-white/15 text-white" : "bg-slate-200 text-slate-700";
            const cardClass = `block w-full rounded-lg border border-slate-200 p-4 shadow-sm transition hover:opacity-95 active:scale-[0.998] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-1 ${bgClass} ${textClass}`;
            const content = (
              <div className="flex items-start gap-3">
                <span className={`mt-0.5 inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${pillClass}`}>
                  {item.tag}
                </span>
                <div className="min-w-0">
                  <p className="text-sm font-bold sm:text-base">{item.title}</p>
                  <p className={`mt-1 text-xs sm:text-sm ${descClass}`}>{item.description}</p>
                </div>
              </div>
            );

            return (
              <li key={item.id}>
                {item.type === "external" ? (
                  <a href={item.href} target="_blank" rel="noopener noreferrer" className={cardClass}>
                    {content}
                  </a>
                ) : (
                  <a href={item.href} target="_blank" rel="noopener noreferrer" className={cardClass}>
                    {content}
                  </a>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
