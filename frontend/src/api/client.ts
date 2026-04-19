import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const client = axios.create({
  baseURL: '/api/v1',
})

client.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// --- Silent token refresh ---

type RefreshSubscriber = (token: string) => void
let isRefreshing = false
let subscribers: RefreshSubscriber[] = []

function enqueue(cb: RefreshSubscriber) {
  subscribers.push(cb)
}

function flushQueue(newToken: string) {
  subscribers.forEach((cb) => cb(newToken))
  subscribers = []
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    // No response at all → network/server unreachable
    if (!error.response) {
      const networkError = new Error(
        'Error de conexión. Verifica que el servidor esté corriendo.'
      )
      return Promise.reject(networkError)
    }

    const original = error.config

    if (error.response?.status !== 401) {
      return Promise.reject(error)
    }

    // The refresh call itself returned 401 — token is invalid, logout immediately
    if (original.url?.includes('/auth/refresh')) {
      useAuthStore.getState().logout()
      return Promise.reject(error)
    }

    // Another refresh is already in flight — queue this request
    if (isRefreshing) {
      return new Promise<string>((resolve) => enqueue(resolve)).then((newToken) => {
        original.headers.Authorization = `Bearer ${newToken}`
        return client(original)
      })
    }

    isRefreshing = true
    const { refreshToken, user, setAuth, logout } = useAuthStore.getState()

    if (!refreshToken || !user) {
      logout()
      isRefreshing = false
      return Promise.reject(error)
    }

    try {
      // Use plain axios to avoid going through this interceptor again
      const { data } = await axios.post<{ access_token: string; refresh_token: string }>(
        '/api/v1/auth/refresh',
        { refresh_token: refreshToken }
      )
      setAuth(user, data.access_token, data.refresh_token)
      flushQueue(data.access_token)
      original.headers.Authorization = `Bearer ${data.access_token}`
      return client(original)
    } catch {
      logout()
      subscribers = []
      return Promise.reject(error)
    } finally {
      isRefreshing = false
    }
  }
)

export default client
