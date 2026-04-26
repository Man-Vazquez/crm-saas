import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getTickets, getStatuses } from '../api/tickets'
import { getDepartments } from '../api/departments'
import type { Ticket, TicketStatus, Department } from '../types'
import { useAuthStore } from '../store/authStore'
import { usePolling } from '../hooks/usePolling'
import CreateTicketModal from '../components/tickets/CreateTicketModal'
import Pagination from '../components/common/Pagination'
import ErrorMessage from '../components/common/ErrorMessage'
import LoadingSpinner from '../components/common/LoadingSpinner'

const PRIORITY_LABEL: Record<string, string> = {
  low: 'Baja',
  medium: 'Media',
  high: 'Alta',
  urgent: 'Urgente',
}

const PRIORITY_COLOR: Record<string, string> = {
  low: 'bg-gray-100 text-gray-600',
  medium: 'bg-blue-100 text-blue-700',
  high: 'bg-orange-100 text-orange-700',
  urgent: 'bg-red-100 text-red-700',
}

const LIMIT = 20

export default function Tickets() {
  const navigate = useNavigate()
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  const [tickets, setTickets] = useState<Ticket[]>([])
  const [statuses, setStatuses] = useState<TicketStatus[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [departmentFilter, setDepartmentFilter] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)

  // Timestamp of the last successful fetch; null until the first load completes
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  // Seconds since last update, recalculated every second for the status text
  const [secondsSince, setSecondsSince] = useState(0)

  // Keep a stable ref to the current page so the polling callback always
  // uses the latest value without needing to be recreated.
  const pageRef = useRef(page)
  useEffect(() => { pageRef.current = page }, [page])

  const statusFilterRef = useRef(statusFilter)
  useEffect(() => { statusFilterRef.current = statusFilter }, [statusFilter])

  const departmentFilterRef = useRef(departmentFilter)
  useEffect(() => { departmentFilterRef.current = departmentFilter }, [departmentFilter])

  useEffect(() => {
    getStatuses().then(setStatuses)
    getDepartments().then(setDepartments)
  }, [])

  /**
   * Main fetch function.
   * @param currentPage  Page to load.
   * @param silent       When true: skips the loading spinner and does NOT
   *                     modify the error state (poll-triggered refresh).
   */
  const loadTickets = (currentPage: number, silent = false) => {
    if (!silent) {
      setLoading(true)
      setError(null)
    }
    getTickets({
      skip: (currentPage - 1) * LIMIT,
      limit: LIMIT,
      status_id: statusFilterRef.current || undefined,
      department_id: departmentFilterRef.current || undefined,
    })
      .then((res) => {
        setTickets(res.items)
        setTotal(res.total)
        setLastUpdated(new Date())
        setSecondsSince(0)
      })
      .catch(() => {
        // Silent polls fail quietly; only surface errors on explicit loads
        if (!silent) {
          setError('No se pudieron cargar los tickets. Verifica tu conexión.')
        }
      })
      .finally(() => {
        if (!silent) setLoading(false)
      })
  }

  // Reset to page 1 whenever a filter changes
  useEffect(() => {
    setPage(1)
    loadTickets(1)
  }, [statusFilter, departmentFilter])

  // Load when page changes (skip the very first render — the filter effect handles it)
  const isFirstRender = useRef(true)
  useEffect(() => {
    if (isFirstRender.current) { isFirstRender.current = false; return }
    loadTickets(page)
  }, [page])

  // Polling — silent refresh every 30 s while the user is authenticated
  usePolling(
    () => loadTickets(pageRef.current, true),
    30_000,
    isAuthenticated,
  )

  // Tick the "updated X sec ago" counter every second
  useEffect(() => {
    const id = setInterval(() => {
      setSecondsSince((s) => s + 1)
    }, 1_000)
    return () => clearInterval(id)
  }, [])

  const handlePageChange = (newPage: number) => {
    setPage(newPage)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const updatedLabel = (() => {
    if (!lastUpdated) return null
    if (secondsSince < 5) return 'Actualizado ahora'
    if (secondsSince < 60) return `Actualizado hace ${secondsSince} seg`
    const mins = Math.floor(secondsSince / 60)
    return `Actualizado hace ${mins} min`
  })()

  const getStatusName = (id: string) =>
    statuses.find((s) => s.id === id)?.name ?? '—'

  const getStatusColor = (id: string) =>
    statuses.find((s) => s.id === id)?.color ?? '#6B7280'

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Tickets</h1>
          <p className="text-sm text-gray-500 mt-0.5">{total} tickets en total</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700"
        >
          Nuevo Ticket
        </button>
      </div>

      {showCreateModal && (
        <CreateTicketModal
          onClose={() => setShowCreateModal(false)}
          onCreated={() => {
            setShowCreateModal(false)
            loadTickets(page)
          }}
        />
      )}

      {/* Filtros */}
      <div className="flex gap-3 mb-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todos los estados</option>
          {statuses.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
        {departments.length > 0 && (
          <select
            value={departmentFilter}
            onChange={(e) => setDepartmentFilter(e.target.value)}
            className="px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todos los departamentos</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        )}
      </div>

      {error && (
        <ErrorMessage message={error} onRetry={() => loadTickets(page)} />
      )}

      {/* Tabla */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        {updatedLabel && !loading && (
          <div className="flex justify-end px-4 pt-2">
            <span className="text-xs text-gray-400">{updatedLabel}</span>
          </div>
        )}
        {loading ? (
          <LoadingSpinner />
        ) : tickets.length === 0 ? (
          <div className="p-8 text-center text-sm text-gray-500">No hay tickets</div>
        ) : (
          <>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Asunto</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Estado</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Prioridad</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Departamento</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Canal</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Fecha</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((ticket) => (
                  <tr
                    key={ticket.id}
                    onClick={() => navigate(`/tickets/${ticket.id}`)}
                    className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors last:border-0"
                  >
                    <td className="px-4 py-3 font-medium text-gray-900">
                      {ticket.ticket_number != null && (
                        <span className="text-gray-400 font-normal mr-1">#{ticket.ticket_number} ·</span>
                      )}
                      {ticket.subject}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className="px-2 py-1 rounded-full text-xs font-medium"
                        style={{
                          backgroundColor: getStatusColor(ticket.status_id) + '20',
                          color: getStatusColor(ticket.status_id),
                        }}
                      >
                        {getStatusName(ticket.status_id)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${PRIORITY_COLOR[ticket.priority]}`}>
                        {PRIORITY_LABEL[ticket.priority]}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500">{ticket.department_name ?? '—'}</td>
                    <td className="px-4 py-3 text-gray-600 capitalize">{ticket.channel}</td>
                    <td className="px-4 py-3 text-gray-500">
                      {new Date(ticket.created_at).toLocaleDateString('es-MX')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <Pagination total={total} page={page} limit={LIMIT} onChange={handlePageChange} />
          </>
        )}
      </div>
    </div>
  )
}