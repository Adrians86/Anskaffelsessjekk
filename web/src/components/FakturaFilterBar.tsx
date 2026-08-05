"use client";

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useCallback } from "react";

export function FakturaFilterBar({
  currentVerdikt,
  currentStatus,
  currentSearch,
}: {
  currentVerdikt: string;
  currentStatus: string;
  currentSearch: string;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const update = useCallback(
    (key: string, value: string) => {
      const params = new URLSearchParams(searchParams.toString());
      if (value) {
        params.set(key, value);
      } else {
        params.delete(key);
      }
      params.delete("side");
      router.push(`${pathname}?${params.toString()}`);
    },
    [router, pathname, searchParams]
  );

  return (
    <div className="flex flex-wrap gap-2 mb-4">
      <select
        value={currentVerdikt}
        onChange={(e) => update("verdikt", e.target.value)}
        className="border border-line rounded-lg px-3 py-1.5 text-xs bg-white focus:outline-none focus:border-copper"
      >
        <option value="">Alle verdikter</option>
        <option value="AVVIK">AVVIK</option>
        <option value="TIL_VURDERING">TIL VURDERING</option>
        <option value="SAMSVAR">SAMSVAR</option>
      </select>

      <select
        value={currentStatus}
        onChange={(e) => update("status", e.target.value)}
        className="border border-line rounded-lg px-3 py-1.5 text-xs bg-white focus:outline-none focus:border-copper"
      >
        <option value="">Alle statuser</option>
        <option value="ny">Ny</option>
        <option value="under_kontroll">Under kontroll</option>
        <option value="godkjent">Godkjent</option>
        <option value="avvist">Avvist</option>
      </select>

      <input
        type="search"
        placeholder="Søk fakturanr / leverandør…"
        defaultValue={currentSearch}
        onChange={(e) => update("soek", e.target.value)}
        className="border border-line rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-copper min-w-48"
      />

      {(currentVerdikt || currentStatus || currentSearch) && (
        <button
          onClick={() => {
            const params = new URLSearchParams();
            router.push(`${pathname}?${params.toString()}`);
          }}
          className="px-3 py-1.5 text-xs text-muted border border-line rounded-lg hover:border-navy"
        >
          Nullstill
        </button>
      )}
    </div>
  );
}
