/* ─────────────────────────────────────────────────────────
   Auth slice — FE-005
   State: { user, accessToken, isAuthenticated, loading }
   Actions: setCredentials, clearCredentials, setLoading
───────────────────────────────────────────────────────── */
import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import type { User } from '@/types'

interface AuthState {
  user:            User | null
  accessToken:     string | null
  isAuthenticated: boolean
  loading:         boolean
}

const initialState: AuthState = {
  user:            null,
  accessToken:     null,
  isAuthenticated: false,
  loading:         true,   // true until session-restore attempt completes
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials: (
      state,
      action: PayloadAction<{ user: User; accessToken: string }>,
    ) => {
      state.user            = action.payload.user
      state.accessToken     = action.payload.accessToken
      state.isAuthenticated = true
      state.loading         = false
    },
    clearCredentials: (state) => {
      state.user            = null
      state.accessToken     = null
      state.isAuthenticated = false
      state.loading         = false
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
  },
})

export const { setCredentials, clearCredentials, setLoading } = authSlice.actions
export default authSlice.reducer
