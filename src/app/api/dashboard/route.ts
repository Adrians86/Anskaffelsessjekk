import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export async function GET() {
  try {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

    const { data: profile } = await supabase.from('profiles').select('organization_id').eq('id', user.id).single()
    const orgId = profile?.organization_id

    const empty = {
      total_materials: 0, critical_count: 0, watch_count: 0, ok_count: 0,
      rop_total: 0, frozen_capital_nok: 0, active_promotions: 0, last_import: null,
    }
    if (!orgId) return NextResponse.json({ stats: empty })

    const { count: matCount } = await supabase
      .from('materials').select('*', { count: 'exact', head: true })
      .eq('organization_id', orgId)

    const { data: rop } = await supabase
      .from('rop_results').select('status').eq('organization_id', orgId)
    let critical = 0, watch = 0, ok = 0
    for (const r of rop || []) {
      if (r.status === 'OUT' || r.status === 'ORDER') critical++
      else if (r.status === 'WATCH') watch++
      else if (r.status === 'OK' || r.status === 'OVERSTOCK') ok++
    }

    // Frozen capital = sum(current_stock.quantity * materials.standard_price)
    const { data: stock } = await supabase
      .from('current_stock').select('material_number, quantity').eq('organization_id', orgId)
    let frozen = 0
    if (stock && stock.length) {
      const { data: mats } = await supabase
        .from('materials').select('material_number, standard_price').eq('organization_id', orgId)
      const priceMap: Record<string, number> = {}
      for (const m of mats || []) priceMap[m.material_number] = Number(m.standard_price) || 0
      for (const s of stock) frozen += (Number(s.quantity) || 0) * (priceMap[s.material_number] || 0)
    }

    const { data: imp } = await supabase
      .from('file_imports').select('imported_at').eq('organization_id', orgId)
      .order('imported_at', { ascending: false }).limit(1)
    const lastImport = imp && imp.length ? String(imp[0].imported_at).slice(0, 10) : null

    return NextResponse.json({
      stats: {
        total_materials: matCount || 0,
        critical_count: critical,
        watch_count: watch,
        ok_count: ok,
        rop_total: critical + watch + ok,
        frozen_capital_nok: Math.round(frozen),
        active_promotions: 0,
        last_import: lastImport,
      },
    })
  } catch (e: unknown) {
    return NextResponse.json({ error: e instanceof Error ? e.message : 'Failed to fetch' }, { status: 500 })
  }
}
