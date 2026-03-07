/* ─────────────────────────────────────────────────────────
   App root — FE-003 + FE-006
   Wraps the RouterProvider; session-restore happens here.
───────────────────────────────────────────────────────── */
import { useEffect } from 'react'
import { RouterProvider } from 'react-router-dom'
import axios from 'axios'
import { router }        from '@/router'
import { useAppDispatch } from '@/hooks/useAppDispatch'
import { setCredentials, clearCredentials } from '@/store/slices/authSlice'
import apiClient from '@/api/client'
import type { TokenResponse, User } from '@/types'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

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
        // Use a plain axios instance (no interceptors) so that a 401 here
        // does NOT trigger the apiClient response interceptor, which would
        // attempt another refresh and cause an infinite loop.
        const { data: tokenData } = await axios.post<TokenResponse>(
          `${BASE_URL}/api/v1/auth/refresh`,
          {},
          { withCredentials: true },
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
