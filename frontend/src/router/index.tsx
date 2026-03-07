/* ─────────────────────────────────────────────────────────
   React Router v6 route definitions — FE-003

   Public routes  (no auth required): /login, /register
   Protected routes (auth required):  /projects, /projects/:id, /tickets/:id
───────────────────────────────────────────────────────── */
import { createBrowserRouter } from 'react-router-dom'

import PublicLayout    from '@/layouts/PublicLayout'
import AppLayout       from '@/layouts/AppLayout'
import ProtectedRoute  from '@/components/auth/ProtectedRoute'
import LoginPage       from '@/pages/auth/LoginPage'
import RegisterPage    from '@/pages/auth/RegisterPage'

// Placeholder for pages not yet implemented
const ComingSoon = ({ label }: { label: string }) => (
  <div className="flex h-full items-center justify-center text-gray-400 text-lg">
    {label} — coming soon
  </div>
)

export const router = createBrowserRouter([
  // ── Public (unauthenticated) ──────────────────────────
  {
    element: <PublicLayout />,
    children: [
      { path: '/login',    element: <LoginPage /> },
      { path: '/register', element: <RegisterPage /> },
    ],
  },

  // ── Protected (authenticated) ─────────────────────────
  {
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true,                              element: <ComingSoon label="Dashboard" /> },
      { path: '/projects',                        element: <ComingSoon label="Projects" /> },
      { path: '/projects/:projectId',             element: <ComingSoon label="Project Detail" /> },
      { path: '/projects/:projectId/tickets',     element: <ComingSoon label="Tickets" /> },
      { path: '/tickets/:ticketId',               element: <ComingSoon label="Ticket Detail" /> },
    ],
  },
])
