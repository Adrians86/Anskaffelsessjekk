"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function NyLeverandorPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [orgNumber, setOrgNumber] = useState("");
  const [address, setAddress] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [categories, setCategories] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/suppliers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          org_number: orgNumber,
          address: address || null,
          email: email || null,
          phone: phone || null,
          categories: categories || null,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `${res.status}`);
      }
      const supplier = await res.json();
      router.push(`/leverandorer/${supplier.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Noe gikk galt");
      setLoading(false);
    }
  }

  return (
    <div className="max-w-lg">
      <div className="mb-6">
        <div className="text-xs uppercase tracking-widest text-muted font-semibold">
          <a href="/leverandorer" className="text-copper hover:text-copper-light">Leverandører</a>
          {" / "}Ny
        </div>
        <h1 className="font-serif text-3xl font-bold text-ink mt-1">Ny leverandør</h1>
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
              Navn <span className="text-avvik">*</span>
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-copper"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">
              Org.nr (9 siffer)
            </label>
            <input
              type="text"
              pattern="\d{9}"
              title="9 siffer"
              value={orgNumber}
              onChange={(e) => setOrgNumber(e.target.value)}
              placeholder="123456789"
              className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-copper"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">
              Adresse
            </label>
            <input
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-copper"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">
                E-post
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-copper"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">
                Telefon
              </label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-copper"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">
              Kategorier
            </label>
            <input
              type="text"
              value={categories}
              onChange={(e) => setCategories(e.target.value)}
              placeholder="f.eks. IT, konsulent, vedlikehold"
              className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-copper"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={loading || !name}
              className="flex-1 bg-navy text-white font-semibold py-2 px-4 rounded-lg hover:bg-navy-light transition-colors disabled:opacity-50"
            >
              {loading ? "Lagrer…" : "Lagre leverandør"}
            </button>
            <a
              href="/leverandorer"
              className="px-4 py-2 border border-line rounded-lg text-sm text-muted hover:border-navy transition-colors"
            >
              Avbryt
            </a>
          </div>
        </form>
      </div>
    </div>
  );
}
