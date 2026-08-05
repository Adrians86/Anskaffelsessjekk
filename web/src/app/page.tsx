"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import type { StatsResponse, InvoiceRow } from "@/lib/api";
import { KpiStrip } from "@/components/KpiStrip";
import { HealthBar } from "@/components/HealthBar";
import { UrgentList } from "@/components/UrgentList";
import { PeriodSelector } from "@/components/PeriodSelector";
import { ActionTiles } from "@/components/ActionTiles";
import { dato } from "@/lib/format";
import { SleepBanner } from "@/components/SleepBanner";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function KpiSkeleton() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="h-20 rounded-xl bg-paper-dark animate-pulse" />
      ))}
    </div>
  );
}

function HomeContent() {
  const searchParams = useSearchParams();
  const periode = searchParams.get("periode") || "kvartal";

  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [urgent, setUrgent] = useState<InvoiceRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const [statsRes, invRes] = await Promise.all([
        fetch(`${API_BASE}/api/stats?periode=${periode}`),
        fetch(`${API_BASE}/api/invoices?sort=avvik_first&limit=5`),
      ]);
      if (!statsRes.ok || !invRes.ok) throw new Error("API error");
      const statsData: StatsResponse = await statsRes.json();
      const allInv: InvoiceRow[] = await invRes.json();
      setStats(statsData);
      setUrgent(
        allInv.filter(
          (inv) => inv.verdict !== "SAMSVAR" && inv.status !== "godkjent" && inv.status !== "avvist"
        )
      );
    } catch {
      setError("sleep");
    } finally {
      setLoading(false);
    }
  }, [periode]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="space-y-8">
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

      <div>
        <div className="text-xs uppercase tracking-widest text-muted font-semibold mb-3">
          Handlinger
        </div>
        <ActionTiles />
      </div>

      {error ? (
        <SleepBanner onRetry={load} />
      ) : (
        <>
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-xs uppercase tracking-widest text-muted font-semibold">
                  Nøkkeltall
                </div>
                {stats && (
                  <div className="text-xs text-muted mt-0.5">
                    {dato(stats.periode_fra)} – {dato(stats.periode_til)}
                  </div>
                )}
              </div>
              <PeriodSelector active={periode} />
            </div>
            {loading ? (
              <KpiSkeleton />
            ) : stats ? (
              <>
                <KpiStrip kpi={stats.kpi} />
                <HealthBar health={stats.health} />
              </>
            ) : null}
          </div>

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
            {loading ? (
              <div className="space-y-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="h-14 rounded-lg bg-paper-dark animate-pulse" />
                ))}
              </div>
            ) : (
              <UrgentList invoices={urgent.slice(0, 5)} />
            )}
          </div>
        </>
      )}

      <div className="text-xs text-muted border-t border-line pt-4">
        <strong>SYNTETISKE DATA</strong> — alle leverandører, avtaler og fakturaer er generert.
        Ingen reelle data inngår.
      </div>
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={
      <div className="space-y-8">
        <div>
          <div className="text-xs uppercase tracking-widest text-copper font-semibold">Kontrolloversikt</div>
          <h1 className="font-serif text-3xl font-bold text-ink mt-1">Arbeidsflate</h1>
        </div>
        <div>
          <div className="text-xs uppercase tracking-widest text-muted font-semibold mb-3">Handlinger</div>
          <ActionTiles />
        </div>
        <div>
          <div className="text-xs uppercase tracking-widest text-muted font-semibold mb-3">Nøkkeltall</div>
          <KpiSkeleton />
        </div>
      </div>
    }>
      <HomeContent />
    </Suspense>
  );
}
