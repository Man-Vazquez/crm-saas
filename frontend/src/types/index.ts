// ─────────────────────────────────────────────────────────────────────────────
// Auto-generated source: run `npm run gen:types` to refresh from the backend.
// Do NOT edit types derived from components['schemas'] by hand — change the
// backend schema and regenerate instead.
// ─────────────────────────────────────────────────────────────────────────────

import type { components } from './api'

// ── Core domain types ────────────────────────────────────────────────────────

export type Ticket        = components['schemas']['TicketResponse'] & {
  ticket_number: number | null
  updated_by: string | null
  last_activity: string | null
}
export type Customer      = components['schemas']['CustomerResponse']
export type Message       = components['schemas']['MessageResponse']
export type Channel       = components['schemas']['ChannelResponse'] & {
  department_id: string | null
}
export type Tenant        = components['schemas']['TenantResponse']

// ── Auth / users ─────────────────────────────────────────────────────────────

export type User      = components['schemas']['UserMe']       // GET /auth/me
export type AdminUser = components['schemas']['UserResponse'] // GET /admin/users

// ── Ticket configuration ──────────────────────────────────────────────────────

export type TicketStatus  = components['schemas']['TicketStatusResponse']
export type TicketType    = components['schemas']['TicketTypeResponse']
export type TicketSubtype = components['schemas']['TicketSubtypeResponse']

// ── Metrics ───────────────────────────────────────────────────────────────────

export type DashboardSummary      = components['schemas']['DashboardSummary']
export type TicketsByStatusItem   = components['schemas']['TicketsByStatusItem']
export type TicketsByPriorityItem = components['schemas']['TicketsByPriorityItem']
export type TicketsByChannelItem  = components['schemas']['TicketsByChannelItem']
export type TicketsByAgentItem    = components['schemas']['TicketsByAgentItem']
export type TicketsByTypeItem     = components['schemas']['TicketsByTypeItem']
export type DailyTicketsItem      = components['schemas']['DailyTicketsItem']

// ── Departments ───────────────────────────────────────────────────────────────

export interface Department {
  id: string
  name: string
  description: string | null
  is_active: boolean
  agent_count: number
  channel_count: number
  created_at: string
}

export interface DepartmentAgent {
  id: string
  full_name: string
  email: string
  role: string
}

// ── Generic pagination wrapper ────────────────────────────────────────────────
// Not in the OpenAPI schema (the backend uses inline dict returns), so it stays
// hand-written here.

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}
