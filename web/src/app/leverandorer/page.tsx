import Link from "next/link";
import { fetchApi } from "@/lib/api";
import type { SupplierRow } from "@/lib/api";

export default async function LeverandorerPage() {
  let suppliers: SupplierRow[] = [];
  try {
    suppliers = await fetchApi<SupplierRow[]>("/api/suppliers");
  } catch {
    // API unavailable
  }

  return (
    <div>
      <div className="mb-6">
        <div className="text-xs uppercase tracking-wide text-muted font-medium">Kartotek</div>
        <h1 className="font-serif text-3xl font-bold text-ink mt-1">Leverandører</h1>
        <p className="text-sm text-muted mt-1">
          Alle registrerte leverandører med avtaler og fakturaoversikt.
        </p>
      </div>

      {suppliers.length === 0 ? (
        <div className="border border-hairline rounded-lg p-6 text-center text-muted">
          <p className="font-medium">Ingen leverandører tilgjengelig</p>
          <p className="text-xs mt-1">Start API-serveren for å se data.</p>
        </div>
      ) : (
        <div className="border border-hairline rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-paper-dark border-b border-hairline text-left">
                <th className="px-4 py-2.5 font-medium text-muted">Navn</th>
                <th className="px-4 py-2.5 font-medium text-muted">Org.nr</th>
                <th className="px-4 py-2.5 font-medium text-muted">By</th>
                <th className="px-4 py-2.5 font-medium text-muted">Avtaler</th>
                <th className="px-4 py-2.5 font-medium text-muted">Fakturaer</th>
                <th className="px-4 py-2.5"></th>
              </tr>
            </thead>
            <tbody>
              {suppliers.map((sup) => (
                <tr key={sup.id} className="border-b border-hairline last:border-b-0 hover:bg-paper-dark/50">
                  <td className="px-4 py-2.5 font-semibold">{sup.name}</td>
                  <td className="px-4 py-2.5 tabular-nums">{sup.org_number}</td>
                  <td className="px-4 py-2.5 text-muted">{sup.city || "—"}</td>
                  <td className="px-4 py-2.5 tabular-nums">{sup.n_contracts}</td>
                  <td className="px-4 py-2.5 tabular-nums">{sup.n_invoices}</td>
                  <td className="px-4 py-2.5">
                    <Link
                      href={`/leverandorer/${sup.id}`}
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
