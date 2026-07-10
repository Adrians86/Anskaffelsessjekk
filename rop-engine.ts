// src/lib/rop-engine.ts
// Silnik obliczeniowy ROP, Safety Stock, Anomaly Detection
// Działa po stronie serwera (API route) lub w Node.js

import type { StockMovement, RopResult, Lang } from './types'

const ISSUE_TYPES = new Set(['261', '201', '601', '551', '543'])
const RECEIPT_TYPES = new Set(['101', '501', '561'])

// Z-score dla poziomu obsługi
function zScore(serviceLevel: number): number {
  // Przybliżenie odwrotnej dystrybuanty normalnej
  const sl = Math.min(0.9999, Math.max(0.5001, serviceLevel))
  if (sl >= 0.99)  return 2.326
  if (sl >= 0.98)  return 2.054
  if (sl >= 0.97)  return 1.881
  if (sl >= 0.95)  return 1.645
  if (sl >= 0.90)  return 1.282
  if (sl >= 0.85)  return 1.036
  return 0.842
}

// Status i akcja w wybranym języku
function buildStatus(
  onHand: number,
  rop: number,
  forecast30: number,
  daysToStockout: number,
  lang: Lang
): { status: RopResult['status']; action_text: string } {
  const labels = {
    OUT:       { EN: '🔴 OUT OF STOCK',  NO: '🔴 TOM',          PL: '🔴 BRAK' },
    ORDER:     { EN: '🔴 ORDER NOW',     NO: '🔴 BESTILL NÅ',   PL: '🔴 ZAMÓW TERAZ' },
    WATCH:     { EN: '🟡 MONITOR',       NO: '🟡 OVERVÅK',      PL: '🟡 OBSERWUJ' },
    OVERSTOCK: { EN: '🟠 OVERSTOCK',     NO: '🟠 OVERLAGER',    PL: '🟠 PRZEBUDOWA' },
    OK:        { EN: '🟢 OK',            NO: '🟢 OK',           PL: '🟢 OK' },
  }

  if (onHand <= 0) {
    const qty = Math.max(1, Math.round(rop))
    return {
      status: 'OUT',
      action_text: {
        EN: `CRITICAL: no stock. Order min. ${qty} pcs.`,
        NO: `KRITISK: tomt. Bestill min. ${qty} stk.`,
        PL: `KRYTYCZNE: brak towaru. Zamów min. ${qty} szt.`,
      }[lang],
    }
  }
  if (onHand < rop) {
    const toOrder = Math.max(1, Math.round(rop - onHand + forecast30))
    const days = Math.round(daysToStockout)
    return {
      status: 'ORDER',
      action_text: {
        EN: `Order ${toOrder} pcs. (stock for ${days} days)`,
        NO: `Bestill ${toOrder} stk. (lager for ${days} dager)`,
        PL: `Zamów ${toOrder} szt. (zapas na ${days} dni)`,
      }[lang],
    }
  }
  if (onHand < rop * 1.2) {
    const days = Math.round(daysToStockout)
    return {
      status: 'WATCH',
      action_text: {
        EN: `Order soon — ${days} days to ROP`,
        NO: `Bestill snart — ${days} dager til ROP`,
        PL: `Zamów wkrótce — ${days} dni do ROP`,
      }[lang],
    }
  }
  if (onHand > rop * 3) {
    return {
      status: 'OVERSTOCK',
      action_text: {
        EN: 'Excess stock. Consider pausing orders.',
        NO: 'Overlager. Vurder å stoppe bestillinger.',
        PL: 'Nadmiar zapasu. Rozważ wstrzymanie zamówień.',
      }[lang],
    }
  }
  return {
    status: 'OK',
    action_text: { EN: 'No action needed', NO: 'Ingen handling', PL: 'Nie podejmuj akcji' }[lang],
  }
}

export interface RopInput {
  movements: StockMovement[]
  currentStock: Record<string, number>  // material_number → qty
  unitPrices: Record<string, number>    // material_number → price
  leadTimeDays: number
  serviceLevel: number   // 0.85 – 0.99
  organizationId: string
  lang: Lang
}

