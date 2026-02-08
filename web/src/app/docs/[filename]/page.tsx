type DocsPageProps = {
  params: {
    filename: string;
  };
};

export default function DocsPlaceholderPage({ params }: DocsPageProps) {
  const filename = decodeURIComponent(params.filename);

  return (
    <section className="space-y-3 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Document Placeholder</h2>
      <p className="text-sm text-slate-600">
        This route will eventually render a document viewer for <span className="font-medium">{filename}</span>.
      </p>
    </section>
  );
}
