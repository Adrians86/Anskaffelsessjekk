'use client'
import { useState, useCallback } from 'react'
import { Upload, CheckCircle, AlertCircle, ChevronDown } from 'lucide-react'
import { parseFile, mapColumns, applyMapping, type MappingResult, type SemanticField } from '@/lib/file-parser'

const FIELDS: { key: SemanticField; label: string; required: boolean }[] = [
  { key: 'material_number', label: 'Material Number', required: true },
  { key: 'date', label: 'Date', required: true },
  { key: 'quantity', label: 'Quantity', required: true },
  { key: 'movement_type', label: 'Movement Type', required: false },
  { key: 'description', label: 'Description', required: false },
  { key: 'storage_location', label: 'Storage Location', required: false },
  { key: 'unit_price', label: 'Unit Price', required: false },
  { key: 'safety_stock', label: 'Safety Stock', required: false },
  { key: 'unit', label: 'Unit of Measure', required: false },
]

type Step = 'upload' | 'mapping' | 'preview' | 'done'

export default function UploadPage() {
  const [step, setStep] = useState<Step>('upload')
  const [isDragging, setIsDragging] = useState(false)
  const [parsed, setParsed] = useState<Awaited<ReturnType<typeof parseFile>> | null>(null)
  const [mapping, setMapping] = useState<MappingResult>({})
  const [preview, setPreview] = useState<Record<string, string>[]>([])
  const [loading, setLoading] = useState(false)
  const [rowsImported, setRowsImported] = useState(0)
  const [error, setError] = useState('')

  const handleFile = useCallback(async (file: File) => {
    setError('')
    setLoading(true)
    try {
      const p = await parseFile(file)
      setParsed(p)
      const m = mapColumns(p)
      setMapping(m)
      setStep('mapping')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Could not read file')
    }
    setLoading(false)
  }, [])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }, [handleFile])

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }

  const applyAndPreview = () => {
    if (!parsed) return
    const rows = applyMapping(parsed, mapping)
    setPreview(rows.slice(0, 10).map(r => ({
      material_number: r.material_number,
      date: r.date,
      quantity: String(r.quantity),
      movement_type: r.movement_type,
      is_issue: r.is_issue ? '▼ issue' : '▲ receipt',
    })))
    setStep('preview')
  }

  const importData = async () => {
    if (!parsed) return
    setLoading(true)
    try {
      const rows = applyMapping(parsed, mapping)
      const res = await fetch('/api/import', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ rows, mapping, filename: parsed.filename }) })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Import failed')
      setRowsImported(data.rows_imported || rows.length)
      setStep('done')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Import failed')
    }
    setLoading(false)
  }

  const confidenceColor = (c: number) => c >= 0.85 ? 'text-green-400' : c >= 0.7 ? 'text-yellow-400' : 'text-red-400'

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-[#E8EDF5] mb-1">Import Data</h1>
      <p className="text-[#8899BB] text-sm mb-8">Upload any SAP export (MB51, MB52) or Excel file — AI maps columns automatically.</p>

      <div className="flex items-center gap-2 mb-8">
        {(['upload', 'mapping', 'preview', 'done'] as Step[]).map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${step === s ? 'bg-[#C9A84C] text-[#0F1A2E]' : (['upload', 'mapping', 'preview', 'done'] as Step[]).indexOf(step) > i ? 'bg-green-500 text-white' : 'bg-[#2A4A7A] text-[#8899BB]'}`}>
              {(['upload', 'mapping', 'preview', 'done'] as Step[]).indexOf(step) > i ? '✓' : i + 1}
            </div>
            <span className={`text-xs capitalize ${step === s ? 'text-[#C9A84C]' : 'text-[#8899BB]'}`}>{s}</span>
            {i < 3 && <div className="w-8 h-px bg-[#2A4A7A]" />}
          </div>
        ))}
      </div>

      {error && <div className="card-dark border-red-500/50 p-4 mb-6 flex items-center gap-3"><AlertCircle size={18} className="text-red-400 flex-shrink-0" /><span className="text-red-300 text-sm">{error}</span></div>}

      {step === 'upload' && (
        <div onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }} onDragLeave={() => setIsDragging(false)} onDrop={onDrop} className={`card-dark border-2 border-dashed rounded-2xl p-16 text-center transition-colors cursor-pointer ${isDragging ? 'border-[#C9A84C] bg-[#C9A84C]/5' : 'border-[#2A4A7A] hover:border-[#C9A84C]/50'}`} onClick={() => document.getElementById('file-input')?.click()}>
          <input id="file-input" type="file" accept=".csv,.xlsx,.xls,.txt" className="hidden" onChange={onInputChange} />
          {loading ? <div className="text-[#C9A84C] animate-pulse text-lg">Analyzing file...</div> : <><Upload size={48} className="text-[#C9A84C] mx-auto mb-4 opacity-70" /><h3 className="text-[#E8EDF5] font-semibold text-lg mb-2">Drop your file here</h3><p className="text-[#8899BB] text-sm mb-4">SAP MB51 · SAP MB52 · Excel · CSV — any ERP export</p><div className="inline-block btn-primary">Browse Files</div></>}
        </div>
      )}

      {step === 'mapping' && parsed && (
        <div className="card-dark p-6">
          <div className="section-title">Column Mapping</div>
          <p className="text-[#8899BB] text-sm mb-6">AI detected <strong className="text-[#C9A84C]">{Object.keys(mapping).length}</strong> fields from <strong className="text-[#E8EDF5]">{parsed.filename}</strong> ({parsed.rows.length} rows). Review and correct if needed.</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            {FIELDS.map(({ key, label, required }) => {
              const current = mapping[key]
              const headerOpts = parsed.headers.map((h, i) => ({ label: `Col ${i}: ${h || '—'}`, value: i }))

              return (
                <div key={key} className="bg-[#0F1A2E] rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-xs font-semibold text-[#8899BB] uppercase tracking-wide">{label}{required && <span className="text-red-400 ml-1">*</span>}</label>
                    {current && <span className={`text-xs ${confidenceColor(current.confidence)}`}>{Math.round(current.confidence * 100)}% conf.</span>}
                  </div>
                  <div className="relative">
                    <select value={current?.column_index ?? ''} onChange={(e) => {
                      const val = e.target.value
                      if (val === '') {
                        const m = { ...mapping }; delete m[key]; setMapping(m)
                      } else {
                        const idx = parseInt(val)
                        setMapping(prev => ({ ...prev, [key]: { column_index: idx, column_name: parsed.headers[idx], confidence: 1, source: 'manual' } }))
                      }
                    }} className="w-full bg-[#1E3158] border border-[#2A4A7A] rounded-lg px-3 py-2 text-sm text-[#E8EDF5] appearance-none pr-8 focus:border-[#C9A84C] focus:outline-none">
                      <option value="">— skip —</option>
                      {headerOpts.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                    </select>
                    <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-[#8899BB] pointer-events-none" />
                  </div>
                  {current && <div className="text-xs text-[#8899BB] mt-1.5 font-mono truncate">Sample: {parsed.rows[0]?.[current.column_index] ?? '—'}</div>}
                </div>
              )
            })}
          </div>

          <div className="flex gap-3">
            <button onClick={() => setStep('upload')} className="btn-secondary">← Back</button>
            <button onClick={applyAndPreview} disabled={!mapping.material_number} className="btn-primary disabled:opacity-50">Preview Data →</button>
          </div>
        </div>
      )}

      {step === 'preview' && (
        <div className="card-dark p-6">
          <div className="section-title">Data Preview</div>
          <p className="text-[#8899BB] text-sm mb-4">First 10 rows of {parsed?.rows.length} total. Looks correct?</p>

          <div className="overflow-x-auto rounded-lg border border-[#2A4A7A] mb-6">
            <table className="data-table w-full">
              <thead>
                <tr>
                  {Object.keys(preview[0] || {}).map(k => <th key={k}>{k}</th>)}
                </tr>
              </thead>
              <tbody>
                {preview.map((row, i) => <tr key={i}>{Object.values(row).map((v, j) => <td key={j} className="font-mono text-xs">{v}</td>)}</tr>)}
              </tbody>
            </table>
          </div>

          <div className="flex gap-3">
            <button onClick={() => setStep('mapping')} className="btn-secondary">← Back</button>
            <button onClick={importData} disabled={loading} className="btn-primary disabled:opacity-50">{loading ? 'Importing...' : `Import ${parsed?.rows.length} Rows →`}</button>
          </div>
        </div>
      )}

      {step === 'done' && (
        <div className="card-dark p-12 text-center">
          <CheckCircle size={56} className="text-green-400 mx-auto mb-4" />
          <h3 className="text-[#E8EDF5] font-semibold text-xl mb-2">Import Successful!</h3>
          <p className="text-[#8899BB] mb-6"><strong className="text-[#C9A84C]">{rowsImported}</strong> rows imported. ROP analysis is ready.</p>
          <div className="flex gap-3 justify-center">
            <a href="/dashboard/rop" className="btn-primary">View ROP Results</a>
            <button onClick={() => { setStep('upload'); setParsed(null); setMapping({}) }} className="btn-secondary">Import Another File</button>
          </div>
        </div>
      )}
    </div>
  )
}
