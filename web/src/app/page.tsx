import Link from "next/link";
import { fetchApi } from "@/lib/api";
import type { StatsResponse, InvoiceRow } from "@/lib/api";
import { KpiStrip } from "@/components/KpiStrip";
import { HealthBar } from "@/components/HealthBar";
import { UrgentList } from "@/components/UrgentList";

export default async function HomePage() {
  let stats: StatsResponse | null = null;
  let urgent: InvoiceRow[] = [];

  try {
    stats = await fetchApi<StatsResponse>("/api/stats");
    const all = await fetchApi<InvoiceRow[]>("/api/invoices?sort=avvik_first&limit=5");
    urgent = all.filter((inv) => inv.verdict !== "SAMSVAR" && inv.status !== "godkjent" && inv.status !== "avvist");
  } catch {
    // API not reachable — render static shell
  }

  return (
    <div>
      {/* Page header */}
      <div className="mb-6">
        <div className="text-xs uppercase tracking-wide text-muted font-medium">Kontrolloversikt</div>
        <h1 className="font-serif text-3xl font-bold text-ink mt-1">Arbeidsflate</h1>
        <p className="text-sm text-muted mt-1">
          Full oversikt over kontrollstatus — hva som krever deg, og hva som er i orden.
        </p>
        <span className="inline-block mt-2 text-xs border border-hairline text-muted px-2 py-0.5 rounded-full">
          Syntetiske data · regelverk per 01.07.2026
        </span>
      </div>

      {/* KPIs */}
      {stats ? (
        <>
          <KpiStrip kpi={stats.kpi} />
          <HealthBar health={stats.health} />
        </>
      ) : (
        <div className="border border-hairline rounded-lg p-6 text-center text-muted">
          <p className="font-medium">API ikke tilgjengelig</p>
          <p className="text-xs mt-1">Start API-serveren: <code className="bg-paper-dark px-1 rounded">uvicorn api.main:app --reload</code></p>
        </div>
      )}

      {/* Urgent + worklist link */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-ink">Krever handling</h2>
          <Link
            href="/faktura"
            className="bg-navy text-white text-sm font-semibold px-4 py-1.5 rounded-md hover:bg-navy-light transition-colors"
          >
            → Åpne arbeidsliste
          </Link>
        </div>
        <UrgentList invoices={urgent.slice(0, 5)} />
      </div>

      {/* Synthetic data notice */}
      <div className="mt-8 text-xs text-muted">
        <strong>SYNTETISKE DATA</strong> — alle leverandører, avtaler og fakturaer er generert. Ingen reelle data inngår.
      </div>
    </div>
  );
}
