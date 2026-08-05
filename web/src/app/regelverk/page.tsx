import { fetchApi } from "@/lib/api";

interface RegelverkRow {
  id: string;
  regime: string;
  condition: string;
  consequence: string;
  citation: string;
  citation_url: string;
  valid_from: string;
  valid_to: string | null;
  active: boolean;
}

const REGIME_ORDER = ["FOA", "FOSA", "ART123"] as const;

const REGIME_LABELS: Record<string, { title: string; sub: string }> = {
  FOA: {
    title: "FOA — Klassisk sektor",
    sub: "Anskaffelsesloven + Forskrift om offentlige anskaffelser",
  },
  FOSA: {
    title: "FOSA — Forsvars- og sikkerhetsanskaffelser",
    sub: "Direktiv 2009/81/EF · protokollplikt fra 100 000 kr",
  },
  ART123: {
    title: "Art. 123 EEA — Vesentlige sikkerhetsinteresser",
    sub: "Unntak fra FOSA/FOA · RAF del III dokumentasjonsplikt",
  },
};

const CONSEQUENCE_LABELS: Record<string, string> = {
  UTENFOR_LOVEN: "Under innslagspunktet — loven gjelder ikke",
  DEL_I_GRUNNLEGGENDE: "Del I: Grunnleggende prinsipper, ingen kunngjøringsplikt",
  KUNNGJORING_DOFFIN_DEL_II: "Del II: Kunngjøringsplikt på Doffin",
  EOS_PROSEDYRE_DEL_III: "Del III: EØS-prosedyre — kunngjøring Doffin + TED",
  EOS_SAERLIGE_TJENESTER: "EØS særlige tjenester — lettere prosedyreregime",
  PROTOKOLLPLIKT: "Protokollplikt (vedlegg 3/4)",
  INGEN_NASJONAL_KUNNGJORINGSPLIKT: "Ingen nasjonal kunngjøringsplikt",
  EOS_PROSEDYRE_FOSA: "EØS-prosedyre etter direktiv 2009/81/EF",
  RAF_DEL_III_DOKUMENTASJONSPLIKT: "RAF del III: Dokumentasjonsplikt",
};

function sourceLabel(url: string): string {
  try {
    const host = new URL(url).hostname;
    if (host.includes("lovdata")) return "Lovdata";
    if (host.includes("regjeringen")) return "Regjeringen.no";
    return host;
  } catch {
    return "Kilde";
  }
}

export default async function RegelverkPage() {
  const rules = await fetchApi<RegelverkRow[]>("/api/regelverk");

  const grouped = Object.fromEntries(
    REGIME_ORDER.map((r) => [r, rules.filter((rule) => rule.regime === r)]),
  );

  return (
    <div className="max-w-5xl">
      <div className="mb-8">
        <div className="text-xs uppercase tracking-widest text-muted font-semibold mb-1">
          Regelverksgrunnlag
        </div>
        <h1 className="font-serif text-3xl font-bold text-ink">Regelverk</h1>
        <p className="text-sm text-muted mt-2 max-w-2xl">
          Gjeldende norsk anskaffelsesregelverk fra offisielle kilder. Brukes som grunnlag for
          terskelvurderinger og regelverkssjekk ved fakturakontroll.
        </p>
      </div>

      <div className="space-y-10">
        {REGIME_ORDER.map((regime) => {
          const rows = grouped[regime] ?? [];
          if (rows.length === 0) return null;
          const meta = REGIME_LABELS[regime];
          return (
            <section key={regime}>
              <div className="mb-3 pb-2 border-b-2 border-copper">
                <h2 className="font-serif text-lg font-semibold text-ink">{meta.title}</h2>
                <p className="text-xs text-muted mt-0.5">{meta.sub}</p>
              </div>
              <div className="overflow-x-auto rounded-xl border border-line">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-paper-dark border-b border-line text-left">
                      <th className="px-4 py-2.5 text-xs font-semibold text-muted uppercase tracking-wide">
                        Betingelse
                      </th>
                      <th className="px-4 py-2.5 text-xs font-semibold text-muted uppercase tracking-wide">
                        Konsekvens
                      </th>
                      <th className="px-4 py-2.5 text-xs font-semibold text-muted uppercase tracking-wide">
                        Kilde
                      </th>
                      <th className="px-4 py-2.5 text-xs font-semibold text-muted uppercase tracking-wide whitespace-nowrap">
                        Gjelder fra
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((rule) => (
                      <tr
                        key={rule.id}
                        className={`border-b border-line last:border-b-0 hover:bg-paper-dark/50 transition-colors ${
                          rule.active ? "" : "opacity-50"
                        }`}
                      >
                        <td className="px-4 py-3 text-xs text-ink leading-relaxed max-w-[280px]">
                          {rule.condition}
                        </td>
                        <td className="px-4 py-3 max-w-[260px]">
                          <span className="text-xs font-medium text-ink leading-snug block">
                            {CONSEQUENCE_LABELS[rule.consequence] ?? rule.consequence}
                          </span>
                          {!rule.active && (
                            <span className="inline-block mt-1 text-[10px] bg-paper-dark text-muted px-1.5 py-0.5 rounded">
                              Utløpt
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 max-w-[200px]">
                          <p className="text-xs text-muted leading-snug mb-1">{rule.citation}</p>
                          {rule.citation_url && (
                            <a
                              href={rule.citation_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-copper hover:text-copper-light hover:underline"
                            >
                              {sourceLabel(rule.citation_url)} ↗
                            </a>
                          )}
                        </td>
                        <td className="px-4 py-3 text-xs text-muted tabular-nums whitespace-nowrap align-top">
                          {rule.valid_from}
                          {rule.valid_to && (
                            <span className="block text-muted">→ {rule.valid_to}</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          );
        })}
      </div>

      <p className="text-xs text-muted mt-10 pt-4 border-t border-line">
        Kilde: Lovdata og Regjeringen.no. Alle beløp i NOK ekskl. mva. EØS-terskelverdier justert
        med virkning fra 21.04.2026 (regjeringen.no). Oppdateres ved regelverksendringer.
      </p>
    </div>
  );
}
