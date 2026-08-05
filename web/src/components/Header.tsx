"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const NAV = [
  { href: "/", label: "Oversikt" },
  { href: "/faktura", label: "Fakturaer" },
  { href: "/leverandorer", label: "Leverandører" },
  { href: "/avtaler", label: "Avtaler" },
  { href: "/terskelsjekk", label: "Terskelsjekk" },
  { href: "/regelverk", label: "Regelverk" },
];

export function Header() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  function isActive(href: string) {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  }

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

        {/* Desktop nav */}
        <nav className="hidden sm:flex gap-1">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`text-sm px-3 py-1.5 rounded-md transition-colors ${
                isActive(item.href)
                  ? "text-white bg-white/15 font-semibold"
                  : "text-white/70 hover:text-white hover:bg-white/10"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          className="sm:hidden text-white/80 hover:text-white p-1"
          aria-label="Meny"
        >
          <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            {menuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile dropdown */}
      {menuOpen && (
        <div className="sm:hidden bg-navy-light border-t border-white/10 px-4 py-2">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMenuOpen(false)}
              className={`block px-3 py-2.5 text-sm rounded-md mb-0.5 transition-colors ${
                isActive(item.href)
                  ? "text-white bg-white/15 font-semibold"
                  : "text-white/70 hover:text-white hover:bg-white/10"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </div>
      )}
    </header>
  );
}
