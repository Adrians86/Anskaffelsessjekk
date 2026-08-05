"use client";

import { useState, useEffect, useRef } from "react";
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
  supplier_org: string | null;
  supplier_id: number | null;
  amount: number;
  currency: string;
  invoice_date: string | null;
  lines: DraftLine[];
}

interface SupplierLookupRow {
  id: number;
  name: string;
  org_number: string;
}

type Tab = "ehf" | "csv" | "pdf";

function CreateSupplierButton({
  name,
  orgNumber,
  onCreated,
}: {
  name: string;
  orgNumber: string;
  onCreated: (sup: SupplierLookupRow) => void;
}) {
  const [creating, setCreating] = useState(false);
  const [done, setDone] = useState(false);

  async function handleCreate() {
    setCreating(true);
    try {
      const res = await fetch(`${API_BASE}/api/suppliers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, org_number: orgNumber }),
      });
      if (!res.ok) throw new Error(`${res.status}`);
      const sup = await res.json();
      setDone(true);
      onCreated({ id: sup.id, name: sup.name, org_number: sup.org_number });
    } catch {
      setCreating(false);
    }
  }

  if (done) return null;
  return (
    <button
      onClick={handleCreate}
      disabled={creating}
      className="text-xs font-semibold text-copper border border-copper/40 px-2 py-0.5 rounded hover:bg-copper/10 transition-colors disabled:opacity-50"
    >
      {creating ? "Oppretter…" : `Opprett «${name}»`}
    </button>
  );
}

function DraftCard({
  draft,
  onError,
}: {
  draft: Draft;
  onError: (msg: string) => void;
}) {
  const router = useRouter();
  const [confirming, setConfirming] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState<SupplierLookupRow | null>(
    draft.supplier_id != null
      ? { id: draft.supplier_id, name: draft.supplier_name, org_number: draft.supplier_org ?? "" }
      : null,
  );
  const [showSearch, setShowSearch] = useState(draft.supplier_id == null);
  const [searchQuery, setSearchQuery] = useState(draft.supplier_org ?? "");
  const [searchResults, setSearchResults] = useState<SupplierLookupRow[]>([]);
  const [searching, setSearching] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!showSearch) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (searchQuery.length < 2) {
      setSearchResults([]);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await fetch(`${API_BASE}/api/suppliers/lookup?q=${encodeURIComponent(searchQuery)}`);
        if (res.ok) setSearchResults(await res.json());
      } finally {
        setSearching(false);
      }
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchQuery, showSearch]);

  async function handleConfirm() {
    if (!selectedSupplier) {
      onError("Velg leverandør før bekreftelse");
      return;
    }
    setConfirming(true);
    try {
      const res = await fetch(`${API_BASE}/api/invoices/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          invoice_number: draft.invoice_number,
          supplier_id: selectedSupplier.id,
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
      onError(err instanceof Error ? err.message : "Bekreftelse feilet");
      setConfirming(false);
    }
  }

  return (
    <div className="bg-card border border-line rounded-xl p-5">
      {/* Invoice header */}
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

      {/* Supplier selection */}
      <div className="mb-4 border border-line rounded-lg p-3 bg-paper-dark">
        <div className="text-xs font-semibold text-muted uppercase tracking-wide mb-2">
          Leverandør <span className="text-avvik">*</span>
        </div>

        {selectedSupplier && !showSearch ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-samsvar text-sm">✓</span>
              <span className="font-medium text-sm text-ink">{selectedSupplier.name}</span>
              {selectedSupplier.org_number && (
                <span className="text-xs text-muted">{selectedSupplier.org_number}</span>
              )}
              {draft.supplier_id != null && (
                <span className="text-xs text-samsvar bg-samsvar-bg px-1.5 py-0.5 rounded">
                  Automatisk koblet
                </span>
              )}
            </div>
            <button
              onClick={() => { setShowSearch(true); setSearchQuery(""); setSearchResults([]); }}
              className="text-xs text-copper hover:text-copper-light flex-shrink-0 ml-2"
            >
              Endre
            </button>
          </div>
        ) : (
          <div>
            {draft.supplier_org && !draft.supplier_id && (
              <div className="text-xs text-avvik mb-2 flex items-center gap-2 flex-wrap">
                <span>⚠ Org.nr {draft.supplier_org} ikke funnet</span>
                {draft.supplier_name && (
                  <CreateSupplierButton
                    name={draft.supplier_name}
                    orgNumber={draft.supplier_org}
                    onCreated={(sup) => { setSelectedSupplier(sup); setShowSearch(false); }}
                  />
                )}
                <span className="text-muted">— eller søk manuelt nedenfor</span>
              </div>
            )}
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Søk på navn eller org.nr…"
                className="w-full border border-line rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-copper"
              />
              {searching && (
                <span className="absolute right-3 top-2 text-xs text-muted">Søker…</span>
              )}
            </div>
            {searchResults.length > 0 && (
              <div className="mt-1 border border-line rounded-lg overflow-hidden">
                {searchResults.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => { setSelectedSupplier(s); setShowSearch(false); }}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-paper flex items-center justify-between border-b border-line last:border-b-0"
                  >
                    <span className="font-medium">{s.name}</span>
                    <span className="text-xs text-muted">{s.org_number}</span>
                  </button>
                ))}
              </div>
            )}
            {searchQuery.length >= 2 && !searching && (
              <div className="mt-2">
                <CreateSupplierButton
                  name={searchQuery}
                  orgNumber=""
                  onCreated={(sup) => { setSelectedSupplier(sup); setShowSearch(false); }}
                />
              </div>
            )}
            {selectedSupplier && (
              <button
                onClick={() => setShowSearch(false)}
                className="text-xs text-muted mt-1.5 hover:text-ink"
              >
                Avbryt
              </button>
            )}
          </div>
        )}
      </div>

      {/* Lines table */}
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
        onClick={handleConfirm}
        disabled={confirming || !selectedSupplier}
        className="bg-copper text-white font-semibold py-2 px-6 rounded-lg hover:bg-copper-light transition-colors disabled:opacity-50 text-sm"
      >
        {confirming ? "Kontrollerer…" : "Bekreft og kontroller →"}
      </button>
    </div>
  );
}

