import client from './client'
import type { Department, DepartmentAgent } from '../types'

export const getDepartments = (): Promise<Department[]> =>
  client.get<Department[]>('/departments').then(r => r.data)

export const createDepartment = (data: { name: string; description?: string | null }): Promise<Department> =>
  client.post<Department>('/departments', data).then(r => r.data)

export const updateDepartment = (
  id: string,
  data: { name?: string; description?: string | null; is_active?: boolean },
): Promise<Department> =>
  client.patch<Department>(`/departments/${id}`, data).then(r => r.data)

export const deleteDepartment = (id: string): Promise<void> =>
  client.delete(`/departments/${id}`).then(() => undefined)

export const getDepartmentAgents = (id: string): Promise<DepartmentAgent[]> =>
  client.get<DepartmentAgent[]>(`/departments/${id}/agents`).then(r => r.data)

export const addDepartmentAgent = (id: string, user_id: string): Promise<void> =>
  client.post(`/departments/${id}/agents`, { user_id }).then(() => undefined)

export const removeDepartmentAgent = (id: string, user_id: string): Promise<void> =>
  client.delete(`/departments/${id}/agents/${user_id}`).then(() => undefined)
