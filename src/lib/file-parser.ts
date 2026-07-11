import * as XLSX from 'xlsx'

export interface ColumnMapping {
  column_index: number
  column_name: string
  confidence: number
  source: 'heuristic' | 'content' | 'manual'
}

export type MappingResult = Partial<Record<SemanticField, ColumnMapping>>

export type SemanticField =
  | 'material_number'
  | 'description'
  | 'quantity'
  | 'date'
  | 'movement_type'
  | 'storage_location'
  | 'unit_price'
  | 'safety_stock'
  | 'open_orders'
  | 'unit'

export interface ParsedFile {
  headers: string[]
  rows: string[][]
  headerRow: number
  rawSheet: XLSX.WorkSheet
  filename: string
}

export async function parseFile(file: File): Promise<ParsedFile> {
  const buffer = await file.arrayBuffer()
  const wb = XLSX.read(buffer, { type: 'array', cellDates: true })
  const ws = wb.Sheets[wb.SheetNames[0]]
  const raw: string[][] = XLSX.utils.sheet_to_json(ws, { header: 1, raw: false, dateNF: 'YYYY-MM-DD', defval: '' }) as string[][]

  const headerRow = findHeaderRow(raw)
  const headers = raw[headerRow].map(h => String(h || '').trim())

  return { headers, rows: raw.slice(headerRow + 1).filter(r => r.some(c => c !== '')), headerRow, rawSheet: ws, filename: file.name }
}

function findHeaderRow(data: string[][]): number {
  let best = 0
  let bestCount = 0
  for (let i = 0; i < Math.min(10, data.length); i++) {
    const nonEmpty = data[i].filter(c => c !== '').length
    if (nonEmpty > bestCount) { bestCount = nonEmpty; best = i }
  }
  return best
}

export function mapColumns(parsed: ParsedFile): MappingResult {
  const { headers, rows } = parsed
  const mapping: MappingResult = {}
  const used = new Set<number>()
  const sample = rows.slice(0, 15)

  const patterns: Record<SemanticField, RegExp[]> = {
    material_number: [/material\b/i, /matnr/i, /nr.?kat/i, /part.?no/i],
    description: [/desc/i, /bezeichnung/i, /beskrivelse/i, /opis/i, /name\b/i],
    date: [/date\b/i, /datum/i, /dato\b/i, /booking/i, /data\b/i],
    movement_type: [/movement/i, /mvt\b/i, /bwart/i, /bevegelse/i],
    storage_location: [/sloc/i, /storage/i, /lagerort/i, /magazyn/i, /location\b/i],
    unit_price: [/price\b/i, /preis/i, /pris\b/i, /cena/i, /standard.?price/i],
    safety_stock: [/safety/i, /sicherheit/i, /sikkerhet/i, /min.?zapas/i],
    unit: [/\bbun\b/i, /\buom\b/i, /unit\b/i, /einheit/i, /enhet/i],
    quantity: [/quantity/i, /qty\b/i, /menge\b/i, /mengde/i, /ilosc/i, /unrestricted/i],
    open_orders: [/open.?order/i, /in.?order/i, /bestilling/i],
  }

  for (const [field, pats] of Object.entries(patterns) as [SemanticField, RegExp[]][]) {
    for (let i = 0; i < headers.length; i++) {
      if (used.has(i)) continue
      if (pats.some(p => p.test(headers[i]))) {
        mapping[field] = { column_index: i, column_name: headers[i], confidence: 0.85, source: 'heuristic' }
        used.add(i)
        break
      }
    }
  }

  for (let i = 0; i < headers.length; i++) {
    if (used.has(i)) continue
    const colVals = sample.map(r => String(r[i] || '').trim()).filter(Boolean)
    if (!colVals.length) continue

    const unique = new Set(colVals).size
    const isConstant = unique <= 2
    const sapMinus = colVals.filter(v => /^\d+[\.,]?\d*-$/.test(v)).length
    if (sapMinus >= 3 && !isConstant && !mapping.quantity) {
      const maxLen = Math.max(...colVals.map(v => v.replace('-', '').length))
      if (maxLen <= 6) {
        mapping.quantity = { column_index: i, column_name: headers[i] || `Col_${i}`, confidence: 0.92, source: 'content' }
        used.add(i)
        continue
      }
    }

    const dateHits = colVals.filter(v => /^\d{4}-\d{2}-\d{2}/.test(v)).length
    if (dateHits >= 3 && !mapping.date) {
      mapping.date = { column_index: i, column_name: headers[i] || `Col_${i}`, confidence: 0.9, source: 'content' }
      used.add(i)
      continue
    }

    const matHits = colVals.filter(v => /^\d{5,12}$/.test(v)).length
    if (matHits >= 5 && unique >= 3 && !mapping.material_number) {
      mapping.material_number = { column_index: i, column_name: headers[i] || `Col_${i}`, confidence: 0.82, source: 'content' }
      used.add(i)
      continue
    }

    const mvtHits = colVals.filter(v => /^(101|201|261|311|312|601|551)$/.test(v)).length
    if (mvtHits >= 3 && !mapping.movement_type) {
      mapping.movement_type = { column_index: i, column_name: headers[i] || `Col_${i}`, confidence: 0.95, source: 'content' }
      used.add(i)
      continue
    }

    const descHits = colVals.filter(v => v.length > 8 && !/^\d/.test(v)).length
    if (descHits >= 5 && !mapping.description) {
      mapping.description = { column_index: i, column_name: headers[i] || `Col_${i}`, confidence: 0.7, source: 'content' }
      used.add(i)
    }
  }

  return mapping
}

