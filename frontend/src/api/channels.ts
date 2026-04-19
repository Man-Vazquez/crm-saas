import client from './client'
import type { Channel } from '../types'

export const getChannels = async () => {
  const { data } = await client.get<Channel[]>('/channels')
  return data
}

export const createChannel = (data: {
  channel_type: string
  name: string
  config: Record<string, string>
}) => client.post<Channel>('/channels', data).then(r => r.data)
