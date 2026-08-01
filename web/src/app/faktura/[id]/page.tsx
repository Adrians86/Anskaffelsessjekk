import Link from "next/link";
import { fetchApi } from "@/lib/api";
import type { InvoiceDetail } from "@/lib/api";
import { VerdictPill } from "@/components/VerdictPill";
import { money, dato } from "@/lib/format";

export default async function InvoiceDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let invoice: InvoiceDetail | null = null;
  try {
    invoice = await fetchApi<InvoiceDetail>(`/api/invoices/${id}`);
  } catch {
    // not found or API down
  }

  if (!invoice) {
    return (
      <div className="text-center py-16 text-muted">
        <p className="font-medium">Faktura ikke funnet</p>
        <Link href="/faktura" className="text-copper text-sm mt-2 inline-block">← Tilbake til listen</Link>
      </div>
    );
  }

  return (
    <div>
      <Link href="/faktura" className="text-xs text-copper hover:text-copper-light">← Fakturaer</Link>

      <div className="mt-4 mb-6">
        <h1 className="font-serif text-2xl font-bold text-ink">{invoice.invoice_number}</h1>
        <p className="text-sm text-muted mt-1">
          <Link href={`/leverandorer/${invoice.supplier_id}`} className="text-copper hover:text-copper-light">
            {invoice.supplier_name}
          </Link>
          {" · "}{money(invoice.amount, invoice.currency)}{" · "}{dato(invoice.date)}
        </p>
      </div>

      {/* Verdict + status */}
      <div className="flex items-center gap-4 mb-6">
        <div>
          <div className="text-xs text-muted font-medium mb-1">Verdikt</div>
          <VerdictPill verdict={invoice.verdict} />
        </div>
        <div>
          <div className="text-xs text-muted font-medium mb-1">Status</div>
          <span className="text-sm font-medium capitalize">{invoice.status.replace("_", " ")}</span>
        </div>
      </div>

      {/* Findings with WHY */}
      {invoice.findings.length > 0 && (
        <div className="mb-8">
          <h2 className="font-semibold text-ink mb-3">Funn ({invoice.findings.length})</h2>
          <div className="space-y-3">
            {invoice.findings.map((f, i) => (
              <div key={i} className="border border-hairline rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <SeverityDot severity={f.severity} />
                    <span className="font-medium text-sm">{f.code}</span>
                  </div>
                </div>
                <p className="text-sm mt-2 text-ink">{f.message}</p>
                {f.citation && (
                  <p className="text-xs text-muted mt-2 italic">Hjemmel: {f.citation}</p>
                )}
                {(f.expected || f.actual) && (
                  <div className="mt-2 flex gap-4 text-xs">
                    {f.expected && (
                      <span className="text-muted">Forventet: <span className="font-semibold text-ink">{f.expected}</span></span>
                    )}
                    {f.actual && (
                      <span className="text-muted">Faktisk: <span className="font-semibold text-ink">{f.actual}</span></span>
                    )}
                  </div>
                )}
                {f.deviation_amount != null && f.deviation_amount !== 0 && (
                  <div className="mt-2 text-xs text-avvik font-semibold">
                    Avvik: {money(f.deviation_amount, "NOK")}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Invoice lines */}
      {invoice.lines.length > 0 && (
        <div>
          <h2 className="font-semibold text-ink mb-3">Fakturalinjer ({invoice.lines.length})</h2>
          <div className="border border-hairline rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-paper-dark border-b border-hairline text-left">
                  <th className="px-4 py-2 font-medium text-muted">Ref</th>
                  <th className="px-4 py-2 font-medium text-muted">Beskrivelse</th>
                  <th className="px-4 py-2 font-medium text-muted text-right">Antall</th>
                  <th className="px-4 py-2 font-medium text-muted text-right">Enhetspris</th>
                  <th className="px-4 py-2 font-medium text-muted text-right">Sum</th>
                </tr>
              </thead>
              <tbody>
                {invoice.lines.map((line, i) => (
                  <tr key={i} className="border-b border-hairline last:border-b-0">
                    <td className="px-4 py-2 font-semibold">{line.item_ref}</td>
                    <td className="px-4 py-2">{line.description}</td>
                    <td className="px-4 py-2 tabular-nums text-right">{line.quantity}</td>
                    <td className="px-4 py-2 tabular-nums text-right">{money(line.unit_price, "NOK")}</td>
                    <td className="px-4 py-2 tabular-nums text-right">{money(line.line_total, "NOK")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function SeverityDot({ severity }: { severity: string }) {
  const color = severity === "ERROR" ? "bg-avvik" : severity === "WARN" ? "bg-vurdering" : "bg-samsvar";
  return <span className={`inline-block w-2 h-2 rounded-full ${color}`} />;
}
