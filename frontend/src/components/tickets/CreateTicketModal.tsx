import { useEffect, useRef, useState } from 'react'
import { createTicket, getStatuses, getTypes } from '../../api/tickets'
import { getCustomers } from '../../api/customers'
import { getChannels } from '../../api/channels'
import type { Channel, Customer, TicketStatus, TicketType } from '../../types'

const PRIORITIES = [
  { value: 'low', label: 'Baja' },
  { value: 'medium', label: 'Media' },
  { value: 'high', label: 'Alta' },
  { value: 'urgent', label: 'Urgente' },
]

interface Props {
  onClose: () => void
  onCreated: () => void
}

export default function CreateTicketModal({ onClose, onCreated }: Props) {
  const [subject, setSubject] = useState('')
  const [priority, setPriority] = useState('medium')
  const [statusId, setStatusId] = useState('')
  const [channelId, setChannelId] = useState('')
  const [typeId, setTypeId] = useState('')

  const [statuses, setStatuses] = useState<TicketStatus[]>([])
  const [channels, setChannels] = useState<Channel[]>([])
  const [types, setTypes] = useState<TicketType[]>([])

  const [customerSearch, setCustomerSearch] = useState('')
  const [customerResults, setCustomerResults] = useState<Customer[]>([])
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null)
  const [showDropdown, setShowDropdown] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    Promise.all([getStatuses(), getTypes(), getChannels()]).then(([s, t, c]) => {
      setStatuses(s)
      setTypes(t)
      setChannels(c)
      const def = s.find((x) => x.is_default) ?? s[0]
      if (def) setStatusId(def.id)
    })
  }, [])

  useEffect(() => {
    if (!customerSearch || selectedCustomer) return
    const timer = setTimeout(() => {
      getCustomers({ search: customerSearch, limit: 8 }).then((res) => {
        setCustomerResults(res.items)
        setShowDropdown(true)
      })
    }, 300)
    return () => clearTimeout(timer)
  }, [customerSearch, selectedCustomer])

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const selectCustomer = (c: Customer) => {
    setSelectedCustomer(c)
    setCustomerSearch(c.full_name)
    setShowDropdown(false)
    setCustomerResults([])
  }

  const clearCustomer = () => {
    setSelectedCustomer(null)
    setCustomerSearch('')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedCustomer || !subject || !statusId) return
    setSubmitting(true)
    const selectedChannel = channels.find((c) => c.id === channelId) ?? null
    try {
      await createTicket({
        customer_id: selectedCustomer.id,
        subject,
        priority,
        status_id: statusId,
        channel: selectedChannel ? selectedChannel.channel_type : 'manual',
        channel_id: selectedChannel ? selectedChannel.id : undefined,
        type_id: typeId || undefined,
      })
      onCreated()
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-base font-semibold text-gray-900">Nuevo Ticket</h2>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {/* Customer search */}
          <div ref={dropdownRef} className="relative">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Cliente <span className="text-red-500">*</span>
            </label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={customerSearch}
                onChange={(e) => {
                  if (selectedCustomer) clearCustomer()
                  setCustomerSearch(e.target.value)
                }}
                placeholder="Buscar cliente..."
                disabled={!!selectedCustomer}
                className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
              />
              {selectedCustomer && (
                <button
                  type="button"
                  onClick={clearCustomer}
                  className="text-gray-400 hover:text-gray-600 text-sm"
                >
                  ✕
                </button>
              )}
            </div>
            {showDropdown && customerResults.length > 0 && (
              <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg max-h-48 overflow-y-auto">
                {customerResults.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => selectCustomer(c)}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex flex-col"
                  >
                    <span className="font-medium text-gray-900">{c.full_name}</span>
                    {c.email && <span className="text-gray-500 text-xs">{c.email}</span>}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Subject */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Asunto <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Descripción breve del ticket"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {/* Priority + Status */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Prioridad</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {PRIORITIES.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Estado <span className="text-red-500">*</span>
              </label>
              <select
                value={statusId}
                onChange={(e) => setStatusId(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="">Seleccionar...</option>
                {statuses.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Channel + Type */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Canal</label>
              <select
                value={channelId}
                onChange={(e) => setChannelId(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Sin canal</option>
                {channels.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
              <select
                value={typeId}
                onChange={(e) => setTypeId(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Sin tipo</option>
                {types.map((t) => (
                  <option key={t.id} value={t.id}>{t.name}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={submitting || !selectedCustomer || !subject || !statusId}
              className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Creando...' : 'Crear Ticket'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
