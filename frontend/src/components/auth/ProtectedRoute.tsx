/* ─────────────────────────────────────────────────────────
   ProtectedRoute — FE-003 / FE-104
   Guards any route that requires the user to be authenticated.

   Behaviour:
   • While session-restore (loading=true) → render nothing (prevents flash)
   • Not authenticated → redirect to /login (replace so Back button works)
   • Authenticated → render children
───────────────────────────────────────────────────────── */
import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAppSelector } from '@/hooks/useAppSelector'

interface Props {
  children: ReactNode
}

export default function ProtectedRoute({ children }: Props) {
  const { isAuthenticated, loading } = useAppSelector((s) => s.auth)

  if (loading) {
    // Session-restore in progress — show a full-screen spinner
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
