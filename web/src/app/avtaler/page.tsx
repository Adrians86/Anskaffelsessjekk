import Link from "next/link";
import { fetchApi } from "@/lib/api";
import type { ContractOut } from "@/lib/api";
import { money, dato } from "@/lib/format";

const STATUS_LABELS: Record<string, string> = {
  aktiv: "Aktiv",
  utlopt: "Utløpt",
  avsluttet: "Avsluttet",
  under_forhandling: "Under forhandling",
};

export default async function AvtalerPage() {
  let contracts: ContractOut[] = [];
  try {
    contracts = await fetchApi<ContractOut[]>("/api/contracts");
  } catch {
    // API unavailable
  }

  return (
    <div>
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="text-xs uppercase tracking-widest text-muted font-semibold">Kontrakter</div>
          <h1 className="font-serif text-3xl font-bold text-ink mt-1">Avtaler</h1>
          <p className="text-sm text-muted mt-1">
            Alle kontrakter med prislister — grunnlaget for fakturakontroll.
          </p>
        </div>
        <Link
          href="/avtaler/ny"
          className="bg-navy text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-navy-light transition-colors whitespace-nowrap"
        >
          + Ny avtale
        </Link>
      </div>

      {contracts.length === 0 ? (
        <div className="border border-line rounded-xl p-12 text-center text-muted bg-card">
          <p className="font-medium text-ink">Ingen avtaler registrert</p>
          <p className="text-xs mt-1">Legg til din første kontrakt for å starte kontrollen.</p>
          <Link
            href="/avtaler/ny"
            className="inline-block mt-4 bg-navy text-white text-sm font-semibold px-4 py-2 rounded-lg"
          >
            Ny avtale
          </Link>
        </div>
      ) : (
        <div className="border border-line rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-paper-dark border-b border-line text-left">
                  <th className="px-4 py-2.5 font-medium text-muted">Referanse</th>
                  <th className="px-4 py-2.5 font-medium text-muted">Tittel</th>
                  <th className="px-4 py-2.5 font-medium text-muted">Leverandør</th>
                  <th className="px-4 py-2.5 font-medium text-muted">Type</th>
                  <th className="px-4 py-2.5 font-medium text-muted">Gyldig fra</th>
                  <th className="px-4 py-2.5 font-medium text-muted">Gyldig til</th>
                  <th className="px-4 py-2.5 font-medium text-muted text-right">Ramme</th>
                  <th className="px-4 py-2.5 font-medium text-muted">Status</th>
                  <th className="px-4 py-2.5 font-medium text-muted text-center">Linjer</th>
                  <th className="px-4 py-2.5"></th>
                </tr>
              </thead>
              <tbody>
                {contracts.map((c) => (
                  <tr key={c.id} className="border-b border-line last:border-b-0 hover:bg-paper-dark/50">
                    <td className="px-4 py-2.5 font-semibold text-xs">{c.reference}</td>
                    <td className="px-4 py-2.5 font-medium">{c.title}</td>
                    <td className="px-4 py-2.5">
                      <Link href={`/leverandorer/${c.supplier_id}`} className="text-copper hover:text-copper-light text-xs">
                        {c.supplier_name}
                      </Link>
                    </td>
                    <td className="px-4 py-2.5 text-xs text-muted">{c.contract_type}</td>
                    <td className="px-4 py-2.5 tabular-nums text-xs text-muted">{dato(c.valid_from)}</td>
                    <td className="px-4 py-2.5 tabular-nums text-xs text-muted">{c.valid_to ? dato(c.valid_to) : "—"}</td>
                    <td className="px-4 py-2.5 tabular-nums text-right text-xs">
                      {c.total_value ? money(c.total_value, "NOK") : "—"}
                    </td>
                    <td className="px-4 py-2.5">
                      <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded-full border ${
                        c.status === "aktiv"
                          ? "bg-samsvar-bg text-samsvar border-samsvar/30"
                          : "bg-paper-dark text-muted border-line"
                      }`}>
                        {STATUS_LABELS[c.status] ?? c.status}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-center text-xs text-muted">{c.lines.length}</td>
                    <td className="px-4 py-2.5">
                      <Link href={`/avtaler/${c.id}`} className="text-copper hover:text-copper-light text-xs font-semibold whitespace-nowrap">
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
