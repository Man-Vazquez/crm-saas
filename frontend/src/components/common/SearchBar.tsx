import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { globalSearch } from '../../api/search'
import type { SearchResponse } from '../../api/search'

export default function SearchBar() {
  const navigate = useNavigate()
  const containerRef = useRef<HTMLDivElement>(null)
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<SearchResponse | null>(null)

  // Close dropdown on click outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  // Close dropdown on Escape
  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open])

  // Debounced search
  useEffect(() => {
    if (query.length < 2) {
      setResults(null)
      setLoading(false)
      return
    }
    setOpen(true)
    setLoading(true)
    const timer = setTimeout(async () => {
      try {
        const data = await globalSearch(query)
        setResults(data)
      } catch {
        setResults(null)
      } finally {
        setLoading(false)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [query])

  const go = (path: string) => {
    navigate(path)
    setQuery('')
    setResults(null)
    setOpen(false)
  }

  const hasTickets = (results?.tickets.length ?? 0) > 0
  const hasCustomers = (results?.customers.length ?? 0) > 0
  const hasMessages = (results?.messages.length ?? 0) > 0
  const hasAny = hasTickets || hasCustomers || hasMessages
  const showDropdown = open && query.length >= 2

  return (
    <div ref={containerRef} className="relative w-full">
      {/* Input */}
      <div className="flex items-center gap-2 h-9 px-3 rounded-lg bg-gray-100 border border-transparent focus-within:bg-white focus-within:border-blue-500 transition-colors">
        <svg
          className="w-4 h-4 text-gray-400 shrink-0"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z"
          />
        </svg>

        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => { if (query.length >= 2) setOpen(true) }}
          placeholder="Buscar tickets, clientes, mensajes..."
          className="flex-1 text-sm text-gray-900 bg-transparent outline-none placeholder-gray-400"
        />

        {loading && (
          <svg
            className="w-4 h-4 text-gray-400 animate-spin shrink-0"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
        )}
      </div>

      {/* Dropdown */}
      {showDropdown && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-lg shadow-xl border border-gray-200 z-50 max-h-[400px] overflow-y-auto">
          {/* Loading */}
          {loading && (
            <p className="px-4 py-4 text-sm text-gray-400 text-center">Buscando...</p>
          )}

          {/* No results */}
          {!loading && results && !hasAny && (
            <p className="px-4 py-4 text-sm text-gray-400 text-center">
              No se encontraron resultados para &quot;{results.query}&quot;
            </p>
          )}

          {/* Results */}
          {!loading && hasAny && (
            <div className="py-1">
              {/* Tickets */}
              {hasTickets && (
                <section>
                  <div className="px-4 py-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wide bg-gray-50">
                    Tickets ({results!.tickets.length})
                  </div>
                  {results!.tickets.map((t) => (
                    <button
                      key={t.id}
                      onMouseDown={() => go(`/tickets/${t.id}`)}
                      className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-gray-50 text-left transition-colors"
                    >
                      <div className="flex flex-col min-w-0">
                        <span className="text-sm text-gray-900 truncate">
                          <span className="font-medium text-gray-500">#{t.ticket_number}</span>{' '}
                          {t.subject}
                        </span>
                        <span className="text-xs text-gray-400 mt-0.5 truncate">
                          {t.customer_name} · {t.channel}
                        </span>
                      </div>
                      <span className="ml-3 shrink-0 text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                        {t.status}
                      </span>
                    </button>
                  ))}
                </section>
              )}

              {/* Clientes */}
              {hasCustomers && (
                <section>
                  <div className="px-4 py-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wide bg-gray-50">
                    Clientes ({results!.customers.length})
                  </div>
                  {results!.customers.map((c) => (
                    <button
                      key={c.id}
                      onMouseDown={() => go(`/customers/${c.id}`)}
                      className="w-full flex flex-col px-4 py-2.5 hover:bg-gray-50 text-left transition-colors"
                    >
                      <span className="text-sm text-gray-900">{c.name}</span>
                      <span className="text-xs text-gray-400 mt-0.5">
                        {c.email}
                        {c.company ? ` · ${c.company}` : ''}
                      </span>
                    </button>
                  ))}
                </section>
              )}

              {/* Mensajes */}
              {hasMessages && (
                <section>
                  <div className="px-4 py-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wide bg-gray-50">
                    Mensajes ({results!.messages.length})
                  </div>
                  {results!.messages.map((m) => (
                    <button
                      key={m.id}
                      onMouseDown={() => go(`/tickets/${m.ticket_id}`)}
                      className="w-full flex flex-col px-4 py-2.5 hover:bg-gray-50 text-left transition-colors"
                    >
                      <span className="text-sm text-gray-900 truncate">
                        <span className="font-medium text-gray-500">#{m.ticket_number}</span>{' '}
                        {m.ticket_subject}
                      </span>
                      <span className="text-xs text-gray-400 mt-0.5 truncate italic">
                        &ldquo;{m.body_snippet}&rdquo;
                      </span>
                    </button>
                  ))}
                </section>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
