/* ─────────────────────────────────────────────────────────
   AppLayout — FE-105 shell (Sprint 1)
   • Top navbar: logo + user avatar + logout
   • Left sidebar: navigation links
   • Main <Outlet /> content area
   Actual Sprint 1 content will be filled in FE-105.
   This file provides the structural skeleton so routing works today.
───────────────────────────────────────────────────────── */
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAppSelector }  from '@/hooks/useAppSelector'
import { useAppDispatch }  from '@/hooks/useAppDispatch'
import { clearCredentials } from '@/store/slices/authSlice'
import apiClient from '@/api/client'

export default function AppLayout() {
  const dispatch  = useAppDispatch()
  const navigate  = useNavigate()
  const { user }  = useAppSelector((s) => s.auth)

  const handleLogout = async () => {
    try {
      await apiClient.post('/api/v1/auth/logout')
    } catch {
      // best-effort
    }
    dispatch(clearCredentials())
    navigate('/login', { replace: true })
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-100">
      {/* ── Sidebar ─────────────────────────────────────── */}
      <aside className="w-56 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col">
        {/* Logo */}
        <div className="h-14 flex items-center px-5 border-b border-gray-200">
          <span className="text-lg font-bold text-primary-600 tracking-tight">
            Jira-Like
          </span>
        </div>

        {/* Nav links */}
        <nav className="flex-1 overflow-y-auto p-3 space-y-1">
          <SidebarLink to="/projects" label="Projects" />
        </nav>
      </aside>

      {/* ── Main area ───────────────────────────────────── */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top navbar */}
        <header className="h-14 flex-shrink-0 bg-white border-b border-gray-200 flex items-center justify-between px-6">
          <div /> {/* Left slot — breadcrumbs will go here */}

          {/* User menu */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-primary-500 flex items-center justify-center text-white text-sm font-semibold select-none">
              {user?.full_name?.[0]?.toUpperCase() ?? '?'}
            </div>
            <span className="text-sm text-gray-700 hidden sm:block">
              {user?.full_name}
            </span>
            <button
              onClick={handleLogout}
              className="text-sm text-gray-500 hover:text-red-500 transition-colors"
            >
              Logout
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

// ── helpers ────────────────────────────────────────────────
function SidebarLink({ to, label }: { to: string; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        [
          'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
          isActive
            ? 'bg-primary-50 text-primary-700'
            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
        ].join(' ')
      }
    >
      {label}
    </NavLink>
  )
}
