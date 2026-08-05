"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { SupplierDetail } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function SupplierEditForm({ supplier }: { supplier: SupplierDetail }) {
  const router = useRouter();
  const [name, setName] = useState(supplier.name);
  const [orgNumber, setOrgNumber] = useState(supplier.org_number);
  const [address, setAddress] = useState(supplier.address ?? "");
  const [postalCode, setPostalCode] = useState(supplier.postal_code ?? "");
  const [city, setCity] = useState(supplier.city ?? "");
  const [website, setWebsite] = useState(supplier.website ?? "");
  const [email, setEmail] = useState(supplier.email ?? "");
  const [phone, setPhone] = useState(supplier.phone ?? "");
  const [status, setStatus] = useState(supplier.status ?? "");
  const [categories, setCategories] = useState(supplier.categories ?? "");
  const [notes, setNotes] = useState(supplier.notes ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const res = await fetch(`${API_BASE}/api/suppliers/${supplier.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name || null,
          org_number: orgNumber || null,
          address: address || null,
          postal_code: postalCode || null,
          city: city || null,
          website: website || null,
          email: email || null,
          phone: phone || null,
          status: status || null,
          categories: categories || null,
          notes: notes || null,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `${res.status}`);
      }
      setSaved(true);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lagring feilet");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-lg">
      {error && (
        <div className="bg-avvik-bg border border-avvik/30 text-avvik rounded-lg p-3 text-sm mb-4">
          {error}
        </div>
      )}
      {saved && (
        <div className="bg-samsvar-bg border border-samsvar/30 text-samsvar rounded-lg p-3 text-sm mb-4">
          Lagret
        </div>
      )}
      <form onSubmit={handleSave} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <Field label="Navn" value={name} onChange={setName} required />
          <Field label="Org.nr" value={orgNumber} onChange={setOrgNumber} />
        </div>
        <Field label="Adresse" value={address} onChange={setAddress} />
        <div className="grid grid-cols-2 gap-3">
          <Field label="Postnr" value={postalCode} onChange={setPostalCode} />
          <Field label="Sted" value={city} onChange={setCity} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Field label="E-post" value={email} onChange={setEmail} type="email" />
          <Field label="Telefon" value={phone} onChange={setPhone} type="tel" />
        </div>
        <Field label="Nettsted" value={website} onChange={setWebsite} type="url" />
        <div>
          <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">
            Status
          </label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-copper bg-white"
          >
            <option value="">—</option>
            <option value="aktiv">Aktiv</option>
            <option value="inaktiv">Inaktiv</option>
            <option value="under_vurdering">Under vurdering</option>
          </select>
        </div>
        <Field label="Kategorier" value={categories} onChange={setCategories} placeholder="f.eks. IT, konsulent" />
        <div>
          <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">
            Notater
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={4}
            className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-copper resize-none"
          />
        </div>
        <button
          type="submit"
          disabled={saving}
          className="bg-navy text-white font-semibold py-2 px-6 rounded-lg hover:bg-navy-light transition-colors disabled:opacity-50"
        >
          {saving ? "Lagrer…" : "Lagre firmadata"}
        </button>
      </form>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  required,
  type = "text",
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  required?: boolean;
  type?: string;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">
        {label}
        {required && <span className="text-avvik ml-0.5">*</span>}
      </label>
      <input
        type={type}
        required={required}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-copper"
      />
    </div>
  );
}
