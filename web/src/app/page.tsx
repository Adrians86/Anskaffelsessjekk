import Link from "next/link";
import { Suspense } from "react";
import { fetchApi } from "@/lib/api";
import type { StatsResponse, InvoiceRow } from "@/lib/api";
import { KpiStrip } from "@/components/KpiStrip";
import { HealthBar } from "@/components/HealthBar";
import { UrgentList } from "@/components/UrgentList";
import { PeriodSelector } from "@/components/PeriodSelector";
import { ActionTiles } from "@/components/ActionTiles";
import { dato } from "@/lib/format";

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const sp = await searchParams;
  const periode = typeof sp.periode === "string" ? sp.periode : "kvartal";

  let stats: StatsResponse | null = null;
  let urgent: InvoiceRow[] = [];

  try {
    stats = await fetchApi<StatsResponse>(`/api/stats?periode=${periode}`);
    const all = await fetchApi<InvoiceRow[]>("/api/invoices?sort=avvik_first&limit=5");
    urgent = all.filter(
      (inv) => inv.verdict !== "SAMSVAR" && inv.status !== "godkjent" && inv.status !== "avvist"
    );
  } catch {
    // API not reachable
  }

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div>
        <div className="text-xs uppercase tracking-widest text-copper font-semibold">
          Kontrolloversikt
        </div>
        <h1 className="font-serif text-3xl font-bold text-ink mt-1">Arbeidsflate</h1>
        <p className="text-sm text-muted mt-1">
          Full oversikt over kontrollstatus — hva som krever deg, og hva som er i orden.
        </p>
        <span className="inline-block mt-2 text-xs border border-line text-muted px-2 py-0.5 rounded-full">
          Syntetiske data · regelverk per 01.07.2026
        </span>
      </div>

      {/* Handlinger */}
      <div>
        <div className="text-xs uppercase tracking-widest text-muted font-semibold mb-3">
          Handlinger
        </div>
        <ActionTiles />
      </div>

      {/* Nøkkeltall */}
      {stats ? (
        <div>
          <div className="flex items-center justify-between mb-3">
            <div>
              <div className="text-xs uppercase tracking-widest text-muted font-semibold">
                Nøkkeltall
              </div>
              <div className="text-xs text-muted mt-0.5">
                {dato(stats.periode_fra)} – {dato(stats.periode_til)}
              </div>
            </div>
            <Suspense>
              <PeriodSelector active={periode} />
            </Suspense>
          </div>
          <KpiStrip kpi={stats.kpi} />
          <HealthBar health={stats.health} />
        </div>
      ) : (
        <div className="border border-line rounded-lg p-6 text-center text-muted bg-card">
          <p className="font-medium">API ikke tilgjengelig</p>
          <p className="text-xs mt-1">
            Start API-serveren:{" "}
            <code className="bg-paper-dark px-1 rounded">uvicorn api.main:app --reload</code>
          </p>
        </div>
      )}

      {/* Krever handling */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="text-xs uppercase tracking-widest text-muted font-semibold">
            Krever handling
          </div>
          <Link
            href="/faktura"
            className="bg-navy text-white text-sm font-semibold px-4 py-1.5 rounded-md hover:bg-navy-light transition-colors"
          >
            Se alle →
          </Link>
        </div>
        <UrgentList invoices={urgent.slice(0, 5)} />
      </div>

      {/* Synthetic data notice */}
      <div className="text-xs text-muted border-t border-line pt-4">
        <strong>SYNTETISKE DATA</strong> — alle leverandører, avtaler og fakturaer er generert.
        Ingen reelle data inngår.
      </div>
    </div>
  );
}
