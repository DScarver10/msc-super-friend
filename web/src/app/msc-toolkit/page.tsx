import { ResourceLibrary } from "@/components/ResourceLibrary";
import { getToolkitItems } from "@/lib/data";

export default function MscToolkitPage() {
  const items = getToolkitItems();

  return (
    <ResourceLibrary
      title="MSC Toolkit"
      description="Find operational references, job aids, and quick links curated to support day-to-day mission execution."
      searchPlaceholder="Search toolkit resources by title, summary, tag, or file name"
      items={items}
      emptyMessage="No toolkit items match your search."
    />
  );
}
