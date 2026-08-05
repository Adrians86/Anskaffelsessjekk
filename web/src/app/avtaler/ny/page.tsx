"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Suspense } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function NyAvtaleForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preselectedSupplierId = searchParams.get("leverandor_id") ?? "";

  const [supplierId, setSupplierId] = useState(preselectedSupplierId);
  const [title, setTitle] = useState("");
  const [reference, setReference] = useState("");
  const [contractType, setContractType] = useState("RAMMEAVTALE");
  const [regime, setRegime] = useState("FOA");
  const [validFrom, setValidFrom] = useState("");
  const [validTo, setValidTo] = useState("");
  const [totalValue, setTotalValue] = useState("");
  const [changeClause, setChangeClause] = useState("kun_skriftlig_tillegg");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/contracts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          supplier_id: parseInt(supplierId),
          title,
          reference,
          contract_type: contractType,
          regime,
          valid_from: validFrom,
          valid_to: validTo || null,
          total_value: totalValue ? parseFloat(totalValue) : null,
          change_clause: changeClause,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `${res.status}`);
      }
      const contract = await res.json();
      router.push(`/avtaler/${contract.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Noe gikk galt");
      setLoading(false);
    }
  }

  return (
    <div className="max-w-lg">
      <div className="mb-6">
        <div className="text-xs uppercase tracking-widest text-muted font-semibold">
          <Link href="/avtaler" className="text-copper hover:text-copper-light">Avtaler</Link>
          {" / "}Ny
        </div>
        <h1 className="font-serif text-3xl font-bold text-ink mt-1">Ny avtale</h1>
      </div>

      <div className="bg-card border border-line rounded-xl p-6">
        {error && (
          <div className="bg-avvik-bg border border-avvik/30 text-avvik rounded-lg p-3 text-sm mb-4">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">
              Leverandør-ID <span className="text-avvik">*</span>
            </label>
            <input
              type="number"
              min="1"
              required
              value={supplierId}
              onChange={(e) => setSupplierId(e.target.value)}
              className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-copper"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">
                Tittel <span className="text-avvik">*</span>
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-copper"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">
                Referanse <span className="text-avvik">*</span>
              </label>
              <input
                type="text"
                required
                value={reference}
                onChange={(e) => setReference(e.target.value)}
                placeholder="RA-2026-001"
                className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-copper"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">Type</label>
              <select
                value={contractType}
                onChange={(e) => setContractType(e.target.value)}
                className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-copper bg-white"
              >
                <option value="RAMMEAVTALE">Rammeavtale</option>
                <option value="ENKELTKONTRAKT">Enkeltkontrakt</option>
                <option value="AVROP">Avrop</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">Regime</label>
              <select
                value={regime}
                onChange={(e) => setRegime(e.target.value)}
                className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-copper bg-white"
              >
                <option value="FOA">FOA</option>
                <option value="KOFA">KOFA</option>
                <option value="HOA">HOA</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">
                Gyldig fra <span className="text-avvik">*</span>
              </label>
              <input
                type="date"
                required
                value={validFrom}
                onChange={(e) => setValidFrom(e.target.value)}
                className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-copper"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">Gyldig til</label>
              <input
                type="date"
                value={validTo}
                onChange={(e) => setValidTo(e.target.value)}
                className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-copper"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">
                Rammeverdi (NOK)
              </label>
              <input
                type="number"
                min="0"
                step="1000"
                value={totalValue}
                onChange={(e) => setTotalValue(e.target.value)}
                className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-copper"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">Endringsklausul</label>
              <select
                value={changeClause}
                onChange={(e) => setChangeClause(e.target.value)}
                className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-copper bg-white"
              >
                <option value="ingen">Ingen</option>
                <option value="kun_skriftlig_tillegg">Kun skriftlig tillegg</option>
                <option value="prisjustering_kpi">Prisjustering (KPI)</option>
                <option value="mengdejustering">Mengdejustering</option>
                <option value="opsjon">Opsjon</option>
                <option value="full_fleksibilitet">Full fleksibilitet</option>
              </select>
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-navy text-white font-semibold py-2 px-4 rounded-lg hover:bg-navy-light transition-colors disabled:opacity-50"
            >
              {loading ? "Lagrer…" : "Lagre avtale"}
            </button>
            <Link
              href="/avtaler"
              className="px-4 py-2 border border-line rounded-lg text-sm text-muted hover:border-navy transition-colors"
            >
              Avbryt
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function NyAvtalePage() {
  return (
    <Suspense>
      <NyAvtaleForm />
    </Suspense>
  );
}
