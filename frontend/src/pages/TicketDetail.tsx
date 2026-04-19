import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getTicket, getMessages, createMessage, replyTicket, getStatuses } from '../api/tickets'
import { getCustomer } from '../api/customers'
import type { Ticket, Message, TicketStatus, Customer } from '../types'

const PRIORITY_LABEL: Record<string, string> = {
  low: 'Baja', medium: 'Media', high: 'Alta', urgent: 'Urgente',
}

export default function TicketDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [statuses, setStatuses] = useState<TicketStatus[]>([])
  const [customer, setCustomer] = useState<Customer | null>(null)
  const [body, setBody] = useState('')
  const [msgType, setMsgType] = useState<'reply' | 'comment'>('reply')
  const [sending, setSending] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    Promise.all([
      getTicket(id),
      getMessages(id),
      getStatuses(),
    ]).then(([t, m, s]) => {
      setTicket(t)
      setMessages(m)
      setStatuses(s)
      return getCustomer(t.customer_id)
    }).then(setCustomer)
      .finally(() => setLoading(false))
  }, [id])

  const getStatusName = (statusId: string) =>
    statuses.find((s) => s.id === statusId)?.name ?? '—'

  const getStatusColor = (statusId: string) =>
    statuses.find((s) => s.id === statusId)?.color ?? '#6B7280'

  const usesEmailChannel = (t: typeof ticket) =>
    msgType === 'reply' && t?.channel === 'email' && !!t.channel_id

  const handleSend = async () => {
    if (!id || !body.trim()) return
    setSending(true)
    try {
      const msg = usesEmailChannel(ticket)
        ? await replyTicket(id, { body, msg_type: msgType })
        : await createMessage(id, { body, msg_type: msgType })
      setMessages((prev) => [...prev, msg])
      setBody('')
    } finally {
      setSending(false)
    }
  }

  if (loading) return <div className="p-6 text-sm text-gray-500">Cargando...</div>
  if (!ticket) return <div className="p-6 text-sm text-gray-500">Ticket no encontrado</div>

  return (
    <div className="p-6 max-w-4xl">
      {/* Breadcrumb */}
      <button
        onClick={() => navigate('/tickets')}
        className="text-sm text-gray-500 hover:text-gray-700 mb-4 flex items-center gap-1"
      >
        ← Tickets
      </button>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">{ticket.subject}</h1>
          <div className="flex items-center gap-2 mt-2">
            <span
              className="px-2 py-1 rounded-full text-xs font-medium"
              style={{
                backgroundColor: getStatusColor(ticket.status_id) + '20',
                color: getStatusColor(ticket.status_id),
              }}
            >
              {getStatusName(ticket.status_id)}
            </span>
            <span className="text-xs text-gray-500">
              {PRIORITY_LABEL[ticket.priority]} · {ticket.channel}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Hilo de mensajes */}
        <div className="col-span-2 flex flex-col gap-4">
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            {messages.length === 0 ? (
              <div className="p-6 text-sm text-gray-500 text-center">Sin mensajes aún</div>
            ) : (
              <div className="divide-y divide-gray-100">
                {messages.map((msg) => (
                  <div key={msg.id} className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        msg.msg_type === 'comment'
                          ? 'bg-yellow-100 text-yellow-700'
                          : msg.direction === 'outbound'
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-gray-100 text-gray-600'
                      }`}>
                        {msg.msg_type === 'comment' ? 'Nota interna' : msg.direction === 'outbound' ? 'Respuesta' : 'Cliente'}
                      </span>
                      <span className="text-xs text-gray-400">
                        {new Date(msg.created_at).toLocaleString('es-MX')}
                      </span>
                    </div>
                    <p className="text-sm text-gray-800 whitespace-pre-wrap">{msg.body}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Composer */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex gap-2 mb-3">
              <button
                onClick={() => setMsgType('reply')}
                className={`px-3 py-1.5 text-xs rounded-md font-medium transition-colors ${
                  msgType === 'reply' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'
                }`}
              >
                Respuesta
              </button>
              <button
                onClick={() => setMsgType('comment')}
                className={`px-3 py-1.5 text-xs rounded-md font-medium transition-colors ${
                  msgType === 'comment' ? 'bg-yellow-500 text-white' : 'bg-gray-100 text-gray-600'
                }`}
              >
                Nota interna
              </button>
            </div>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder={msgType === 'reply' ? 'Escribe una respuesta al cliente...' : 'Escribe una nota interna...'}
              rows={4}
              className="w-full text-sm border border-gray-200 rounded-md p-3 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex items-center justify-between mt-2">
              <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                msgType === 'comment'
                  ? 'bg-yellow-100 text-yellow-700'
                  : usesEmailChannel(ticket)
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-500'
              }`}>
                {msgType === 'comment'
                  ? 'Guardará como nota interna'
                  : usesEmailChannel(ticket)
                  ? 'Enviará por Email'
                  : 'Guardará como mensaje interno'}
              </span>
              <button
                onClick={handleSend}
                disabled={sending || !body.trim()}
                className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {sending ? 'Enviando...' : 'Enviar'}
              </button>
            </div>
          </div>
        </div>

        {/* Panel lateral */}
        <div className="flex flex-col gap-4">
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Cliente</h3>
            {customer ? (
              <div>
                <p className="text-sm font-medium text-gray-900">{customer.full_name}</p>
                {customer.email && <p className="text-xs text-gray-500 mt-0.5">{customer.email}</p>}
                {customer.phone && <p className="text-xs text-gray-500">{customer.phone}</p>}
                {customer.company && <p className="text-xs text-gray-500">{customer.company}</p>}
              </div>
            ) : (
              <p className="text-sm text-gray-400">Sin cliente</p>
            )}
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Detalles</h3>
            <div className="flex flex-col gap-2 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-500">Canal</span>
                <span className="text-gray-900 capitalize">{ticket.channel}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Prioridad</span>
                <span className="text-gray-900">{PRIORITY_LABEL[ticket.priority]}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Creado</span>
                <span className="text-gray-900">{new Date(ticket.created_at).toLocaleDateString('es-MX')}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}