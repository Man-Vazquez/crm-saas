import client from './client'
import type { Customer, PaginatedResponse } from '../types'

export const getCustomers = async (params?: {
  skip?: number
  limit?: number
  search?: string
}) => {
  const { data } = await client.get<PaginatedResponse<Customer>>('/customers', { params })
  return data
}

export const getCustomer = async (id: string) => {
  const { data } = await client.get<Customer>(`/customers/${id}`)
  return data
}

export const createCustomer = async (payload: {
  full_name: string
  email?: string
  phone?: string
  company?: string
  notes?: string
}) => {
  const { data } = await client.post<Customer>('/customers', payload)
  return data
}