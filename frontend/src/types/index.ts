/* ─────────────────────────────────────────────────────────
   Shared domain types used across the application.
   Kept in sync with backend Pydantic schemas.
───────────────────────────────────────────────────────── */

// ── Auth ──────────────────────────────────────────────────
export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
}

export interface User {
  id: string
  email: string
  full_name: string
  created_at: string
}

// ── Projects ──────────────────────────────────────────────
export interface Project {
  id: string
  name: string
  key: string
  description: string | null
  owner_id: string
  created_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}

// ── Tickets ──────────────────────────────────────────────
export type TicketType     = 'BUG' | 'STORY' | 'TASK' | 'EPIC'
export type TicketPriority = 'BLOCKER' | 'HIGH' | 'MEDIUM' | 'LOW'
export type TicketStatus   = 'TODO' | 'IN_PROGRESS' | 'IN_REVIEW' | 'DONE'

export interface Ticket {
  id: string
  key: string
  ticket_number: number
  title: string
  description: string | null
  ticket_type: TicketType
  priority: TicketPriority
  status: TicketStatus
  story_points: number | null
  project_id: string
  reporter_id: string
  assignee_id: string | null
  created_at: string
}
