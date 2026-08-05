export function SleepBanner({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="border border-vurdering/30 bg-vurdering-bg rounded-xl p-8 text-center">
      <div className="text-3xl mb-3">⏳</div>
      <p className="font-semibold text-ink">Tjenesten starter opp</p>
      <p className="text-sm text-muted mt-1">Prøv igjen om 30 sekunder.</p>
      <button
        onClick={onRetry}
        className="mt-4 text-sm border border-vurdering/40 text-vurdering px-5 py-2 rounded-lg hover:bg-vurdering/10 transition-colors"
      >
        Prøv igjen
      </button>
    </div>
  );
}
