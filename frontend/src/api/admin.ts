import client from './client'
import type { AdminUser, PaginatedResponse, Tenant } from '../types'

export const getAdminUsers = (skip = 0, limit = 20) =>
  client.get<PaginatedResponse<AdminUser>>('/admin/users', { params: { skip, limit } }).then(r => r.data)

export const createAdminUser = (data: {
  email: string
  full_name: string
  password: string
  role: string
}) => client.post<AdminUser>('/admin/users', data).then(r => r.data)

export const updateAdminUser = (id: string, data: {
  full_name?: string
  role?: string
  is_active?: boolean
}) => client.patch<AdminUser>(`/admin/users/${id}`, data).then(r => r.data)

export const deleteAdminUser = (id: string) =>
  client.delete(`/admin/users/${id}`)

export const getAdminTenant = () =>
  client.get<Tenant>('/admin/tenant').then(r => r.data)

export const updateAdminTenant = (data: { name: string }) =>
  client.patch<Tenant>('/admin/tenant', data).then(r => r.data)
