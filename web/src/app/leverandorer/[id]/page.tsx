import Link from "next/link";
import { Suspense } from "react";
import { fetchApi } from "@/lib/api";
import type { SupplierDetail, ContractOut, CommitmentOut } from "@/lib/api";
import { VerdictPill } from "@/components/VerdictPill";
import { money, dato } from "@/lib/format";
import { SupplierTabBar } from "@/components/SupplierTabBar";
import { SupplierEditForm } from "@/components/SupplierEditForm";

const TABS = [
  { id: "oversikt", label: "Oversikt" },
  { id: "firmadata", label: "Firmadata" },
  { id: "tjenester", label: "Kat. og tjenester" },
  { id: "kvalifikasjoner", label: "Kvalifikasjoner" },
  { id: "personer", label: "Personer" },
  { id: "avtaler", label: "Avtaler / Forp." },
  { id: "vurdering", label: "Vurdering" },
];

export default async function SupplierDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const [{ id }, sp] = await Promise.all([params, searchParams]);
  const tab = typeof sp.tab === "string" ? sp.tab : "oversikt";

  let supplier: SupplierDetail | null = null;
  let contracts: ContractOut[] = [];
  let commitments: CommitmentOut[] = [];

  try {
    supplier = await fetchApi<SupplierDetail>(`/api/suppliers/${id}`);
    contracts = await fetchApi<ContractOut[]>(`/api/contracts?supplier_id=${id}`);
    commitments = await fetchApi<CommitmentOut[]>(`/api/forpliktelser?leverandor_id=${id}`);
  } catch {
    // API down or not found
  }

  if (!supplier) {
    return (
      <div className="text-center py-16 text-muted">
        <p className="font-medium text-ink">Leverandør ikke funnet</p>
        <Link href="/leverandorer" className="text-copper text-sm mt-2 inline-block">← Tilbake til listen</Link>
      </div>
    );
  }

  const avvikCount = supplier.invoices.filter((i) => i.verdict === "AVVIK").length;
  const totalInvoiced = supplier.invoices
    .filter((i) => i.currency === "NOK")
    .reduce((sum, i) => sum + i.amount, 0);

  return (
    <div>
      <Link href="/leverandorer" className="text-xs text-copper hover:text-copper-light">← Leverandører</Link>

      <div className="mt-4 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="font-serif text-2xl font-bold text-ink">{supplier.name}</h1>
            <p className="text-sm text-muted mt-1">
              Org.nr: {supplier.org_number}
              {supplier.status && <span className="ml-2 text-xs border border-line px-2 py-0.5 rounded-full">{supplier.status}</span>}
            </p>
          </div>
          <div className="flex gap-2">
            <Link
              href={`/avtaler/ny?leverandor_id=${id}`}
              className="border border-line text-sm px-3 py-1.5 rounded-lg hover:border-navy transition-colors text-muted"
            >
              + Avtale
            </Link>
            <Link
              href="/faktura/ny"
              className="bg-copper text-white text-sm font-semibold px-3 py-1.5 rounded-lg hover:bg-copper-light transition-colors"
            >
              + Faktura
            </Link>
          </div>
        </div>
      </div>

      {/* Tab bar */}
      <Suspense>
        <SupplierTabBar supplierId={id} tabs={TABS} activeTab={tab} />
      </Suspense>

      <div className="mt-6">
        {tab === "oversikt" && (
          <TabOversikt supplier={supplier} avvikCount={avvikCount} totalInvoiced={totalInvoiced} contracts={contracts} />
        )}
        {tab === "firmadata" && (
          <TabFirmadata supplier={supplier} />
        )}
        {tab === "tjenester" && (
          <TabTjenester supplier={supplier} />
        )}
        {tab === "kvalifikasjoner" && (
          <TabKvalifikasjoner supplier={supplier} />
        )}
        {tab === "personer" && (
          <TabPersoner supplier={supplier} />
        )}
        {tab === "avtaler" && (
          <TabAvtaler contracts={contracts} commitments={commitments} supplierId={id} />
        )}
        {tab === "vurdering" && (
          <TabVurdering supplier={supplier} avvikCount={avvikCount} />
        )}
      </div>
    </div>
  );
}

