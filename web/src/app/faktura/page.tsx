import Link from "next/link";
import { fetchApi } from "@/lib/api";
import type { InvoiceRow } from "@/lib/api";
import { VerdictPill } from "@/components/VerdictPill";
import { money, dato } from "@/lib/format";

export default async function FakturaPage() {
  let invoices: InvoiceRow[] = [];
  try {
    invoices = await fetchApi<InvoiceRow[]>("/api/invoices?sort=avvik_first&limit=200");
  } catch {
    // API unavailable
  }

  return (
    <div>
      <div className="mb-6">
        <div className="text-xs uppercase tracking-wide text-muted font-medium">Kontroll</div>
        <h1 className="font-serif text-3xl font-bold text-ink mt-1">Fakturaer</h1>
        <p className="text-sm text-muted mt-1">
          Alle fakturaer med verdikt og status — avvik sortert øverst.
        </p>
      </div>

      {invoices.length === 0 ? (
        <div className="border border-hairline rounded-lg p-6 text-center text-muted">
          <p className="font-medium">Ingen fakturaer tilgjengelig</p>
          <p className="text-xs mt-1">Start API-serveren for å se data.</p>
        </div>
      ) : (
        <div className="border border-hairline rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-paper-dark border-b border-hairline text-left">
                <th className="px-4 py-2.5 font-medium text-muted">Fakturanr</th>
                <th className="px-4 py-2.5 font-medium text-muted">Leverandør</th>
                <th className="px-4 py-2.5 font-medium text-muted">Beløp</th>
                <th className="px-4 py-2.5 font-medium text-muted">Dato</th>
                <th className="px-4 py-2.5 font-medium text-muted">Verdikt</th>
                <th className="px-4 py-2.5 font-medium text-muted">Status</th>
                <th className="px-4 py-2.5 font-medium text-muted">Funn</th>
                <th className="px-4 py-2.5"></th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr key={inv.id} className="border-b border-hairline last:border-b-0 hover:bg-paper-dark/50">
                  <td className="px-4 py-2.5 font-semibold">{inv.invoice_number}</td>
                  <td className="px-4 py-2.5">
                    <Link href={`/leverandorer/${inv.supplier_id}`} className="text-copper hover:text-copper-light">
                      {inv.supplier_name}
                    </Link>
                  </td>
                  <td className="px-4 py-2.5 tabular-nums whitespace-nowrap">{money(inv.amount, inv.currency)}</td>
                  <td className="px-4 py-2.5 tabular-nums">{dato(inv.date)}</td>
                  <td className="px-4 py-2.5"><VerdictPill verdict={inv.verdict} /></td>
                  <td className="px-4 py-2.5">
                    <StatusChip status={inv.status} />
                  </td>
                  <td className="px-4 py-2.5 text-xs text-muted max-w-48 truncate">{inv.finding}</td>
                  <td className="px-4 py-2.5">
                    <Link
                      href={`/faktura/${inv.id}`}
                      className="text-copper hover:text-copper-light text-xs font-semibold"
                    >
                      Åpne →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function StatusChip({ status }: { status: string }) {
  const styles: Record<string, string> = {
    ny: "bg-blue-50 text-blue-700 border-blue-200",
    under_kontroll: "bg-amber-50 text-amber-700 border-amber-200",
    godkjent: "bg-green-50 text-green-700 border-green-200",
    avvist: "bg-red-50 text-red-700 border-red-200",
  };
  const labels: Record<string, string> = {
    ny: "Ny",
    under_kontroll: "Under kontroll",
    godkjent: "Godkjent",
    avvist: "Avvist",
  };
  const cls = styles[status] || "bg-gray-50 text-gray-600 border-gray-200";
  const label = labels[status] || status;
  return (
    <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded-full border ${cls}`}>
      {label}
    </span>
  );
}
