import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export async function POST(req: NextRequest) {
  try {
    const { user_id, org_name, full_name } = await req.json()

    if (!user_id) {
      return NextResponse.json({ error: 'Missing user_id' }, { status: 400 })
    }

    const supabase = await createClient()

    const slug = (org_name || 'my-org').toLowerCase().replace(/[^a-z0-9]/g, '-').replace(/-+/g, '-').slice(0, 30) + '-' + Math.random().toString(36).slice(2, 6)

    const { data: org, error: orgError } = await supabase.from('organizations').insert({ name: org_name || 'My Organization', slug, plan: 'free' }).select().single()
    if (orgError) throw new Error(orgError.message)

    const { error: profileError } = await supabase.from('profiles').insert({ id: user_id, organization_id: org.id, full_name: full_name || 'User', role: 'owner', lang: 'EN' })
    if (profileError) throw new Error(profileError.message)

    return NextResponse.json({ ok: true, organization_id: org.id })
  } catch (e: unknown) {
    console.error('Setup org error:', e)
    return NextResponse.json({ error: e instanceof Error ? e.message : 'Setup failed' }, { status: 500 })
  }
}
