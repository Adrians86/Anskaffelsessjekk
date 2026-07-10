'use client'
import { useState } from 'react'
import { AlertTriangle, Package, TrendingDown, DollarSign, Tag, Upload } from 'lucide-react'
import Link from 'next/link'
import type { DashboardStats } from '@/lib/types'

const MOCK_STATS: DashboardStats = {
  total_materials: 64,
  critical_count: 3,
  watch_count: 7,
  ok_count: 54,
  frozen_capital_nok: 0,
  active_promotions: 0,
  last_import: '2026-06-01',
}

function KpiCard({ label, value, sub, accent, icon: Icon }: { label: string; value: string | number; sub?: string; accent: 'gold' | 'red' | 'green' | 'yellow' | 'orange'; icon: React.ElementType }) {
  const colors = { gold: 'border-t-[#C9A84C]', red: 'border-t-red-500', green: 'border-t-green-500', yellow: 'border-t-yellow-400', orange: 'border-t-orange-500' }
  const textColors = { gold: 'text-[#C9A84C]', red: 'text-red-400', green: 'text-green-400', yellow: 'text-yellow-400', orange: 'text-orange-400' }
  return (
    <div className={`card-dark p-5 border-t-4 ${colors[accent]}`}>
      <div className="flex items-start justify-between">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-widest text-[#8899BB] mb-2">{label}</div>
          <div className={`text-3xl font-bold ${textColors[accent]}`}>{value}</div>
          {sub && <div className="text-xs text-[#8899BB] mt-1">{sub}</div>}
        </div>
        <Icon size={20} className={`${textColors[accent]} opacity-60 mt-1`} />
      </div>
    </div>
  )
}

function StatusBar({ critical, watch, ok, total }: { critical: number; watch: number; ok: number; total: number }) {
  const pCrit = (critical / total) * 100
  const pWatch = (watch / total) * 100
  const pOk = (ok / total) * 100
  return (
    <div className="mt-2">
      <div className="flex h-2 rounded-full overflow-hidden gap-0.5">
        <div className="bg-red-500 transition-all" style={{ width: `${pCrit}%` }} />
        <div className="bg-yellow-400 transition-all" style={{ width: `${pWatch}%` }} />
        <div className="bg-green-500 transition-all" style={{ width: `${pOk}%` }} />
      </div>
      <div className="flex gap-4 mt-1.5 text-xs text-[#8899BB]">
        <span className="text-red-400">● {critical} critical</span>
        <span className="text-yellow-400">● {watch} monitor</span>
        <span className="text-green-400">● {ok} OK</span>
      </div>
    </div>
  )
}

function QuickAction({ href, icon: Icon, label, desc, color }: { href: string; icon: React.ElementType; label: string; desc: string; color: string }) {
  return (
    <Link href={href} className="card-dark p-4 flex items-center gap-4 hover:border-[#C9A84C]/50 transition-colors group cursor-pointer">
      <div className={`p-2.5 rounded-lg ${color} bg-opacity-20`}>
        <Icon size={18} className={color} />
      </div>
      <div>
        <div className="text-sm font-semibold text-[#E8EDF5] group-hover:text-[#C9A84C] transition-colors">{label}</div>
        <div className="text-xs text-[#8899BB]">{desc}</div>
      </div>
    </Link>
  )
}

export default function DashboardPage() {
  const [stats] = useState<DashboardStats>(MOCK_STATS)

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[#E8EDF5]">Dashboard</h1>
        <p className="text-[#8899BB] text-sm mt-1">AS North Advisory · SpareParts AI · {stats.last_import ? `Last import: ${stats.last_import}` : 'No data imported yet'}</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <KpiCard label="Total Materials" value={stats.total_materials} sub="In warehouse" accent="gold" icon={Package} />
        <KpiCard label="Order Now / Out" value={stats.critical_count} sub="Immediate action" accent="red" icon={AlertTriangle} />
        <KpiCard label="Monitor" value={stats.watch_count} sub="Order soon" accent="yellow" icon={TrendingDown} />
        <KpiCard label="Frozen Capital" value={stats.frozen_capital_nok > 0 ? `${stats.frozen_capital_nok.toLocaleString('no-NO')} NOK` : '—'} sub="Upload MB52 for value" accent="orange" icon={DollarSign} />
      </div>

      {stats.total_materials > 0 && (
        <div className="card-dark p-5 mb-8">
          <div className="section-title">Stock Health Overview</div>
          <StatusBar critical={stats.critical_count} watch={stats.watch_count} ok={stats.ok_count} total={stats.total_materials} />
        </div>
      )}

      <div className="section-title">Quick Actions</div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-8">
        <QuickAction href="/dashboard/upload" icon={Upload} label="Import SAP Data" desc="Upload MB51 or MB52 file" color="text-[#C9A84C]" />
        <QuickAction href="/dashboard/rop" icon={TrendingDown} label="View ROP Results" desc="Reorder points & actions" color="text-red-400" />
        <QuickAction href="/dashboard/promotions" icon={Tag} label="Create Promotion" desc="AI-generated campaigns for dead stock" color="text-green-400" />
      </div>

      {stats.total_materials === 0 && (
        <div className="card-dark p-12 text-center border-dashed">
          <Upload size={40} className="text-[#C9A84C] mx-auto mb-4 opacity-60" />
          <h3 className="text-[#E8EDF5] font-semibold text-lg mb-2">No data yet</h3>
          <p className="text-[#8899BB] text-sm mb-6 max-w-sm mx-auto">Upload your SAP MB51 (movement history) or MB52 (stock snapshot) to start the analysis.</p>
          <Link href="/dashboard/upload" className="btn-primary inline-block">Upload First File</Link>
        </div>
      )}
    </div>
  )
}
