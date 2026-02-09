import { CardList } from "@/components/CardList";
import { getDoctrineItems } from "@/lib/data";

export default function DoctrineLibraryPage() {
  const items = getDoctrineItems();

  return (
    <section className="space-y-4">
      <h2 className="text-lg font-semibold sm:text-xl">Doctrine Library</h2>
      <p className="text-sm text-slate-600">Quick access to trusted DHA and DAF health services publications.</p>
      <CardList title="Doctrine Items" items={items} />
    </section>
  );
}
