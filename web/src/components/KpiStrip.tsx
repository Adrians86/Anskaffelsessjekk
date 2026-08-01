import { nok } from "@/lib/format";
import type { KpiStats } from "@/lib/api";

export function KpiStrip({ kpi }: { kpi: KpiStats }) {
  const cells = [
    { label: "Kontrollert", value: String(kpi.total_invoices), accent: "border-t-navy" },
    { label: "Avvik", value: String(kpi.avvik), accent: "border-t-avvik" },
    { label: "Til vurdering", value: String(kpi.til_vurdering), accent: "border-t-vurdering" },
    { label: "Samsvar", value: String(kpi.samsvar), accent: "border-t-samsvar" },
    { label: "Verdi funnet", value: nok(kpi.verdi_funnet), accent: "border-t-copper" },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-5 border border-hairline rounded-lg overflow-hidden">
      {cells.map((cell) => (
        <div key={cell.label} className={`border-t-4 ${cell.accent} p-4 border-r border-hairline last:border-r-0`}>
          <div className="text-xs text-muted font-medium uppercase tracking-wide">{cell.label}</div>
          <div className="font-serif text-2xl font-bold mt-1 text-ink tabular-nums">{cell.value}</div>
        </div>
      ))}
    </div>
  );
}
