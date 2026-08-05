"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface DraftLine {
  item_ref: string;
  description: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

interface Draft {
  invoice_number: string;
  supplier_name: string;
  amount: number;
  currency: string;
  invoice_date: string | null;
  lines: DraftLine[];
}

type Tab = "ehf" | "csv";

export default function NyFakturaPage() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("ehf");
  const [file, setFile] = useState<File | null>(null);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [confirming, setConfirming] = useState<number | null>(null);
  const [supplierId, setSupplierId] = useState("");

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    setDrafts([]);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const endpoint = tab === "ehf" ? "/api/invoices/upload/ehf" : "/api/invoices/upload/csv";
      const res = await fetch(`${API_BASE}${endpoint}`, { method: "POST", body: fd });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `${res.status}`);
      }
      const data = await res.json();
      setDrafts(Array.isArray(data) ? data : [data]);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Opplasting feilet");
    } finally {
      setUploading(false);
    }
  }

  async function handleConfirm(draft: Draft) {
    if (!supplierId) {
      setUploadError("Velg leverandør-ID før bekreftelse");
      return;
    }
    const idx = drafts.indexOf(draft);
    setConfirming(idx);
    setUploadError(null);
    try {
      const res = await fetch(`${API_BASE}/api/invoices/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          invoice_number: draft.invoice_number,
          supplier_id: parseInt(supplierId),
          amount: draft.amount,
          currency: draft.currency,
          invoice_date: draft.invoice_date ?? new Date().toISOString().slice(0, 10),
          lines: draft.lines,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `${res.status}`);
      }
      const saved = await res.json();
      router.push(`/faktura/${saved.id}`);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Bekreftelse feilet");
      setConfirming(null);
    }
  }

  return (
    <div className="max-w-3xl">
      <div className="mb-6">
        <div className="text-xs uppercase tracking-widest text-muted font-semibold">
          <Link href="/faktura" className="text-copper hover:text-copper-light">Fakturaer</Link>
          {" / "}Ny
        </div>
        <h1 className="font-serif text-3xl font-bold text-ink mt-1">Kontroller faktura</h1>
        <p className="text-sm text-muted mt-1">
          Last opp EHF eller CSV — parse, bekreft og kontroller mot avtalt prisliste.
        </p>
      </div>

      {/* Tab selector */}
      <div className="flex gap-1 border-b border-line mb-6">
        {(["ehf", "csv"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => { setTab(t); setFile(null); setDrafts([]); setUploadError(null); }}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === t
                ? "border-copper text-copper"
                : "border-transparent text-muted hover:text-ink"
            }`}
          >
            {t === "ehf" ? "EHF / XML" : "CSV batch"}
          </button>
        ))}
      </div>

      <div className="bg-card border border-line rounded-xl p-6 mb-6">
        <div>
          <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-2">
            {tab === "ehf" ? "EHF-fil (.xml, .ehf)" : "CSV-fil (.csv)"}
          </label>
          <input
            type="file"
            accept={tab === "ehf" ? ".xml,.ehf" : ".csv"}
            onChange={(e) => { setFile(e.target.files?.[0] ?? null); setDrafts([]); }}
            className="block w-full text-sm text-muted file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border file:border-line file:text-sm file:font-semibold file:bg-paper-dark file:text-ink hover:file:bg-paper"
          />
        </div>

        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="mt-4 bg-navy text-white font-semibold py-2 px-6 rounded-lg hover:bg-navy-light transition-colors disabled:opacity-50"
        >
          {uploading ? "Laster opp…" : "Last opp og parse"}
        </button>
      </div>

      {uploadError && (
        <div className="bg-avvik-bg border border-avvik/30 text-avvik rounded-lg p-4 text-sm mb-4">
          {uploadError}
        </div>
      )}

      {drafts.length > 0 && (
        <div className="space-y-4">
          <div className="text-xs uppercase tracking-widest text-muted font-semibold">
            {drafts.length} faktura{drafts.length !== 1 ? "er" : ""} lest — bekreft for å kontrollere
          </div>

          <div className="bg-card border border-line rounded-xl p-4 mb-4">
            <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">
              Leverandør-ID <span className="text-avvik">*</span>
            </label>
            <input
              type="number"
              min="1"
              value={supplierId}
              onChange={(e) => setSupplierId(e.target.value)}
              placeholder="ID fra leverandørregisteret"
              className="w-48 border border-line rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-copper"
            />
            <p className="text-xs text-muted mt-1">
              Finn ID-en i{" "}
              <Link href="/leverandorer" className="text-copper hover:text-copper-light">leverandøroversikten</Link>.
            </p>
          </div>

          {drafts.map((draft, i) => (
            <div key={i} className="bg-card border border-line rounded-xl p-5">
              <div className="flex items-start justify-between gap-4 mb-4">
                <div>
                  <div className="font-semibold text-ink">{draft.invoice_number || "Ukjent fakturanr"}</div>
                  <div className="text-sm text-muted">{draft.supplier_name}</div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-lg tabular-nums">
                    {draft.amount.toLocaleString("nb-NO", { minimumFractionDigits: 2 })} {draft.currency}
                  </div>
                  {draft.invoice_date && (
                    <div className="text-xs text-muted">{draft.invoice_date}</div>
                  )}
                </div>
              </div>

              {draft.lines.length > 0 && (
                <div className="border border-line rounded-lg overflow-hidden mb-4">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-paper-dark border-b border-line text-left">
                        <th className="px-3 py-2 font-medium text-muted">Ref</th>
                        <th className="px-3 py-2 font-medium text-muted">Beskrivelse</th>
                        <th className="px-3 py-2 font-medium text-muted text-right">Antall</th>
                        <th className="px-3 py-2 font-medium text-muted text-right">Enhetspris</th>
                        <th className="px-3 py-2 font-medium text-muted text-right">Sum</th>
                      </tr>
                    </thead>
                    <tbody>
                      {draft.lines.map((line, j) => (
                        <tr key={j} className="border-b border-line last:border-b-0">
                          <td className="px-3 py-1.5 font-semibold">{line.item_ref}</td>
                          <td className="px-3 py-1.5">{line.description}</td>
                          <td className="px-3 py-1.5 tabular-nums text-right">{line.quantity}</td>
                          <td className="px-3 py-1.5 tabular-nums text-right">{line.unit_price.toLocaleString("nb-NO")}</td>
                          <td className="px-3 py-1.5 tabular-nums text-right">{line.line_total.toLocaleString("nb-NO")}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <button
                onClick={() => handleConfirm(draft)}
                disabled={confirming === i || !supplierId}
                className="bg-copper text-white font-semibold py-2 px-6 rounded-lg hover:bg-copper-light transition-colors disabled:opacity-50 text-sm"
              >
                {confirming === i ? "Kontrollerer…" : "Bekreft og kontroller →"}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
