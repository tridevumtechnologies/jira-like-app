/* ─────────────────────────────────────────────────────────
   App root — FE-003 + FE-006
   Wraps the RouterProvider; session-restore happens here.
───────────────────────────────────────────────────────── */
import { useEffect } from 'react'
import { RouterProvider } from 'react-router-dom'
import { router }        from '@/router'
import { useAppDispatch } from '@/hooks/useAppDispatch'
import { setCredentials, clearCredentials } from '@/store/slices/authSlice'
import apiClient from '@/api/client'
import type { TokenResponse, User } from '@/types'

/**
 * On first mount, attempt to restore the session via the HttpOnly
 * refresh-token cookie (FE-103 requirement).
 * Dispatches setCredentials on success or clearCredentials on failure.
 */
function SessionRestore() {
  const dispatch = useAppDispatch()

  useEffect(() => {
    const restore = async () => {
      try {
        const { data: tokenData } = await apiClient.post<TokenResponse>(
          '/api/v1/auth/refresh',
        )
        const { data: user } = await apiClient.get<User>('/api/v1/users/me', {
          headers: { Authorization: `Bearer ${tokenData.access_token}` },
        })
        dispatch(setCredentials({ user, accessToken: tokenData.access_token }))
      } catch {
        dispatch(clearCredentials())
      }
    }

    void restore()
  }, [dispatch])

  return null
}

export default function App() {
  return (
    <>
      <SessionRestore />
      <RouterProvider router={router} />
    </>
  )
}
