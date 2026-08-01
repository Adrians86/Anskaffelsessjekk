const VERDICT_STYLES: Record<string, { label: string; fg: string; bg: string }> = {
  AVVIK: { label: "AVVIK", fg: "text-avvik", bg: "bg-avvik-bg" },
  TIL_VURDERING: { label: "TIL VURDERING", fg: "text-vurdering", bg: "bg-vurdering-bg" },
  SAMSVAR: { label: "SAMSVAR", fg: "text-samsvar", bg: "bg-samsvar-bg" },
};

export function VerdictPill({ verdict }: { verdict: string }) {
  const style = VERDICT_STYLES[verdict] || { label: verdict, fg: "text-muted", bg: "bg-gray-100" };
  return (
    <span className={`${style.bg} ${style.fg} text-[11px] font-bold tracking-wide px-2.5 py-0.5 rounded-full whitespace-nowrap`}>
      {style.label}
    </span>
  );
}