export function computeRop(input: RopInput): Omit<RopResult, 'id' | 'computed_at'>[] {
  const { movements, currentStock, unitPrices, leadTimeDays, serviceLevel, organizationId, lang } = input
  const z = zScore(serviceLevel)

  // Filtruj tylko wydania
  const issues = movements.filter(m =>
    m.is_issue || ISSUE_TYPES.has(m.movement_type)
  )

  if (!issues.length) return []

  // Grupuj wg materiału
  const byMaterial: Record<string, StockMovement[]> = {}
  for (const m of issues) {
    if (!byMaterial[m.material_number]) byMaterial[m.material_number] = []
    byMaterial[m.material_number].push(m)
  }

  const results: Omit<RopResult, 'id' | 'computed_at'>[] = []

  for (const [matNum, matMovements] of Object.entries(byMaterial)) {
    const dates = matMovements.map(m => new Date(m.posting_date))
    const minDate = new Date(Math.min(...dates.map(d => d.getTime())))
    const maxDate = new Date(Math.max(...dates.map(d => d.getTime())))
    const daysSpan = Math.max(1,
      (maxDate.getTime() - minDate.getTime()) / (1000 * 60 * 60 * 24)
    )

    const totalQty = matMovements.reduce((s, m) => s + Math.abs(m.quantity), 0)
    const avgDaily = totalQty / daysSpan

    // Miesięczna agregacja → std
    const monthly: Record<string, number> = {}
    for (const m of matMovements) {
      const key = m.posting_date.slice(0, 7) // YYYY-MM
      monthly[key] = (monthly[key] || 0) + Math.abs(m.quantity)
    }
    const monthlyVals = Object.values(monthly)
    const mean = monthlyVals.reduce((s, v) => s + v, 0) / (monthlyVals.length || 1)
    const variance = monthlyVals.reduce((s, v) => s + (v - mean) ** 2, 0) / Math.max(1, monthlyVals.length - 1)
    const stdMonthly = Math.sqrt(variance) || avgDaily * 30 * 0.3
    const stdDaily = stdMonthly / 30

    // Safety Stock i ROP
    const safetyStock = z * stdDaily * Math.sqrt(leadTimeDays)
    const rop = avgDaily * leadTimeDays + safetyStock
    const forecast30 = avgDaily * 30

    // Stan i wartość
    const onHand = currentStock[matNum] ?? 0
    const unitPrice = unitPrices[matNum] ?? 0
    const frozenCapital = onHand * unitPrice
    const daysToStockout = avgDaily > 0 ? onHand / avgDaily : 9999

    const { status, action_text } = buildStatus(onHand, rop, forecast30, daysToStockout, lang)

    results.push({
      organization_id: organizationId,
      material_number: matNum,
      avg_daily_usage: Math.round(avgDaily * 10000) / 10000,
      std_daily: Math.round(stdDaily * 10000) / 10000,
      safety_stock_calc: Math.max(0, Math.round(safetyStock * 10) / 10),
      reorder_point: Math.max(0, Math.round(rop * 10) / 10),
      forecast_30d: Math.round(forecast30 * 10) / 10,
      days_to_stockout: Math.round(daysToStockout * 10) / 10,
      frozen_capital: Math.round(frozenCapital * 100) / 100,
      status,
      action_text,
      lead_time_used: leadTimeDays,
      service_level_used: serviceLevel,
    })
  }

  // Sortuj: krytyczne pierwsze
  const order = { OUT: 1, ORDER: 2, WATCH: 3, OVERSTOCK: 4, OK: 5 }
  return results.sort((a, b) => (order[a.status] || 9) - (order[b.status] || 9))
}

// ── Anomaly Detection ──────────────────────────────────────
export interface Anomaly {
  material_number: string
  type: 'SURGE' | 'DROP'
  last_month_qty: number
  hist_avg: number
  ratio?: number
  recommendation_en: string
  recommendation_no: string
  recommendation_pl: string
}

export function detectAnomalies(
  movements: StockMovement[],
  thresholdFactor = 3.0
): Anomaly[] {
  const issues = movements.filter(m => m.is_issue || ISSUE_TYPES.has(m.movement_type))

  // Miesięczna agregacja
  const monthly: Record<string, Record<string, number>> = {}
  for (const m of issues) {
    const mat = m.material_number
    const month = m.posting_date.slice(0, 7)
    if (!monthly[mat]) monthly[mat] = {}
    monthly[mat][month] = (monthly[mat][month] || 0) + Math.abs(m.quantity)
  }

  const anomalies: Anomaly[] = []

  for (const [mat, months] of Object.entries(monthly)) {
    const sorted = Object.keys(months).sort()
    if (sorted.length < 2) continue

    const history = sorted.slice(0, -1).map(k => months[k])
    const lastMonth = months[sorted[sorted.length - 1]]
    const histAvg = history.reduce((s, v) => s + v, 0) / history.length

    if (histAvg > 0 && lastMonth > histAvg * thresholdFactor) {
      anomalies.push({
        material_number: mat,
        type: 'SURGE',
        last_month_qty: lastMonth,
        hist_avg: histAvg,
        ratio: lastMonth / histAvg,
        recommendation_en: 'Check if this is a new demand trend. Update ROP if confirmed.',
        recommendation_no: 'Sjekk om dette er en ny etterspørselstrend. Oppdater ROP ved behov.',
        recommendation_pl: 'Sprawdź czy to nowy trend. Zaktualizuj ROP jeśli potwierdzony.',
      })
    } else if (histAvg > 1 && lastMonth === 0) {
      anomalies.push({
        material_number: mat,
        type: 'DROP',
        last_month_qty: 0,
        hist_avg: histAvg,
        recommendation_en: 'No movement last month. Check if part is discontinued or order error.',
        recommendation_no: 'Ingen bevegelse forrige måned. Sjekk om del er utgått eller feil.',
        recommendation_pl: 'Brak ruchu w ostatnim miesiącu. Czy część wycofana lub błąd zamówienia?',
      })
    }
  }

  return anomalies
}
