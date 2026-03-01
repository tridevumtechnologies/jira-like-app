/* ─────────────────────────────────────────────────────────
   PublicLayout — wraps unauthenticated pages (login / register)
   Simple centered card layout.
───────────────────────────────────────────────────────── */
import { Outlet, Navigate } from 'react-router-dom'
import { useAppSelector } from '@/hooks/useAppSelector'

export default function PublicLayout() {
  const { isAuthenticated, loading } = useAppSelector((s) => s.auth)

  // While session-restore is in flight, show nothing to avoid flash
  if (loading) return null

  // Already authenticated → send to app
  if (isAuthenticated) return <Navigate to="/projects" replace />

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* App brand */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-primary-600 tracking-tight">
            Jira-Like
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Project &amp; ticket management
          </p>
        </div>

        {/* Page content */}
        <div className="bg-white rounded-2xl shadow-md p-8">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
