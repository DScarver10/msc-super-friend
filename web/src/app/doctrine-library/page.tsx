import { ResourceLibrary } from "@/components/ResourceLibrary";
import { getDoctrineItems } from "@/lib/data";

export default function DoctrineLibraryPage() {
  const items = getDoctrineItems();

  return (
    <ResourceLibrary
      title="Doctrine Library"
      description="Quickly access authoritative DHA and DAF publications for policy-aligned decision support."
      searchPlaceholder="Search by publication number, title, functional area, or file name"
      items={items}
      emptyMessage="No doctrine items match your search."
    />
  );
}
