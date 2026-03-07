/* ─────────────────────────────────────────────────────────
   LoginPage — FE-101

   • Form: email + password with client-side validation
   • Calls POST /api/v1/auth/login → stores token in Redux
   • Redirect to /projects on success
   • Inline error message on 401 / other failures
   • Link to /register
───────────────────────────────────────────────────────── */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAppDispatch } from '@/hooks/useAppDispatch'
import { setCredentials } from '@/store/slices/authSlice'
import { loginUser, fetchCurrentUser } from '@/api/auth'

// ── Types ─────────────────────────────────────────────────

interface FormState {
  email:    string
  password: string
}

interface FormErrors {
  email?:    string
  password?: string
}

// ── Component ─────────────────────────────────────────────

export default function LoginPage() {
  const dispatch  = useAppDispatch()
  const navigate  = useNavigate()

  const [form, setForm]         = useState<FormState>({ email: '', password: '' })
  const [errors, setErrors]     = useState<FormErrors>({})
  const [apiError, setApiError] = useState<string | null>(null)
  const [loading, setLoading]   = useState(false)

  // ── Validation ───────────────────────────────────────────

  function validate(): boolean {
    const next: FormErrors = {}

    if (!form.email.trim()) {
      next.email = 'Email is required.'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      next.email = 'Enter a valid email address.'
    }

    if (!form.password) {
      next.password = 'Password is required.'
    }

    setErrors(next)
    return Object.keys(next).length === 0
  }

  // ── Submit ───────────────────────────────────────────────

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setApiError(null)

    if (!validate()) return

    setLoading(true)
    try {
      const tokenData = await loginUser({ email: form.email, password: form.password })
      const user      = await fetchCurrentUser(tokenData.access_token)
      dispatch(setCredentials({ user, accessToken: tokenData.access_token }))
      navigate('/projects', { replace: true })
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 401) {
        setApiError('Invalid email or password.')
      } else {
        setApiError('Something went wrong. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  // ── Helpers ──────────────────────────────────────────────

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
    // Clear field error on change
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }))
    }
  }

  // ── Render ───────────────────────────────────────────────

  return (
    <>
      <h2 className="text-xl font-semibold text-gray-800 mb-6">Sign in to your account</h2>

      {/* API-level error banner */}
      {apiError && (
        <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {apiError}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate className="space-y-5">
        {/* Email */}
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
            Email address
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            value={form.email}
            onChange={handleChange}
            className={`w-full rounded-lg border px-3 py-2 text-sm shadow-sm outline-none transition
              focus:ring-2 focus:ring-primary-500 focus:border-primary-500
              ${errors.email ? 'border-red-400 bg-red-50' : 'border-gray-300 bg-white'}`}
            placeholder="you@example.com"
          />
          {errors.email && (
            <p className="mt-1 text-xs text-red-600">{errors.email}</p>
          )}
        </div>

        {/* Password */}
        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
            Password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            value={form.password}
            onChange={handleChange}
            className={`w-full rounded-lg border px-3 py-2 text-sm shadow-sm outline-none transition
              focus:ring-2 focus:ring-primary-500 focus:border-primary-500
              ${errors.password ? 'border-red-400 bg-red-50' : 'border-gray-300 bg-white'}`}
            placeholder="••••••••"
          />
          {errors.password && (
            <p className="mt-1 text-xs text-red-600">{errors.password}</p>
          )}
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white
            hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1
            disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Signing in…
            </span>
          ) : (
            'Sign in'
          )}
        </button>
      </form>

      {/* Register link */}
      <p className="mt-6 text-center text-sm text-gray-500">
        Don&apos;t have an account?{' '}
        <Link
          to="/register"
          className="font-medium text-primary-600 hover:text-primary-700 transition-colors"
        >
          Create one
        </Link>
      </p>
    </>
  )
}
