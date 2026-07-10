'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { LayoutDashboard, Package, TrendingUp, Calendar, BarChart3, AlertTriangle, Tag, ClipboardCheck, Upload, Settings, LogOut } from 'lucide-react'

const NAV = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/dashboard/upload', label: 'Import Data', icon: Upload },
  { href: '/dashboard/rop', label: 'ROP & Orders', icon: TrendingUp },
  { href: '/dashboard/stock', label: 'Stock', icon: Package },
  { href: '/dashboard/aging', label: 'Aging', icon: Calendar },
  { href: '/dashboard/abc', label: 'ABC Analysis', icon: BarChart3 },
  { href: '/dashboard/anomalies', label: 'Anomalies', icon: AlertTriangle },
  { href: '/dashboard/promotions', label: 'Promotions', icon: Tag },
  { href: '/dashboard/audit', label: 'ISO Audit', icon: ClipboardCheck },
  { href: '/dashboard/settings', label: 'Settings', icon: Settings },
]

const LANG_FLAGS: Record<string, string> = { EN: '🇬🇧', NO: '🇳🇴', PL: '🇵🇱' }

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="w-60 bg-[#1B2A4A] border-r border-[#2A4A7A] flex flex-col flex-shrink-0">
        <div className="px-5 py-5 border-b border-[#2A4A7A]">
          <div className="text-[#C9A84C] font-bold text-lg tracking-tight">⚙️ SpareParts AI</div>
          <div className="text-[#8899BB] text-xs mt-0.5">AS North Advisory</div>
        </div>

        <div className="px-4 py-3 border-b border-[#2A4A7A] flex gap-2">
          {['NO', 'EN', 'PL'].map(l => (
            <button key={l} className="flex-1 text-xs py-1 rounded border border-[#2A4A7A] hover:border-[#C9A84C] hover:text-[#C9A84C] text-[#8899BB] transition-colors">{LANG_FLAGS[l]} {l}</button>
          ))}
        </div>

        <nav className="flex-1 px-3 py-3 space-y-0.5 overflow-y-auto">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || (href !== '/dashboard' && pathname.startsWith(href))
            return (
              <Link key={href} href={href} className={`nav-link ${active ? 'active' : ''}`}>
                <Icon size={16} />
                {label}
              </Link>
            )
          })}
        </nav>

        <div className="px-3 py-3 border-t border-[#2A4A7A]">
          <button className="nav-link w-full text-red-400 hover:text-red-300">
            <LogOut size={16} />
            Sign out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto bg-[#0F1A2E]">{children}</main>
    </div>
  )
}
