import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export async function GET() {
  try {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

    const { data: profile } = await supabase.from('profiles').select('organization_id').eq('id', user.id).single()

    if (!profile?.organization_id) {
      return NextResponse.json({ results: [] })
    }

    const { data, error } = await supabase.from('rop_results').select('*').eq('organization_id', profile.organization_id).order('status', { ascending: true })
    if (error) throw new Error(error.message)

    return NextResponse.json({ results: data || [] })
  } catch (e: unknown) {
    return NextResponse.json({ error: e instanceof Error ? e.message : 'Failed to fetch' }, { status: 500 })
  }
}
