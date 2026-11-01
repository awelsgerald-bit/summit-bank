// Shown for a moment while a page's code downloads. The menu and header stay in place around it.
export default function PageLoader() {
  return (
    <div className="max-w-lg mx-auto space-y-4 py-4" role="status" aria-label="Loading">
      <div className="h-6 w-40 rounded-lg bg-[var(--glass-border)] animate-pulse" />
      <div className="h-40 rounded-3xl bg-[var(--glass-border)] animate-pulse" />
      <div className="h-16 rounded-2xl bg-[var(--glass-border)] animate-pulse" />
      <div className="h-16 rounded-2xl bg-[var(--glass-border)] animate-pulse" />
    </div>
  );
}
