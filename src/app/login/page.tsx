'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { Loader2 } from 'lucide-react'

export default function LoginPage() {
  const router = useRouter()
  const supabase = createClient()

  const [mode, setMode] = useState<'signin' | 'signup'>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [orgName, setOrgName] = useState('')
  const [fullName, setFullName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')

  const DEMO_EMAIL = 'demo@asnorth.no'
  const DEMO_PASSWORD = 'Demo12345!'

  const handleDemo = async () => {
    setMode('signin')
    setError('')
    setInfo('Logging in to demo account...')
    setLoading(true)

    try {
      const { error: signInError } = await supabase.auth.signInWithPassword({
        email: DEMO_EMAIL,
        password: DEMO_PASSWORD,
      })

      if (signInError) throw signInError
      router.push('/dashboard')
      router.refresh()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Something went wrong while signing in to demo')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setInfo('')
    setLoading(true)

    try {
      if (mode === 'signin') {
        const { error: signInError } = await supabase.auth.signInWithPassword({ email, password })
        if (signInError) throw signInError
        router.push('/dashboard')
        router.refresh()
      } else {
        const { data: signUpData, error: signUpError } = await supabase.auth.signUp({ email, password })
        if (signUpError) throw signUpError
        if (!signUpData.user) throw new Error('No user returned')

        const res = await fetch('/api/setup-org', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: signUpData.user.id,
            org_name: orgName || 'My Organization',
            full_name: fullName || email.split('@')[0],
          }),
        })

        if (!res.ok) {
          const d = await res.json()
          throw new Error(d.error || 'Setup failed')
        }

        if (signUpData.session) {
          router.push('/dashboard')
          router.refresh()
        } else {
          setInfo('Check your email to confirm your account, then log in.')
        }
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0F1A2E] p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="text-4xl mb-3">⚙️</div>
          <h1 className="text-2xl font-bold text-[#C9A84C] tracking-tight">SpareParts AI</h1>
          <p className="text-sm text-[#8899BB] mt-1">AS North Advisory · asnorth.no</p>
        </div>

        <div className="card-dark p-8">
          <div className="flex gap-1 mb-6 bg-[#0F1A2E] p-1 rounded-lg">
            <button
              onClick={() => setMode('signin')}
              className={`flex-1 py-2 text-sm font-medium rounded transition-colors ${mode === 'signin' ? 'bg-[#C9A84C] text-[#0F1A2E]' : 'text-[#8899BB]'}`}
            >
              Sign In
            </button>
            <button
              onClick={() => setMode('signup')}
              className={`flex-1 py-2 text-sm font-medium rounded transition-colors ${mode === 'signup' ? 'bg-[#C9A84C] text-[#0F1A2E]' : 'text-[#8899BB]'}`}
            >
              Sign Up
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'signup' && (
              <>
                <div>
                  <label className="text-xs font-semibold text-[#8899BB] uppercase tracking-wider block mb-2">Full Name</label>
                  <input type="text" value={fullName} onChange={e => setFullName(e.target.value)} placeholder="Adrian Śliwa" className="w-full bg-[#0F1A2E] border border-[#2A4A7A] rounded-lg px-4 py-2.5 text-[#E8EDF5] text-sm focus:border-[#C9A84C] focus:outline-none" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-[#8899BB] uppercase tracking-wider block mb-2">Organization Name</label>
                  <input type="text" value={orgName} onChange={e => setOrgName(e.target.value)} placeholder="AS North Advisory" className="w-full bg-[#0F1A2E] border border-[#2A4A7A] rounded-lg px-4 py-2.5 text-[#E8EDF5] text-sm focus:border-[#C9A84C] focus:outline-none" />
                </div>
              </>
            )}

            <div>
              <label className="text-xs font-semibold text-[#8899BB] uppercase tracking-wider block mb-2">Email</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="adrian@asnorth.no" className="w-full bg-[#0F1A2E] border border-[#2A4A7A] rounded-lg px-4 py-2.5 text-[#E8EDF5] text-sm focus:border-[#C9A84C] focus:outline-none" />
            </div>

            <div>
              <label className="text-xs font-semibold text-[#8899BB] uppercase tracking-wider block mb-2">Password</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} required minLength={6} placeholder="At least 6 characters" className="w-full bg-[#0F1A2E] border border-[#2A4A7A] rounded-lg px-4 py-2.5 text-[#E8EDF5] text-sm focus:border-[#C9A84C] focus:outline-none" />
            </div>

            {error && <div className="bg-red-500/10 border border-red-500/40 rounded-lg p-3 text-red-300 text-sm">{error}</div>}
            {info && <div className="bg-green-500/10 border border-green-500/40 rounded-lg p-3 text-green-300 text-sm">{info}</div>}

            <button type="submit" disabled={loading} className="w-full btn-primary flex items-center justify-center gap-2 py-3 disabled:opacity-50">
              {loading && <Loader2 size={16} className="animate-spin" />}
              {mode === 'signin' ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          <div className="mt-6 border-t border-[#2A4A7A] pt-5 text-sm text-[#8899BB]">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <span className="inline-flex items-center rounded-full bg-[#D9B24A]/15 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-[#D9B24A]">
                DEMO — syntetiske data
              </span>
              <button type="button" onClick={handleDemo} className="btn-secondary w-full sm:w-auto">
                Prøv demo / Try demo
              </button>
            </div>
            <p className="mt-3 text-xs text-[#8899BB] leading-5">
              Dostęp do konta demo (read-only) dla rekrutera lub klienta. Synthetic data only, zero changes to live tenant.
            </p>
          </div>
        </div>

        <p className="text-center text-xs text-[#8899BB] mt-6">Multi-tenant · Row-Level Security · Data isolated per organization</p>
      </div>
    </div>
  )
}
