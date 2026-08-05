import Link from "next/link";
import { Suspense } from "react";
import { fetchApi } from "@/lib/api";
import type { InvoiceRow } from "@/lib/api";
import { VerdictPill } from "@/components/VerdictPill";
import { money, dato } from "@/lib/format";
import { FakturaFilterBar } from "@/components/FakturaFilterBar";

const PAGE_SIZE = 25;

export default async function FakturaPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const sp = await searchParams;
  const verdikt = typeof sp.verdikt === "string" ? sp.verdikt : "";
  const status = typeof sp.status === "string" ? sp.status : "";
  const soek = typeof sp.soek === "string" ? sp.soek : "";
  const side = typeof sp.side === "string" ? parseInt(sp.side, 10) : 1;

  let invoices: InvoiceRow[] = [];
  let total = 0;
  try {
    const params = new URLSearchParams({ sort: "avvik_first", limit: "200" });
    if (verdikt) params.set("verdict", verdikt);
    if (status) params.set("status", status);
    if (soek) params.set("search", soek);
    const all = await fetchApi<InvoiceRow[]>(`/api/invoices?${params}`);
    total = all.length;
    const offset = (side - 1) * PAGE_SIZE;
    invoices = all.slice(offset, offset + PAGE_SIZE);
  } catch {
    // API unavailable
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  function buildPageUrl(p: number) {
    const params = new URLSearchParams();
    if (verdikt) params.set("verdikt", verdikt);
    if (status) params.set("status", status);
    if (soek) params.set("soek", soek);
    if (p > 1) params.set("side", String(p));
    const q = params.toString();
    return `/faktura${q ? `?${q}` : ""}`;
  }

  return (
    <div>
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="text-xs uppercase tracking-widest text-muted font-semibold">Kontroll</div>
          <h1 className="font-serif text-3xl font-bold text-ink mt-1">Fakturaer</h1>
          <p className="text-sm text-muted mt-1">
            {total > 0 ? `${total} faktura${total === 1 ? "" : "er"} · avvik sortert øverst` : "Avvik sortert øverst."}
          </p>
        </div>
        <Link
          href="/faktura/ny"
          className="bg-copper text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-copper-light transition-colors whitespace-nowrap"
        >
          + Kontroller faktura
        </Link>
      </div>

      <Suspense>
        <FakturaFilterBar
          currentVerdikt={verdikt}
          currentStatus={status}
          currentSearch={soek}
        />
      </Suspense>

      {invoices.length === 0 ? (
        <div className="border border-line rounded-xl p-12 text-center text-muted bg-card">
          <p className="font-medium text-ink">Ingen fakturaer funnet</p>
          <p className="text-xs mt-1">
            {verdikt || status || soek
              ? "Prøv å justere filtrene."
              : "Last opp en faktura for å starte."}
          </p>
          {!verdikt && !status && !soek && (
            <Link
              href="/faktura/ny"
              className="inline-block mt-4 bg-navy text-white text-sm font-semibold px-4 py-2 rounded-lg"
            >
              Last opp faktura
            </Link>
          )}
        </div>
      ) : (
        <>
          <div className="border border-line rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-paper-dark border-b border-line text-left">
                    <th className="px-4 py-2.5 font-medium text-muted">Fakturanr</th>
                    <th className="px-4 py-2.5 font-medium text-muted">Leverandør</th>
                    <th className="px-4 py-2.5 font-medium text-muted text-right">Beløp</th>
                    <th className="px-4 py-2.5 font-medium text-muted">Dato</th>
                    <th className="px-4 py-2.5 font-medium text-muted">Verdikt</th>
                    <th className="px-4 py-2.5 font-medium text-muted">Status</th>
                    <th className="px-4 py-2.5 font-medium text-muted max-w-48">Funn</th>
                    <th className="px-4 py-2.5"></th>
                  </tr>
                </thead>
                <tbody>
                  {invoices.map((inv) => (
                    <tr key={inv.id} className="border-b border-line last:border-b-0 hover:bg-paper-dark/50">
                      <td className="px-4 py-2.5 font-semibold text-xs">{inv.invoice_number}</td>
                      <td className="px-4 py-2.5">
                        <Link href={`/leverandorer/${inv.supplier_id}`} className="text-copper hover:text-copper-light">
                          {inv.supplier_name}
                        </Link>
                      </td>
                      <td className="px-4 py-2.5 tabular-nums text-right whitespace-nowrap">{money(inv.amount, inv.currency)}</td>
                      <td className="px-4 py-2.5 tabular-nums whitespace-nowrap text-muted text-xs">{dato(inv.date)}</td>
                      <td className="px-4 py-2.5"><VerdictPill verdict={inv.verdict} /></td>
                      <td className="px-4 py-2.5"><StatusChip status={inv.status} /></td>
                      <td className="px-4 py-2.5 text-xs text-muted max-w-48 truncate">{inv.finding}</td>
                      <td className="px-4 py-2.5">
                        <Link href={`/faktura/${inv.id}`} className="text-copper hover:text-copper-light text-xs font-semibold whitespace-nowrap">
                          Åpne →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4 text-xs text-muted">
              <span>Side {side} av {totalPages} · {total} fakturaer</span>
              <div className="flex gap-1">
                {side > 1 && (
                  <Link href={buildPageUrl(side - 1)} className="px-3 py-1.5 border border-line rounded-lg hover:border-navy">
                    ← Forrige
                  </Link>
                )}
                {side < totalPages && (
                  <Link href={buildPageUrl(side + 1)} className="px-3 py-1.5 border border-line rounded-lg hover:border-navy">
                    Neste →
                  </Link>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function StatusChip({ status }: { status: string }) {
  const styles: Record<string, string> = {
    ny: "bg-blue-50 text-blue-700 border-blue-200",
    under_kontroll: "bg-amber-50 text-amber-700 border-amber-200",
    godkjent: "bg-samsvar-bg text-samsvar border-samsvar/30",
    avvist: "bg-avvik-bg text-avvik border-avvik/30",
  };
  const labels: Record<string, string> = {
    ny: "Ny",
    under_kontroll: "Under kontroll",
    godkjent: "Godkjent",
    avvist: "Avvist",
  };
  const cls = styles[status] || "bg-paper-dark text-muted border-line";
  return (
    <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded-full border ${cls}`}>
      {labels[status] ?? status}
    </span>
  );
}
