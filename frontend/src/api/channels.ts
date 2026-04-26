import client from './client'
import type { Channel, PaginatedResponse } from '../types'

export const getChannels = (skip = 0, limit = 20) =>
  client.get<PaginatedResponse<Channel>>('/channels', { params: { skip, limit } }).then(r => r.data)

export const createChannel = (data: {
  channel_type: string
  name: string
  config: Record<string, string>
  department_id?: string | null
}) => client.post<Channel>('/channels', data).then(r => r.data)

export const updateChannel = (id: string, data: {
  config?: Record<string, string>
  is_active?: boolean
  department_id?: string | null
  agent_id?: string | null
}) => client.patch<Channel>(`/channels/${id}`, data).then(r => r.data)
