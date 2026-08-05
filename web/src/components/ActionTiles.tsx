import Link from "next/link";

const TILES = [
  {
    href: "/faktura/ny",
    icon: "📄",
    title: "Kontroller faktura",
    desc: "Last opp EHF, CSV eller PDF",
    accent: true,
  },
  {
    href: "/leverandorer/ny",
    icon: "🏢",
    title: "Ny leverandør",
    desc: "Legg til i kartoteket",
    accent: false,
  },
  {
    href: "/avtaler",
    icon: "📋",
    title: "Registrer avtale",
    desc: "Kontrakt og prisliste",
    accent: false,
  },
  {
    href: "/terskelsjekk",
    icon: "⚖️",
    title: "Terskelsjekk",
    desc: "Velg prosedyre etter verdi",
    accent: false,
  },
  {
    href: "/faktura",
    icon: "📊",
    title: "Arbeidsliste",
    desc: "Fakturaer som krever handling",
    accent: false,
  },
];

export function ActionTiles() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {TILES.map((tile) => (
        <Link
          key={tile.href}
          href={tile.href}
          className="bg-card border border-line rounded-[12px] p-4 hover:border-copper transition-colors group"
        >
          <div
            className={`w-[34px] h-[34px] rounded-[10px] flex items-center justify-center text-lg mb-3 ${
              tile.accent ? "bg-copper" : "bg-navy"
            }`}
          >
            {tile.icon}
          </div>
          <div className="font-bold text-sm text-ink group-hover:text-copper transition-colors">
            {tile.title}
          </div>
          <div className="text-xs text-muted mt-0.5">{tile.desc}</div>
        </Link>
      ))}
    </div>
  );
}
