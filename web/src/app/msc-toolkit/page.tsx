import { CardList } from "@/components/CardList";
import { getToolkitItems } from "@/lib/data";

export default function MscToolkitPage() {
  const items = getToolkitItems();

  return (
    <section className="space-y-4">
      <h2 className="text-lg font-semibold sm:text-xl">MSC Toolkit</h2>
      <p className="text-sm text-slate-600">Helpful resources, right when you need them.</p>
      <CardList items={items} />
    </section>
  );
}