function TabOversikt({
  supplier,
  avvikCount,
  totalInvoiced,
  contracts,
}: {
  supplier: SupplierDetail;
  avvikCount: number;
  totalInvoiced: number;
  contracts: ContractOut[];
}) {
  return (
    <div className="space-y-6">
      {/* KPI strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiBox label="Fakturaer" value={String(supplier.invoices.length)} />
        <KpiBox label="Avtaler" value={String(contracts.length)} />
        <KpiBox label="Avvik" value={String(avvikCount)} highlight={avvikCount > 0} />
        <KpiBox label="Fakturert (NOK)" value={money(totalInvoiced, "NOK")} />
      </div>

      {/* Firm info */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {supplier.address && (
          <div className="border border-line rounded-lg p-3 bg-card">
            <div className="text-xs text-muted font-medium">Adresse</div>
            <div className="text-sm mt-0.5">{supplier.address}{supplier.postal_code || supplier.city ? `, ${supplier.postal_code ?? ""} ${supplier.city ?? ""}`.trim() : ""}</div>
          </div>
        )}
        {supplier.email && (
          <div className="border border-line rounded-lg p-3 bg-card">
            <div className="text-xs text-muted font-medium">E-post</div>
            <div className="text-sm mt-0.5">{supplier.email}</div>
          </div>
        )}
        {supplier.phone && (
          <div className="border border-line rounded-lg p-3 bg-card">
            <div className="text-xs text-muted font-medium">Telefon</div>
            <div className="text-sm mt-0.5">{supplier.phone}</div>
          </div>
        )}
        {supplier.categories && (
          <div className="border border-line rounded-lg p-3 bg-card">
            <div className="text-xs text-muted font-medium">Kategorier</div>
            <div className="text-sm mt-0.5">{supplier.categories}</div>
          </div>
        )}
      </div>

      {/* Recent invoices */}
      {supplier.invoices.length > 0 && (
        <div>
          <h2 className="font-semibold text-ink mb-3">Siste fakturaer</h2>
          <div className="border border-line rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-paper-dark border-b border-line text-left">
                  <th className="px-4 py-2 font-medium text-muted">Fakturanr</th>
                  <th className="px-4 py-2 font-medium text-muted text-right">Beløp</th>
                  <th className="px-4 py-2 font-medium text-muted">Verdikt</th>
                  <th className="px-4 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {supplier.invoices.slice(0, 5).map((inv) => (
                  <tr key={inv.id} className="border-b border-line last:border-b-0 hover:bg-paper-dark/50">
                    <td className="px-4 py-2 font-semibold text-xs">{inv.invoice_number}</td>
                    <td className="px-4 py-2 tabular-nums text-right">{money(inv.amount, inv.currency)}</td>
                    <td className="px-4 py-2"><VerdictPill verdict={inv.verdict} /></td>
                    <td className="px-4 py-2">
                      <Link href={`/faktura/${inv.id}`} className="text-copper text-xs font-semibold">Åpne →</Link>
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

function TabFirmadata({ supplier }: { supplier: SupplierDetail }) {
  return <SupplierEditForm supplier={supplier} />;
}

function TabTjenester({ supplier }: { supplier: SupplierDetail }) {
  return (
    <div className="space-y-6">
      {supplier.categories && (
        <div>
          <h2 className="font-semibold text-ink mb-2">Kategorier</h2>
          <div className="flex flex-wrap gap-2">
            {supplier.categories.split(",").map((cat) => cat.trim()).filter(Boolean).map((cat, i) => (
              <span key={i} className="inline-block bg-paper-dark border border-line text-xs px-3 py-1 rounded-full text-ink">
                {cat}
              </span>
            ))}
          </div>
        </div>
      )}

      <div>
        <h2 className="font-semibold text-ink mb-2">Tjenester og produkter ({supplier.services.length})</h2>
        {supplier.services.length === 0 ? (
          <p className="text-sm text-muted">Ingen tjenester registrert.</p>
        ) : (
          <div className="border border-line rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-paper-dark border-b border-line text-left">
                  <th className="px-4 py-2 font-medium text-muted">Navn</th>
                  <th className="px-4 py-2 font-medium text-muted">Beskrivelse</th>
                  <th className="px-4 py-2 font-medium text-muted">Enhet</th>
                  <th className="px-4 py-2 font-medium text-muted text-right">Enhetspris</th>
                </tr>
              </thead>
              <tbody>
                {supplier.services.map((s) => (
                  <tr key={s.id} className="border-b border-line last:border-b-0">
                    <td className="px-4 py-2 font-medium">{s.name}</td>
                    <td className="px-4 py-2 text-muted text-xs">{s.description ?? "—"}</td>
                    <td className="px-4 py-2 text-muted text-xs">{s.unit ?? "—"}</td>
                    <td className="px-4 py-2 tabular-nums text-right">
                      {s.unit_price != null ? money(s.unit_price, "NOK") : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function TabKvalifikasjoner({ supplier }: { supplier: SupplierDetail }) {
  const today = new Date().toISOString().slice(0, 10);
  return (
    <div>
      <h2 className="font-semibold text-ink mb-3">Kvalifikasjoner ({supplier.qualifications.length})</h2>
      {supplier.qualifications.length === 0 ? (
        <p className="text-sm text-muted">Ingen kvalifikasjoner registrert.</p>
      ) : (
        <div className="space-y-2">
          {supplier.qualifications.map((q) => {
            const expired = q.valid_to != null && q.valid_to < today;
            return (
              <div key={q.id} className={`border rounded-lg p-3 flex items-center justify-between ${expired ? "border-avvik/40 bg-avvik-bg/30" : "border-line bg-card"}`}>
                <span className={`text-sm font-medium ${expired ? "text-avvik" : "text-ink"}`}>{q.name}</span>
                <span className={`text-xs ${expired ? "text-avvik font-semibold" : "text-muted"}`}>
                  {q.valid_to ? (expired ? `UTLØPT ${dato(q.valid_to)}` : `Gyldig til ${dato(q.valid_to)}`) : "Ingen utløpsdato"}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function TabPersoner({ supplier }: { supplier: SupplierDetail }) {
  const leverandorSide = supplier.contacts.filter((c) => c.side === "SUPPLIER");
  const internSide = supplier.contacts.filter((c) => c.side === "INTERNAL");
  return (
    <div className="space-y-6">
      <PersonGroup title="Kontakt hos leverandøren" contacts={leverandorSide} />
      <PersonGroup title="Ansvarlig hos oss" contacts={internSide} />
    </div>
  );
}

function PersonGroup({ title, contacts }: { title: string; contacts: SupplierDetail["contacts"] }) {
  return (
    <div>
      <h2 className="font-semibold text-ink mb-2">{title} ({contacts.length})</h2>
      {contacts.length === 0 ? (
        <p className="text-sm text-muted">Ingen registrert.</p>
      ) : (
        <div className="space-y-2">
          {contacts.map((c) => (
            <div key={c.id} className="border border-line rounded-lg p-3 bg-card">
              <div className="font-medium text-sm">{c.name}</div>
              {c.role && <div className="text-xs text-muted">{c.role}</div>}
              <div className="flex gap-4 mt-1 text-xs text-muted">
                {c.email && <span>{c.email}</span>}
                {c.phone && <span>{c.phone}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function TabAvtaler({ contracts, commitments, supplierId }: { contracts: ContractOut[]; commitments: CommitmentOut[]; supplierId: string }) {
  const FORM_LABELS: Record<string, string> = {
    CONFIRMED_ANNEX: "Formalisert (aneks)",
    PENDING_ANNEX: "Avventer formalisering",
    EMAIL_ONLY: "E-post",
    MEETING_MINUTES: "Møtereferat",
  };
  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-ink">Avtaler ({contracts.length})</h2>
          <Link
            href={`/avtaler`}
            className="text-xs text-copper hover:text-copper-light"
          >
            Se alle →
          </Link>
        </div>
        {contracts.length === 0 ? (
          <p className="text-sm text-muted">Ingen avtaler registrert for denne leverandøren.</p>
        ) : (
          <div className="space-y-2">
            {contracts.map((c) => (
              <div key={c.id} className="border border-line rounded-lg p-3 bg-card flex items-center justify-between">
                <div>
                  <div className="font-medium text-sm">{c.title}</div>
                  <div className="text-xs text-muted">{c.reference} · {dato(c.valid_from)}{c.valid_to ? ` → ${dato(c.valid_to)}` : ""}</div>
                </div>
                <Link href={`/avtaler/${c.id}`} className="text-copper text-xs font-semibold ml-4">Åpne →</Link>
              </div>
            ))}
          </div>
        )}
      </div>

      <div>
        <h2 className="font-semibold text-ink mb-3">Forpliktelser ({commitments.length})</h2>
        {commitments.length === 0 ? (
          <p className="text-sm text-muted">Ingen forpliktelser registrert.</p>
        ) : (
          <div className="space-y-2">
            {commitments.map((f) => (
              <div key={f.id} className="border border-line rounded-lg p-3 bg-card">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-medium text-sm">{f.condition_type}</div>
                    <div className="text-xs text-muted mt-0.5">{f.source_ref}</div>
                  </div>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${
                    f.confirmed_by_user
                      ? "bg-samsvar-bg text-samsvar border-samsvar/30"
                      : "bg-vurdering-bg text-vurdering border-vurdering/30"
                  }`}>
                    {f.confirmed_by_user ? "Bekreftet" : "Ubekreftet"}
                  </span>
                </div>
                {f.value != null && (
                  <div className="text-xs text-muted mt-1">
                    Verdi: {f.value.toLocaleString("nb-NO")} {f.unit ?? "NOK"}
                  </div>
                )}
                <div className="text-xs text-muted mt-0.5">{FORM_LABELS[f.formalization] ?? f.formalization}</div>
                {f.gyldighet && (
                  <div className="text-xs mt-1 text-muted italic">{f.gyldighet}</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function TabVurdering({ supplier, avvikCount }: { supplier: SupplierDetail; avvikCount: number }) {
  const total = supplier.invoices.length;
  const avvikPct = total > 0 ? Math.round((avvikCount / total) * 100) : 0;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <KpiBox label="Andel med avvik" value={`${avvikPct} %`} highlight={avvikPct > 20} />
        <KpiBox label="Fakturaer totalt" value={String(total)} />
        <KpiBox label="Avvik" value={String(avvikCount)} highlight={avvikCount > 0} />
      </div>

      {supplier.notes && (
        <div className="border border-line rounded-xl p-4 bg-card">
          <div className="text-xs font-semibold text-muted uppercase tracking-wide mb-2">Notater</div>
          <p className="text-sm text-ink whitespace-pre-wrap">{supplier.notes}</p>
        </div>
      )}

      <div className="border border-line rounded-xl p-4 bg-card">
        <div className="text-xs font-semibold text-muted uppercase tracking-wide mb-2">Merk</div>
        <p className="text-xs text-muted">
          Vurderingen er en intern kontrollindikasjon — ikke en kvalifikasjonsrangering etter FOA §16.
          Brukes ikke til eksklusjon av leverandøren.
        </p>
      </div>
    </div>
  );
}

function KpiBox({ label, value, highlight = false }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className={`border rounded-lg p-3 ${highlight ? "border-avvik/40 bg-avvik-bg/30" : "border-line bg-card"}`}>
      <div className="text-xs text-muted font-medium">{label}</div>
      <div className={`text-xl font-bold mt-0.5 tabular-nums ${highlight ? "text-avvik" : "text-ink"}`}>{value}</div>
    </div>
  );
}
