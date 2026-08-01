import Link from "next/link";
import { VerdictPill } from "./VerdictPill";
import { money } from "@/lib/format";
import type { InvoiceRow } from "@/lib/api";

export function UrgentList({ invoices }: { invoices: InvoiceRow[] }) {
  if (invoices.length === 0) {
    return (
      <div className="text-center py-10 text-muted">
        <div className="text-4xl mb-2">🎯</div>
        <div className="font-semibold">Alt er kontrollert</div>
        <div className="text-sm mt-1">Ingen fakturaer krever handling akkurat nå.</div>
      </div>
    );
  }

  return (
    <div className="border border-hairline rounded-lg overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-paper-dark border-b border-hairline text-left">
            <th className="px-4 py-2 font-medium text-muted">Faktura</th>
            <th className="px-4 py-2 font-medium text-muted">Leverandør</th>
            <th className="px-4 py-2 font-medium text-muted">Beløp</th>
            <th className="px-4 py-2 font-medium text-muted">Verdikt</th>
            <th className="px-4 py-2 font-medium text-muted">Funn</th>
            <th className="px-4 py-2"></th>
          </tr>
        </thead>
        <tbody>
          {invoices.map((inv) => (
            <tr key={inv.id} className="border-b border-hairline last:border-b-0 hover:bg-paper-dark/50">
              <td className="px-4 py-2.5 font-semibold">{inv.invoice_number}</td>
              <td className="px-4 py-2.5">{inv.supplier_name}</td>
              <td className="px-4 py-2.5 tabular-nums whitespace-nowrap">{money(inv.amount, inv.currency)}</td>
              <td className="px-4 py-2.5"><VerdictPill verdict={inv.verdict} /></td>
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
  );
}
