'use client'
import { useEffect, useState } from 'react'
import { Download, Sliders } from 'lucide-react'
import type { RopResult } from '@/lib/types'

const STATUS_BADGE: Record<string, string> = {
  OUT: 'badge-red', ORDER: 'badge-red', WATCH: 'badge-yellow', OVERSTOCK: 'badge-orange', OK: 'badge-green',
}

export default function RopPage() {
  const [results, setResults] = useState<RopResult[]>([])
  const [loading, setLoading] = useState(true)
  const [leadTime, setLeadTime] = useState(14)
  const [serviceLevel, setServiceLevel] = useState(95)
  const [filter, setFilter] = useState<string>('ALL')

  useEffect(() => {
    fetch('/api/rop').then(r => r.json()).then(d => {
      setResults(d.results || [])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const filtered = filter === 'ALL' ? results : results.filter(r => r.status === filter)
  const frozenTotal = results.reduce((s, r) => s + (r.frozen_capital || 0), 0)
  const critical = results.filter(r => ['OUT', 'ORDER'].includes(r.status)).length

  const exportCsv = () => {
    const toOrder = results.filter(r => ['OUT', 'ORDER'].includes(r.status))
    const csv = ['Material,Status,Action', ...toOrder.map(r => `${r.material_number},${r.status},"${r.action_text}"`)].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `orders_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-[#E8EDF5]">ROP & Orders</h1>
          <p className="text-[#8899BB] text-sm mt-1">Reorder Point analysis — what to order today</p>
        </div>
        <button onClick={exportCsv} className="btn-primary flex items-center gap-2"><Download size={16} /> Export Orders</button>
      </div>

      <div className="card-dark p-5 mb-6 flex flex-wrap gap-8">
        <div className="flex items-center gap-3">
          <Sliders size={16} className="text-[#C9A84C]" />
          <label className="text-sm text-[#8899BB]">Lead Time:</label>
          <input type="range" min={1} max={90} value={leadTime} onChange={e => setLeadTime(+e.target.value)} className="w-32 accent-[#C9A84C]" />
          <span className="text-[#E8EDF5] text-sm font-mono w-16">{leadTime} days</span>
        </div>
        <div className="flex items-center gap-3">
          <label className="text-sm text-[#8899BB]">Service Level:</label>
          <input type="range" min={85} max={99} value={serviceLevel} onChange={e => setServiceLevel(+e.target.value)} className="w-32 accent-[#C9A84C]" />
          <span className="text-[#E8EDF5] text-sm font-mono w-16">{serviceLevel}%</span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="kpi-card red"><div className="text-[11px] uppercase tracking-widest text-[#8899BB] mb-2">Critical</div><div className="text-2xl font-bold text-red-400">{critical}</div></div>
        <div className="kpi-card green"><div className="text-[11px] uppercase tracking-widest text-[#8899BB] mb-2">OK</div><div className="text-2xl font-bold text-green-400">{results.filter(r => r.status === 'OK').length}</div></div>
        <div className="kpi-card gold"><div className="text-[11px] uppercase tracking-widest text-[#8899BB] mb-2">Frozen Capital</div><div className="text-2xl font-bold text-[#C9A84C]">{frozenTotal.toLocaleString('no-NO')} NOK</div></div>
      </div>

      <div className="flex gap-2 mb-4">
        {['ALL', 'OUT', 'ORDER', 'WATCH', 'OK', 'OVERSTOCK'].map(s => (
          <button key={s} onClick={() => setFilter(s)} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filter === s ? 'bg-[#C9A84C] text-[#0F1A2E]' : 'bg-[#1E3158] text-[#8899BB] hover:text-[#E8EDF5]'}`}>{s}</button>
        ))}
      </div>

      <div className="card-dark overflow-hidden">
        {loading ? <div className="p-12 text-center text-[#8899BB]">Loading...</div> : filtered.length === 0 ? <div className="p-12 text-center text-[#8899BB]">No data. <a href="/dashboard/upload" className="text-[#C9A84C] underline">Upload a file first</a>.</div> : <table className="data-table w-full"><thead><tr><th>Material</th><th>Avg Daily</th><th>Safety Stock</th><th>ROP</th><th>Days to Stockout</th><th>Status</th><th>Action</th></tr></thead><tbody>{filtered.map(r => <tr key={r.material_number}><td className="font-mono text-[#C9A84C]">{r.material_number}</td><td>{r.avg_daily_usage?.toFixed(2)}</td><td>{r.safety_stock_calc?.toFixed(1)}</td><td className="font-semibold">{r.reorder_point?.toFixed(1)}</td><td>{r.days_to_stockout > 900 ? '∞' : Math.round(r.days_to_stockout)}</td><td><span className={STATUS_BADGE[r.status]}>{r.status}</span></td><td className="text-xs text-[#8899BB]">{r.action_text}</td></tr>)}</tbody></table>}
      </div>
    </div>
  )
}
