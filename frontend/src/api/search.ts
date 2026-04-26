import client from './client'

export interface SearchTicketResult {
  id: string
  ticket_number: number
  subject: string
  status: string
  priority: string
  channel: string
  customer_name: string
}

export interface SearchCustomerResult {
  id: string
  name: string
  email: string
  company: string
}

export interface SearchMessageResult {
  id: string
  ticket_id: string
  ticket_number: number
  ticket_subject: string
  body_snippet: string
}

export interface SearchResponse {
  query: string
  tickets: SearchTicketResult[]
  customers: SearchCustomerResult[]
  messages: SearchMessageResult[]
  total: number
}

export async function globalSearch(q: string, limit = 5): Promise<SearchResponse> {
  const { data } = await client.get<SearchResponse>('/search', { params: { q, limit } })
  return data
}
