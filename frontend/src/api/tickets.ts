import client from './client'
import type { Ticket, TicketStatus, TicketType, TicketSubtype, Message, PaginatedResponse } from '../types'

export const getTickets = async (params?: {
  skip?: number
  limit?: number
  status_id?: string
  priority?: string
  customer_id?: string
  department_id?: string
}) => {
  const { data } = await client.get<PaginatedResponse<Ticket>>('/tickets', { params })
  return data
}

export const getTicket = async (id: string) => {
  const { data } = await client.get<Ticket>(`/tickets/${id}`)
  return data
}

export const createTicket = async (payload: {
  subject: string
  customer_id: string
  status_id: string
  priority: string
  channel?: string
  channel_id?: string
  type_id?: string
  subtype_id?: string
  assigned_to?: string
}) => {
  const { data } = await client.post<Ticket>('/tickets', payload)
  return data
}

export const updateTicket = async (id: string, payload: Partial<Ticket>) => {
  const { data } = await client.patch<Ticket>(`/tickets/${id}`, payload)
  return data
}

export const getStatuses = async () => {
  const { data } = await client.get<TicketStatus[]>('/tickets/statuses')
  return data
}

export const getTypes = async () => {
  const { data } = await client.get<TicketType[]>('/tickets/types')
  return data
}

export const getSubtypes = async (typeId: string) => {
  const { data } = await client.get<TicketSubtype[]>(`/tickets/types/${typeId}/subtypes`)
  return data
}

export const replyTicket = async (ticketId: string, payload: {
  body: string
  msg_type: 'reply' | 'comment'
}) => {
  const { data } = await client.post<Message>(`/tickets/${ticketId}/reply`, payload)
  return data
}

export const getMessages = async (ticketId: string) => {
  const { data } = await client.get<Message[]>(`/tickets/${ticketId}/messages`)
  return data
}

export const createMessage = async (ticketId: string, payload: {
  body: string
  msg_type: 'reply' | 'comment'
}) => {
  const { data } = await client.post<Message>(`/tickets/${ticketId}/messages`, payload)
  return data
}

// ── Metrics ──────────────────────────────────────────────────────────────────

import type {
  DashboardSummary,
  TicketsByStatusItem,
  TicketsByPriorityItem,
  TicketsByChannelItem,
  TicketsByAgentItem,
  TicketsByTypeItem,
  DailyTicketsItem,
} from '../types'

export const getMetricsSummary = () =>
  client.get<DashboardSummary>('/metrics/summary').then(r => r.data)

export const getMetricsByStatus = () =>
  client.get<TicketsByStatusItem[]>('/metrics/by-status').then(r => r.data)

export const getMetricsByPriority = () =>
  client.get<TicketsByPriorityItem[]>('/metrics/by-priority').then(r => r.data)

export const getMetricsByChannel = () =>
  client.get<TicketsByChannelItem[]>('/metrics/by-channel').then(r => r.data)

export const getMetricsByAgent = () =>
  client.get<TicketsByAgentItem[]>('/metrics/by-agent').then(r => r.data)

export const getMetricsByType = () =>
  client.get<TicketsByTypeItem[]>('/metrics/by-type').then(r => r.data)

export const getMetricsDaily = () =>
  client.get<DailyTicketsItem[]>('/metrics/daily').then(r => r.data)