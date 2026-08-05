import Link from "next/link";

const NAV = [
  { href: "/", label: "Oversikt" },
  { href: "/faktura", label: "Fakturaer" },
  { href: "/leverandorer", label: "Leverandører" },
  { href: "/avtaler", label: "Avtaler" },
  { href: "/terskelsjekk", label: "Terskelsjekk" },
];

export function Header() {
  return (
    <header className="bg-navy border-b-2 border-copper">
      <div className="max-w-7xl mx-auto px-6 h-[52px] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-[26px] h-[26px] border-2 border-copper rounded-[7px] flex items-center justify-center text-copper text-xs font-bold flex-shrink-0">
            ✓
          </div>
          <Link href="/" className="text-white font-serif text-[17px] font-semibold tracking-tight hover:opacity-90 transition-opacity">
            Anskaffelsessjekk
          </Link>
        </div>
        <nav className="hidden sm:flex gap-1">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="text-white/80 hover:text-white hover:bg-white/10 text-sm px-3 py-1.5 rounded-md transition-colors"
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
