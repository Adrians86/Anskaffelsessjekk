import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { computeRop } from '@/lib/rop-engine'
import type { MappedRow } from '@/lib/file-parser'
import type { StockMovement } from '@/lib/types'

export async function POST(req: NextRequest) {
  try {
    const supabase = await createClient()
    const { data: { user }, error: authError } = await supabase.auth.getUser()
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const { data: profile } = await supabase.from('profiles').select('organization_id').eq('id', user.id).single()
    if (!profile?.organization_id) {
      return NextResponse.json({ error: 'No organization found' }, { status: 400 })
    }

    const orgId = profile.organization_id
    const { rows, mapping, filename } = await req.json() as { rows: MappedRow[]; mapping: Record<string, unknown>; filename: string }

    if (!rows?.length) {
      return NextResponse.json({ error: 'No rows to import' }, { status: 400 })
    }

    const materials = [...new Set(rows.map(r => r.material_number))].map(mat => {
      const row = rows.find(r => r.material_number === mat)!
      return {
        organization_id: orgId,
        material_number: mat,
        description: row.description || '',
        unit: row.unit || 'PC',
        standard_price: row.unit_price || 0,
        safety_stock: row.safety_stock || 0,
        storage_location: row.storage_location || '',
      }
    })

    await supabase.from('materials').upsert(materials, { onConflict: 'organization_id,material_number' })

    const hasMovements = rows.some(r => r.movement_type || r.date)
    let rowsImported = 0

    if (hasMovements) {
      const movements = rows.map(r => ({
        organization_id: orgId,
        material_number: r.material_number,
        posting_date: r.date || new Date().toISOString().slice(0, 10),
        quantity: r.quantity,
        movement_type: r.movement_type || '261',
        is_issue: r.is_issue,
        storage_location: r.storage_location || null,
      }))

      const { data: insertedMvt, error: mvtError } = await supabase.from('stock_movements').insert(movements).select('id')
      if (mvtError) throw new Error(mvtError.message)
      rowsImported = insertedMvt?.length || movements.length

      const allMovements = movements as StockMovement[]
      const ropResults = computeRop({
        movements: allMovements,
        currentStock: {},
        unitPrices: Object.fromEntries(rows.map(r => [r.material_number, r.unit_price || 0])),
        leadTimeDays: 14,
        serviceLevel: 0.95,
        organizationId: orgId,
        lang: 'EN',
      })

      if (ropResults.length) {
        await supabase.from('rop_results').delete().eq('organization_id', orgId)
        await supabase.from('rop_results').insert(ropResults.map(r => ({ ...r, computed_at: new Date().toISOString() })))
      }
    } else {
      const stockRows = rows.map(r => ({
        organization_id: orgId,
        material_number: r.material_number,
        quantity: r.quantity,
        open_orders: 0,
        snapshot_date: new Date().toISOString().slice(0, 10),
        updated_at: new Date().toISOString(),
      }))

      const { error: stockError } = await supabase.from('current_stock').upsert(stockRows, { onConflict: 'organization_id,material_number' })
      if (stockError) throw new Error(stockError.message)
      rowsImported = stockRows.length
    }

    await supabase.from('file_imports').insert({ organization_id: orgId, filename, import_type: hasMovements ? 'MB51' : 'MB52', rows_imported: rowsImported, mapping_profile: mapping, status: 'done' })

    return NextResponse.json({ rows_imported: rowsImported, status: 'ok' })
  } catch (e: unknown) {
    console.error('Import error:', e)
    return NextResponse.json({ error: e instanceof Error ? e.message : 'Import failed' }, { status: 500 })
  }
}
