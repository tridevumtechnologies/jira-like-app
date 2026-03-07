/* ─────────────────────────────────────────────────────────
   RegisterPage — FE-102

   • Form: full name, email, password, confirm password
   • Client-side validation before submit
   • Calls POST /api/v1/auth/register → auto-login → /projects
   • Inline error messages per field + API-level error banner
   • Link back to /login
───────────────────────────────────────────────────────── */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAppDispatch } from '@/hooks/useAppDispatch'
import { setCredentials } from '@/store/slices/authSlice'
import { registerUser, fetchCurrentUser } from '@/api/auth'

// ── Types ─────────────────────────────────────────────────

interface FormState {
  full_name:        string
  email:            string
  password:         string
  confirm_password: string
}

interface FormErrors {
  full_name?:        string
  email?:            string
  password?:         string
  confirm_password?: string
}

// ── Field sub-component (defined OUTSIDE RegisterPage to prevent remount) ──

interface FieldProps {
  id:            keyof FormState
  label:         string
  type?:         string
  placeholder?:  string
  autoComplete?: string
  error?:        string
  value:         string
  onChange:      (e: React.ChangeEvent<HTMLInputElement>) => void
}

function Field({ id, label, type = 'text', placeholder, autoComplete, error, value, onChange }: FieldProps) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <input
        id={id}
        name={id}
        type={type}
        autoComplete={autoComplete}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className={`w-full rounded-lg border px-3 py-2 text-sm shadow-sm outline-none transition
          focus:ring-2 focus:ring-primary-500 focus:border-primary-500
          ${error ? 'border-red-400 bg-red-50' : 'border-gray-300 bg-white'}`}
      />
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  )
}

// ── Component ─────────────────────────────────────────────

export default function RegisterPage() {
  const dispatch  = useAppDispatch()
  const navigate  = useNavigate()

  const [form, setForm] = useState<FormState>({
    full_name:        '',
    email:            '',
    password:         '',
    confirm_password: '',
  })
  const [errors, setErrors]     = useState<FormErrors>({})
  const [apiError, setApiError] = useState<string | null>(null)
  const [loading, setLoading]   = useState(false)

  // ── Validation ───────────────────────────────────────────

  function validate(): boolean {
    const next: FormErrors = {}

    if (!form.full_name.trim()) {
      next.full_name = 'Full name is required.'
    } else if (form.full_name.trim().length < 2) {
      next.full_name = 'Full name must be at least 2 characters.'
    }

    if (!form.email.trim()) {
      next.email = 'Email is required.'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      next.email = 'Enter a valid email address.'
    }

    if (!form.password) {
      next.password = 'Password is required.'
    } else if (form.password.length < 8) {
      next.password = 'Password must be at least 8 characters.'
    }

    if (!form.confirm_password) {
      next.confirm_password = 'Please confirm your password.'
    } else if (form.password !== form.confirm_password) {
      next.confirm_password = 'Passwords do not match.'
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
      const tokenData = await registerUser({
        full_name: form.full_name.trim(),
        email:     form.email.trim(),
        password:  form.password,
      })
      const user = await fetchCurrentUser(tokenData.access_token)
      dispatch(setCredentials({ user, accessToken: tokenData.access_token }))
      navigate('/projects', { replace: true })
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail

      if (status === 409 || (typeof detail === 'string' && detail.toLowerCase().includes('exist'))) {
        setApiError('An account with this email already exists.')
      } else if (status === 422) {
        setApiError('Please check your input and try again.')
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
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }))
    }
  }

  // ── Render ───────────────────────────────────────────────

  return (
    <>
      <h2 className="text-xl font-semibold text-gray-800 mb-6">Create your account</h2>

      {/* API-level error banner */}
      {apiError && (
        <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {apiError}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate className="space-y-5">
        <Field
          id="full_name"
          label="Full name"
          placeholder="Jane Smith"
          autoComplete="name"
          value={form.full_name}
          onChange={handleChange}
          error={errors.full_name}
        />
        <Field
          id="email"
          label="Email address"
          type="email"
          placeholder="you@example.com"
          autoComplete="email"
          value={form.email}
          onChange={handleChange}
          error={errors.email}
        />
        <Field
          id="password"
          label="Password"
          type="password"
          placeholder="Min. 8 characters"
          autoComplete="new-password"
          value={form.password}
          onChange={handleChange}
          error={errors.password}
        />
        <Field
          id="confirm_password"
          label="Confirm password"
          type="password"
          placeholder="Repeat your password"
          autoComplete="new-password"
          value={form.confirm_password}
          onChange={handleChange}
          error={errors.confirm_password}
        />

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
              Creating account…
            </span>
          ) : (
            'Create account'
          )}
        </button>
      </form>

      {/* Login link */}
      <p className="mt-6 text-center text-sm text-gray-500">
        Already have an account?{' '}
        <Link
          to="/login"
          className="font-medium text-primary-600 hover:text-primary-700 transition-colors"
        >
          Sign in
        </Link>
      </p>
    </>
  )
}
