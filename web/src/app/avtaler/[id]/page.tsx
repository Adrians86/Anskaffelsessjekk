import Link from "next/link";
import { fetchApi } from "@/lib/api";
import type { ContractOut } from "@/lib/api";
import { money, dato } from "@/lib/format";

export default async function AvtaleDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let contract: ContractOut | null = null;
  try {
    contract = await fetchApi<ContractOut>(`/api/contracts/${id}`);
  } catch {
    // not found or API down
  }

  if (!contract) {
    return (
      <div className="text-center py-16 text-muted">
        <p className="font-medium text-ink">Avtale ikke funnet</p>
        <Link href="/avtaler" className="text-copper text-sm mt-2 inline-block">← Tilbake til avtaler</Link>
      </div>
    );
  }

  const CLAUSE_LABELS: Record<string, string> = {
    ingen: "Ingen endringsklausul",
    kun_skriftlig_tillegg: "Kun skriftlig tillegg",
    prisjustering_kpi: "Prisjustering (KPI)",
    mengdejustering: "Mengdejustering",
    opsjon: "Opsjon",
    full_fleksibilitet: "Full fleksibilitet",
  };

  return (
    <div>
      <Link href="/avtaler" className="text-xs text-copper hover:text-copper-light">← Avtaler</Link>

      <div className="mt-4 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="font-serif text-2xl font-bold text-ink">{contract.title}</h1>
            <p className="text-sm text-muted mt-1">
              {contract.reference}
              {" · "}
              <Link href={`/leverandorer/${contract.supplier_id}`} className="text-copper hover:text-copper-light">
                {contract.supplier_name}
              </Link>
            </p>
          </div>
          <span className={`inline-block text-xs font-semibold px-2 py-1 rounded-full border mt-1 ${
            contract.status === "aktiv"
              ? "bg-samsvar-bg text-samsvar border-samsvar/30"
              : "bg-paper-dark text-muted border-line"
          }`}>
            {contract.status ?? "—"}
          </span>
        </div>
      </div>

      {/* Details grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 mb-8">
        <InfoBox label="Type" value={contract.contract_type} />
        <InfoBox label="Regime" value={contract.regime} />
        <InfoBox label="Gyldig fra" value={dato(contract.valid_from)} />
        <InfoBox label="Gyldig til" value={contract.valid_to ? dato(contract.valid_to) : "Ingen sluttdato"} />
        {contract.total_value != null && (
          <InfoBox label="Rammeverdi" value={money(contract.total_value, "NOK")} />
        )}
        <InfoBox label="Endringsklausul" value={CLAUSE_LABELS[contract.change_clause] ?? contract.change_clause} />
      </div>

      {/* Price lines */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-ink">Prisliste ({contract.lines.length} linjer)</h2>
        </div>

        {contract.lines.length === 0 ? (
          <div className="border border-line rounded-xl p-8 text-center text-muted bg-card">
            <p className="font-medium text-ink">Ingen prislinjer registrert</p>
            <p className="text-xs mt-1">Prislisten er grunnlaget for fakturakontroll.</p>
          </div>
        ) : (
          <div className="border border-line rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-paper-dark border-b border-line text-left">
                    <th className="px-4 py-2.5 font-medium text-muted">Artikkelnr</th>
                    <th className="px-4 py-2.5 font-medium text-muted">Beskrivelse</th>
                    <th className="px-4 py-2.5 font-medium text-muted text-right">Enhetspris</th>
                    <th className="px-4 py-2.5 font-medium text-muted">Enhet</th>
                    <th className="px-4 py-2.5 font-medium text-muted text-right">Maks mengde</th>
                    <th className="px-4 py-2.5 font-medium text-muted">Valuta</th>
                  </tr>
                </thead>
                <tbody>
                  {contract.lines.map((line) => (
                    <tr key={line.id} className="border-b border-line last:border-b-0">
                      <td className="px-4 py-2.5 font-semibold text-xs">{line.item_ref}</td>
                      <td className="px-4 py-2.5">{line.description ?? "—"}</td>
                      <td className="px-4 py-2.5 tabular-nums text-right">{money(line.unit_price, line.currency ?? "NOK")}</td>
                      <td className="px-4 py-2.5 text-muted text-xs">{line.unit ?? "—"}</td>
                      <td className="px-4 py-2.5 tabular-nums text-right text-muted text-xs">
                        {line.max_quantity != null ? line.max_quantity.toLocaleString("nb-NO") : "—"}
                      </td>
                      <td className="px-4 py-2.5 text-muted text-xs">{line.currency ?? "NOK"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function InfoBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line rounded-lg p-3 bg-card">
      <div className="text-xs text-muted font-medium">{label}</div>
      <div className="text-sm font-medium mt-0.5">{value}</div>
    </div>
  );
}
