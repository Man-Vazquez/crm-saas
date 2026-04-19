export interface Tenant {
  id: string
  name: string
  slug: string
  plan: string
  is_active: boolean
}

export interface AdminUser {
  id: string
  email: string
  full_name: string
  role: 'admin' | 'supervisor' | 'agent'
  is_active: boolean
}

export interface DashboardSummary {
  total_open: number
  total_in_progress: number
  total_resolved: number
  total_closed: number
  avg_resolution_hours: number | null
}

export interface TicketsByStatusItem {
  status_name: string
  color: string
  count: number
}

export interface TicketsByPriorityItem {
  priority: string
  count: number
}

export interface TicketsByChannelItem {
  channel: string
  count: number
}

export interface TicketsByAgentItem {
  agent_name: string
  total: number
  open: number
  resolved: number
}

export interface TicketsByTypeItem {
  type_name: string
  subtype_name: string | null
  count: number
}

export interface DailyTicketsItem {
  date: string
  count: number
}

export interface User {
  id: string
  tenant_id: string
  email: string
  full_name: string
  role: 'admin' | 'supervisor' | 'agent'
  is_active: boolean
}

export interface Customer {
  id: string
  tenant_id: string
  full_name: string
  email: string | null
  phone: string | null
  company: string | null
  notes: string | null
  custom_fields: Record<string, unknown>
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TicketStatus {
  id: string
  tenant_id: string
  name: string
  color: string
  sort_order: number
  is_default: boolean
  is_active: boolean
}

export interface TicketType {
  id: string
  tenant_id: string
  name: string
  description: string | null
  is_active: boolean
}

export interface TicketSubtype {
  id: string
  tenant_id: string
  type_id: string
  name: string
  is_active: boolean
}

export interface Ticket {
  id: string
  tenant_id: string
  customer_id: string
  assigned_to: string | null
  status_id: string
  type_id: string | null
  subtype_id: string | null
  subject: string
  channel: string
  channel_id: string | null
  priority: 'low' | 'medium' | 'high' | 'urgent'
  is_active: boolean
  resolved_at: string | null
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  tenant_id: string
  ticket_id: string
  author_id: string | null
  body: string
  direction: 'inbound' | 'outbound'
  msg_type: 'reply' | 'comment'
  metadata_: Record<string, unknown>
  created_at: string
}

export interface Channel {
  id: string
  tenant_id: string
  channel_type: string
  name: string
  is_active: boolean
  created_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}