export default function NyFakturaPage() {
  const [tab, setTab] = useState<Tab>("ehf");
  const [file, setFile] = useState<File | null>(null);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    setDrafts([]);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const endpoint =
        tab === "ehf" ? "/api/invoices/upload/ehf"
        : tab === "csv" ? "/api/invoices/upload/csv"
        : "/api/invoices/upload/pdf";
      const res = await fetch(`${API_BASE}${endpoint}`, { method: "POST", body: fd });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const detail: string = err.detail ?? `${res.status}`;
        if (detail.startsWith("no_text_layer")) {
          throw new Error("Skannet dokument — fyll inn feltene manuelt.");
        }
        throw new Error(detail);
      }
      const data = await res.json();
      setDrafts(Array.isArray(data) ? data : [data]);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Opplasting feilet");
    } finally {
      setUploading(false);
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
          Last opp EHF, CSV eller PDF/bilde — parse, bekreft og kontroller mot avtalt prisliste.
        </p>
      </div>

      {/* Tab selector */}
      <div className="flex gap-1 border-b border-line mb-6">
        {(["ehf", "csv", "pdf"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => { setTab(t); setFile(null); setDrafts([]); setUploadError(null); }}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === t ? "border-copper text-copper" : "border-transparent text-muted hover:text-ink"
            }`}
          >
            {t === "ehf" ? "EHF / XML" : t === "csv" ? "CSV batch" : "PDF / JPG"}
          </button>
        ))}
      </div>

      <div className="bg-card border border-line rounded-xl p-6 mb-6">
        <div>
          <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-2">
            {tab === "ehf" ? "EHF-fil (.xml, .ehf)" : tab === "csv" ? "CSV-fil (.csv)" : "PDF eller bilde (.pdf, .jpg, .png)"}
          </label>
          <input
            type="file"
            accept={tab === "ehf" ? ".xml,.ehf" : tab === "csv" ? ".csv" : ".pdf,.jpg,.jpeg,.png"}
            onChange={(e) => { setFile(e.target.files?.[0] ?? null); setDrafts([]); }}
            className="block w-full text-sm text-muted file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border file:border-line file:text-sm file:font-semibold file:bg-paper-dark file:text-ink hover:file:bg-paper"
          />
        </div>
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="mt-4 bg-navy text-white font-semibold py-2 px-6 rounded-lg hover:bg-navy-light transition-colors disabled:opacity-50"
        >
          {uploading
            ? "Laster opp…"
            : tab === "pdf"
            ? "Les faktura"
            : "Last opp og parse"}
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
          {drafts.map((draft, i) => (
            <DraftCard key={i} draft={draft} onError={setUploadError} />
          ))}
        </div>
      )}
    </div>
  );
}
