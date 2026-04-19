import client from './client'
import type { User } from '../types'

interface LoginResponse {
  access_token: string
  refresh_token: string
  user: User
}

export const login = async (email: string, password: string): Promise<LoginResponse> => {
  const { data } = await client.post<LoginResponse>('/auth/login', { email, password })
  return data
}

export const getMe = async (): Promise<User> => {
  const { data } = await client.get<User>('/auth/me')
  return data
}

export const refreshTokens = async (refreshToken: string) => {
  const { data } = await client.post<{ access_token: string; refresh_token: string }>(
    '/auth/refresh',
    { refresh_token: refreshToken }
  )
  return data
}