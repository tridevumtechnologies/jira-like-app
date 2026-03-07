/* ─────────────────────────────────────────────────────────
   Auth API helpers — FE-101 / FE-102

   Thin wrappers around apiClient so pages stay clean.
───────────────────────────────────────────────────────── */
import apiClient from './client'
import type { TokenResponse, User } from '@/types'

// ── Request payloads ──────────────────────────────────────

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  full_name: string
  email: string
  password: string
}

// ── API calls ─────────────────────────────────────────────

export async function loginUser(data: LoginRequest): Promise<TokenResponse> {
  const res = await apiClient.post<TokenResponse>('/api/v1/auth/login', data)
  return res.data
}

export async function registerUser(data: RegisterRequest): Promise<TokenResponse> {
  const res = await apiClient.post<TokenResponse>('/api/v1/auth/register', data)
  return res.data
}

/**
 * Fetch the current user profile using a freshly issued access token.
 * Pass the token explicitly to avoid a race with the Redux store update.
 */
export async function fetchCurrentUser(accessToken: string): Promise<User> {
  const res = await apiClient.get<User>('/api/v1/users/me', {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  return res.data
}
