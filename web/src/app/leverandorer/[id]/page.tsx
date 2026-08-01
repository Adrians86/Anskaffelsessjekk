import Link from "next/link";
import { fetchApi } from "@/lib/api";
import type { SupplierDetail } from "@/lib/api";
import { VerdictPill } from "@/components/VerdictPill";
import { money, dato } from "@/lib/format";

export default async function SupplierDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let supplier: SupplierDetail | null = null;
  try {
    supplier = await fetchApi<SupplierDetail>(`/api/suppliers/${id}`);
  } catch {
    // not found or API down
  }

  if (!supplier) {
    return (
      <div className="text-center py-16 text-muted">
        <p className="font-medium">Leverandør ikke funnet</p>
        <Link href="/leverandorer" className="text-copper text-sm mt-2 inline-block">← Tilbake til listen</Link>
      </div>
    );
  }

  return (
    <div>
      <Link href="/leverandorer" className="text-xs text-copper hover:text-copper-light">← Leverandører</Link>

      <div className="mt-4 mb-6">
        <h1 className="font-serif text-2xl font-bold text-ink">{supplier.name}</h1>
        <p className="text-sm text-muted mt-1">Org.nr: {supplier.org_number}</p>
      </div>

      {/* Firm info */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {supplier.address && (
          <div className="border border-hairline rounded-lg p-3">
            <div className="text-xs text-muted font-medium">Adresse</div>
            <div className="text-sm mt-0.5">{supplier.address}, {supplier.postal_code} {supplier.city}</div>
          </div>
        )}
        {supplier.email && (
          <div className="border border-hairline rounded-lg p-3">
            <div className="text-xs text-muted font-medium">E-post</div>
            <div className="text-sm mt-0.5">{supplier.email}</div>
          </div>
        )}
        {supplier.phone && (
          <div className="border border-hairline rounded-lg p-3">
            <div className="text-xs text-muted font-medium">Telefon</div>
            <div className="text-sm mt-0.5">{supplier.phone}</div>
          </div>
        )}
      </div>

      {/* Contracts */}
      {supplier.contracts.length > 0 && (
        <div className="mb-8">
          <h2 className="font-semibold text-ink mb-3">Avtaler ({supplier.contracts.length})</h2>
          <div className="border border-hairline rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-paper-dark border-b border-hairline text-left">
                  <th className="px-4 py-2 font-medium text-muted">Referanse</th>
                  <th className="px-4 py-2 font-medium text-muted">Tittel</th>
                  <th className="px-4 py-2 font-medium text-muted">Gyldig fra</th>
                </tr>
              </thead>
              <tbody>
                {supplier.contracts.map((c) => (
                  <tr key={c.id} className="border-b border-hairline last:border-b-0">
                    <td className="px-4 py-2 font-semibold">{c.reference}</td>
                    <td className="px-4 py-2">{c.title}</td>
                    <td className="px-4 py-2 tabular-nums">{dato(c.valid_from)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Invoices */}
      {supplier.invoices.length > 0 && (
        <div>
          <h2 className="font-semibold text-ink mb-3">Fakturaer ({supplier.invoices.length})</h2>
          <div className="border border-hairline rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-paper-dark border-b border-hairline text-left">
                  <th className="px-4 py-2 font-medium text-muted">Fakturanr</th>
                  <th className="px-4 py-2 font-medium text-muted">Beløp</th>
                  <th className="px-4 py-2 font-medium text-muted">Verdikt</th>
                  <th className="px-4 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {supplier.invoices.map((inv) => (
                  <tr key={inv.id} className="border-b border-hairline last:border-b-0 hover:bg-paper-dark/50">
                    <td className="px-4 py-2 font-semibold">{inv.invoice_number}</td>
                    <td className="px-4 py-2 tabular-nums">{money(inv.amount, inv.currency)}</td>
                    <td className="px-4 py-2"><VerdictPill verdict={inv.verdict} /></td>
                    <td className="px-4 py-2">
                      <Link href={`/faktura/${inv.id}`} className="text-copper text-xs font-semibold">
                        Åpne →
                      </Link>
                    </td>
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
