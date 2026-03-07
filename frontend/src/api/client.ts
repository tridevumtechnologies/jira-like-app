/* ─────────────────────────────────────────────────────────
   Axios HTTP client — FE-004

   Features:
   • Base URL from VITE_API_URL env var
   • Request interceptor: attaches Bearer token from Redux store
   • Response interceptor:
       - On 401 → attempt POST /api/v1/auth/refresh (cookie sent automatically)
       - If refresh succeeds → update store + retry original request once
       - If refresh fails → clear store + redirect to /login
───────────────────────────────────────────────────────── */
import axios, {
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from 'axios'
import { store } from '@/store'
import { setCredentials, clearCredentials } from '@/store/slices/authSlice'
import type { TokenResponse, User } from '@/types'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

const apiClient: AxiosInstance = axios.create({
  baseURL:         BASE_URL,
  withCredentials: true,           // send HttpOnly refresh token cookie automatically
  headers: { 'Content-Type': 'application/json' },
})

// ── Request interceptor — attach access token ────────────
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = store.getState().auth.accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Flag to prevent multiple concurrent refresh attempts ─
let _isRefreshing = false
let _refreshQueue: Array<(token: string) => void> = []

function _processQueue(newToken: string) {
  _refreshQueue.forEach((resolve) => resolve(newToken))
  _refreshQueue = []
}

// ── Response interceptor — handle 401 with token refresh ─
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retried?: boolean
    }

    // Never attempt a refresh retry for the refresh endpoint itself —
    // doing so creates an infinite loop (refresh fails → interceptor retries
    // refresh → fails again → interceptor retries … ).
    const isRefreshEndpoint = originalRequest.url?.includes('/auth/refresh')

    if (error.response?.status !== 401 || originalRequest._retried || isRefreshEndpoint) {
      return Promise.reject(error)
    }

    if (_isRefreshing) {
      // Queue the request until refresh completes
      return new Promise((resolve) => {
        _refreshQueue.push((token: string) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          resolve(apiClient(originalRequest))
        })
      })
    }

    originalRequest._retried = true
    _isRefreshing = true

    try {
      // Attempt token refresh — withCredentials sends the HttpOnly cookie
      const { data } = await axios.post<TokenResponse>(
        `${BASE_URL}/api/v1/auth/refresh`,
        {},
        { withCredentials: true },
      )
      const newAccessToken = data.access_token

      // Fetch fresh user profile and update the store
      const { data: user } = await axios.get<User>(
        `${BASE_URL}/api/v1/users/me`,
        { headers: { Authorization: `Bearer ${newAccessToken}` } },
      )
      store.dispatch(setCredentials({ user, accessToken: newAccessToken }))

      _processQueue(newAccessToken)
      originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
      return apiClient(originalRequest)
    } catch {
      // Dispatch clearCredentials so ProtectedRoute / PublicLayout redirect
      // the user via React Router — no hard page reload needed.
      store.dispatch(clearCredentials())
      return Promise.reject(error)
    } finally {
      _isRefreshing = false
    }
  },
)

export default apiClient
