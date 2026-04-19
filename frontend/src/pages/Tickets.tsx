import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getTickets, getStatuses } from '../api/tickets'
import type { Ticket, TicketStatus } from '../types'
import CreateTicketModal from '../components/tickets/CreateTicketModal'

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

export default function Tickets() {
  const navigate = useNavigate()
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [statuses, setStatuses] = useState<TicketStatus[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)

  useEffect(() => {
    getStatuses().then(setStatuses)
  }, [])

  const loadTickets = () => {
    setLoading(true)
    getTickets({ status_id: statusFilter || undefined })
      .then((res) => {
        setTickets(res.items)
        setTotal(res.total)
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadTickets()
  }, [statusFilter])

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
            loadTickets()
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
      </div>

      {/* Tabla */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-sm text-gray-500">Cargando...</div>
        ) : tickets.length === 0 ? (
          <div className="p-8 text-center text-sm text-gray-500">No hay tickets</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left px-4 py-3 font-medium text-gray-600">Asunto</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Estado</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Prioridad</th>
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
                  <td className="px-4 py-3 font-medium text-gray-900">{ticket.subject}</td>
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
                  <td className="px-4 py-3 text-gray-600 capitalize">{ticket.channel}</td>
                  <td className="px-4 py-3 text-gray-500">
                    {new Date(ticket.created_at).toLocaleDateString('es-MX')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}