export interface MappedRow {
  material_number: string
  description: string
  quantity: number
  date: string
  movement_type: string
  storage_location: string
  unit_price: number
  safety_stock: number
  unit: string
  is_issue: boolean
}

const ISSUE_TYPES = new Set(['261', '201', '601', '551', '543'])

function cleanNumber(val: string): number {
  if (!val) return 0
  const s = String(val).trim()
  const negative = s.endsWith('-')
  const clean = s.replace(/-/g, '').replace(/\s/g, '').replace(',', '.')
  const n = parseFloat(clean)
  return isNaN(n) ? 0 : (negative ? -n : n)
}

function cleanDate(val: string): string {
  if (!val) return ''
  if (/^\d{4}-\d{2}-\d{2}/.test(val)) return val.slice(0, 10)
  const m = val.match(/^(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})/)
  if (m) return `${m[3]}-${m[2].padStart(2, '0')}-${m[1].padStart(2, '0')}`
  return val.slice(0, 10)
}

export function applyMapping(parsed: ParsedFile, mapping: MappingResult): MappedRow[] {
  const results: MappedRow[] = []

  for (const row of parsed.rows) {
    const get = (field: SemanticField): string => mapping[field] != null ? String(row[mapping[field]!.column_index] || '').trim() : ''

    const matNum = get('material_number')
    const dateStr = cleanDate(get('date'))
    if (!matNum || !dateStr) continue

    const qtyRaw = get('quantity')
    const qty = cleanNumber(qtyRaw)
    const isNegativeSAP = String(row[mapping.quantity?.column_index ?? -1] || '').trim().endsWith('-')
    const mvtType = get('movement_type')
    const isIssue = isNegativeSAP || ISSUE_TYPES.has(mvtType) || qty < 0

    results.push({
      material_number: matNum,
      description: get('description'),
      quantity: Math.abs(qty),
      date: dateStr,
      movement_type: mvtType,
      storage_location: get('storage_location'),
      unit_price: cleanNumber(get('unit_price')),
      safety_stock: cleanNumber(get('safety_stock')),
      unit: get('unit') || 'PC',
      is_issue: isIssue,
    })
  }

  return results
}

export interface MappingIssue {
  field: SemanticField
  level: 'error' | 'warn'
  message: string
}

export function validateMapping(parsed: ParsedFile, mapping: MappingResult): MappingIssue[] {
  const issues: MappingIssue[] = []
  const sample = parsed.rows.slice(0, 20)
  const colVals = (idx: number) => sample.map(r => String(r[idx] ?? '').trim()).filter(Boolean)

  const required: [SemanticField, string][] = [
    ['material_number', 'Material Number'],
    ['date', 'Date'],
    ['quantity', 'Quantity'],
  ]
  for (const [f, label] of required) {
    if (mapping[f] == null) {
      issues.push({ field: f, level: 'error', message: `${label} is not mapped yet. Pick the matching column from the dropdown.` })
    }
  }

  if (mapping.date != null) {
    const vals = colVals(mapping.date.column_index)
    const hits = vals.filter(v => /^\d{4}-\d{2}-\d{2}/.test(v) || /^\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4}/.test(v)).length
    if (vals.length && hits / vals.length < 0.5) {
      issues.push({ field: 'date', level: 'error', message: `The "Date" field points to a column that is not dates (e.g. "${vals[0]}"). Choose the column with values like 2025-08-02.` })
    }
  }

  if (mapping.quantity != null) {
    const vals = colVals(mapping.quantity.column_index)
    const hits = vals.filter(v => /^-?\d+([.,]\d+)?-?$/.test(v)).length
    if (vals.length && hits / vals.length < 0.5) {
      issues.push({ field: 'quantity', level: 'error', message: `The "Quantity" field points to a column that is not numbers (e.g. "${vals[0]}"). Choose the quantity column.` })
    }
  }

  if (mapping.material_number != null) {
    const vals = colVals(mapping.material_number.column_index)
    const dateish = vals.filter(v => /^\d{4}-\d{2}-\d{2}/.test(v)).length
    if (vals.length && dateish / vals.length > 0.5) {
      issues.push({ field: 'material_number', level: 'warn', message: `The "Material Number" field looks like dates. Double-check the mapping.` })
    }
  }

  return issues
}
