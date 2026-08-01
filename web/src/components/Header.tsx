import Link from "next/link";

export function Header() {
  return (
    <header className="bg-navy text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-14">
        <Link href="/" className="font-semibold tracking-wide text-sm">
          Anskaffelsessjekk
          <span className="opacity-70 font-normal ml-2">kontroll av offentlige anskaffelser</span>
        </Link>
        <nav className="hidden sm:flex gap-6 text-sm">
          <Link href="/" className="hover:opacity-80 transition-opacity">Oversikt</Link>
          <Link href="/faktura" className="hover:opacity-80 transition-opacity">Fakturaer</Link>
          <Link href="/leverandorer" className="hover:opacity-80 transition-opacity">Leverandører</Link>
        </nav>
      </div>
    </header>
  );
}
