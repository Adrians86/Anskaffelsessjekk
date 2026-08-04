"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";

const PERIODS = [
  { value: "maned", label: "Måned" },
  { value: "kvartal", label: "Kvartal" },
  { value: "ar", label: "År" },
] as const;

export function PeriodSelector({ active }: { active: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const setPeriod = useCallback(
    (periode: string) => {
      const params = new URLSearchParams(searchParams.toString());
      params.set("periode", periode);
      params.delete("fra");
      params.delete("til");
      router.push(`/?${params.toString()}`);
    },
    [router, searchParams],
  );

  return (
    <div className="flex items-center gap-1">
      {PERIODS.map((p) => (
        <button
          key={p.value}
          onClick={() => setPeriod(p.value)}
          className={`px-3 py-1 text-xs font-medium rounded-md border transition-colors ${
            active === p.value
              ? "bg-navy text-white border-navy"
              : "bg-white text-muted border-hairline hover:border-navy hover:text-ink"
          }`}
        >
          {p.label}
        </button>
      ))}
    </div>
  );
}
