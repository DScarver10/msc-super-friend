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
            const bgClass = index % 2 === 0 ? "bg-slate-100" : "bg-[#f8eef1]";
            const cardClass = `block w-full rounded-lg border border-slate-200 p-4 shadow-sm transition hover:bg-slate-50 active:scale-[0.998] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-1 ${bgClass}`;
            const content = (
              <div className="flex items-start gap-3">
                <span className="mt-0.5 inline-flex rounded-full bg-slate-200 px-2.5 py-1 text-xs font-medium text-slate-700">
                  {item.tag}
                </span>
                <div className="min-w-0">
                  <p className="text-sm font-bold text-slate-900 sm:text-base">{item.title}</p>
                  <p className="mt-1 text-xs text-slate-600 sm:text-sm">{item.description}</p>
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
                  <a href={item.href} download={item.filename || true} className={cardClass}>
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
