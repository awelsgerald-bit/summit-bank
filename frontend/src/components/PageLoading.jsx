// Shown for a moment while a page's code arrives. Quiet on purpose: no layout jump, no spinner storm.
export default function PageLoading() {
  return (
    <div className="min-h-[40vh] flex items-center justify-center" role="status" aria-live="polite">
      <span className="w-6 h-6 rounded-full border-2 border-[var(--text-3)] border-t-transparent animate-spin" />
      <span className="sr-only">Loading</span>
    </div>
  );
}
