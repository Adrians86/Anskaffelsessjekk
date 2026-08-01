import type { HealthBar as HealthBarData } from "@/lib/api";

export function HealthBar({ health }: { health: HealthBarData }) {
  return (
    <div className="mt-6">
      <div className="text-sm font-semibold text-ink mb-2">Porteføljehelse</div>
      <div className="flex h-3 rounded-full overflow-hidden">
        <div className="bg-avvik" style={{ width: `${health.pct_avvik}%` }} />
        <div className="bg-vurdering" style={{ width: `${health.pct_til_vurdering}%` }} />
        <div className="bg-samsvar" style={{ width: `${health.pct_samsvar}%` }} />
      </div>
      <div className="text-xs text-muted mt-1">
        ● {Math.round(health.pct_avvik)}% avvik · {Math.round(health.pct_til_vurdering)}% til vurdering · {Math.round(health.pct_samsvar)}% samsvar
      </div>
    </div>
  );
}
