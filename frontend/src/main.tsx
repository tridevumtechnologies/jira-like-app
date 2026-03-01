/* ─────────────────────────────────────────────────────────
   Application entry point — FE-001, FE-005, FE-006
   Providers:
     1. Redux store  (react-redux Provider)
     2. React Query  (QueryClientProvider)          — FE-006
     3. App          (session-restore + router)
───────────────────────────────────────────────────────── */
import { StrictMode } from 'react'
import { createRoot }  from 'react-dom/client'
import { Provider }    from 'react-redux'
import {
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

import { store } from '@/store'
import App       from '@/App'
import '@/index.css'

// ── React Query client — FE-006 ────────────────────────
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime:          1000 * 60 * 2,  // 2 min
      retry:              1,
      refetchOnWindowFocus: false,
    },
  },
})

// ── Mount ─────────────────────────────────────────────
const rootEl = document.getElementById('root')!

createRoot(rootEl).render(
  <StrictMode>
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <App />
        {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
      </QueryClientProvider>
    </Provider>
  </StrictMode>,
)
