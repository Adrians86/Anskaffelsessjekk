"use client";

import { useState } from "react";
import type { TerskelResult } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const OPPDRAGSGIVER = [
  { value: "statlig", label: "Statlig" },
  { value: "kommune", label: "Kommunal" },
  { value: "helseforetak", label: "Helseforetak" },
  { value: "forsvar", label: "Forsvar" },
];

const KONTRAKTTYPE = [
  { value: "vare_tjeneste", label: "Vare/tjeneste" },
  { value: "bygg_anlegg", label: "Bygg og anlegg" },
  { value: "konsesjonskontrakt", label: "Konsesjonskontrakt" },
];

const CONSEQUENCE_LABEL: Record<string, string> = {
  NASJONAL_KUNNGJORING: "Nasjonal kunngjøring",
  EOS_KUNNGJORING: "EØS-kunngjøring (Doffin + TED)",
  DIREKTE_ANSKAFFELSE_TILLATT: "Direkteanskaffelse tillatt",
  FORENKLET_PROSEDYRE: "Forenklet prosedyre",
  INGEN_REGEL_TRUFFET: "Ingen treffende regel",
};

export default function TerskelsjekePage() {
  const [verdi, setVerdi] = useState("");
  const [oppdragsgiver, setOppdragsgiver] = useState("statlig");
  const [kontrakttype, setKontrakttype] = useState("vare_tjeneste");
  const [results, setResults] = useState<TerskelResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const res = await fetch(`${API_BASE}/api/terskelsjekk`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          verdi: parseFloat(verdi),
          oppdragsgiver,
          kontrakttype,
        }),
      });
      if (!res.ok) throw new Error(`${res.status}`);
      const data: TerskelResult[] = await res.json();
      setResults(data);
    } catch {
      setError("Kunne ikke kontakte API. Start serveren og prøv igjen.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <div className="text-xs uppercase tracking-widest text-copper font-semibold">Regelverk</div>
        <h1 className="font-serif text-3xl font-bold text-ink mt-1">Terskelsjekk</h1>
        <p className="text-sm text-muted mt-1">
          Finn riktig anskaffelsesprosedyre basert på estimert kontraktsverdi.
        </p>
      </div>

      <div className="bg-card border border-line rounded-xl p-6 mb-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">
              Estimert verdi (NOK ekskl. mva)
            </label>
            <input
              type="number"
              min="0"
              step="1000"
              required
              value={verdi}
              onChange={(e) => setVerdi(e.target.value)}
              placeholder="f.eks. 500000"
              className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-copper"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">
                Oppdragsgiver
              </label>
              <select
                value={oppdragsgiver}
                onChange={(e) => setOppdragsgiver(e.target.value)}
                className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-copper bg-white"
              >
                {OPPDRAGSGIVER.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">
                Kontrakttype
              </label>
              <select
                value={kontrakttype}
                onChange={(e) => setKontrakttype(e.target.value)}
                className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-copper bg-white"
              >
                {KONTRAKTTYPE.map((k) => (
                  <option key={k.value} value={k.value}>{k.label}</option>
                ))}
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !verdi}
            className="w-full bg-navy text-white font-semibold py-2 px-4 rounded-lg hover:bg-navy-light transition-colors disabled:opacity-50"
          >
            {loading ? "Sjekker…" : "Sjekk terskel"}
          </button>
        </form>
      </div>

      {error && (
        <div className="bg-avvik-bg border border-avvik/30 text-avvik rounded-lg p-4 text-sm mb-4">
          {error}
        </div>
      )}

      {results && (
        <div className="space-y-3">
          <div className="text-xs uppercase tracking-widest text-muted font-semibold mb-2">Resultat</div>
          {results.map((r, i) => (
            <div key={i} className="bg-card border border-line rounded-xl p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="text-xs text-muted font-medium mb-1">Regime</div>
                  <div className="font-bold text-ink">{r.regime}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-muted font-medium mb-1">Konsekvens</div>
                  <span className={`inline-block text-xs font-semibold px-2 py-0.5 rounded-full ${
                    r.consequence === "INGEN_REGEL_TRUFFET"
                      ? "bg-paper-dark text-muted"
                      : r.consequence.includes("EOS")
                      ? "bg-avvik-bg text-avvik"
                      : r.consequence === "DIREKTE_ANSKAFFELSE_TILLATT"
                      ? "bg-samsvar-bg text-samsvar"
                      : "bg-vurdering-bg text-vurdering"
                  }`}>
                    {CONSEQUENCE_LABEL[r.consequence] ?? r.consequence}
                  </span>
                </div>
              </div>
              <p className="text-sm text-ink mt-3">{r.citation}</p>
              {r.citation_url && (
                <a
                  href={r.citation_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-copper hover:text-copper-light mt-2 inline-block"
                >
                  Kilde →
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
