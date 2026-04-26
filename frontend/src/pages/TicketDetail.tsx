import { useEffect, useState } from 'react'
import DOMPurify from 'dompurify'
import { useParams, useNavigate } from 'react-router-dom'
import { getTicket, getMessages, createMessage, replyTicket, getStatuses, getTypes, getSubtypes, updateTicket } from '../api/tickets'
import { getCustomer } from '../api/customers'
import { getAdminUsers } from '../api/admin'
import { getDepartments } from '../api/departments'
import type { Ticket, Message, TicketStatus, TicketType, TicketSubtype, Customer, AdminUser, Department } from '../types'
import ErrorMessage from '../components/common/ErrorMessage'
import LoadingSpinner from '../components/common/LoadingSpinner'

const PRIORITY_LABEL: Record<string, string> = {
  low: 'Baja', medium: 'Media', high: 'Alta', urgent: 'Urgente',
}

const SELECT_CLS =
  'text-xs border border-gray-200 rounded px-1.5 py-0.5 bg-white text-gray-900 ' +
  'focus:outline-none focus:ring-1 focus:ring-blue-400 disabled:opacity-40 max-w-[140px]'

function FieldRow({
  label,
  status,
  children,
}: {
  label: string
  status: 'saving' | 'saved' | 'error' | undefined
  children: React.ReactNode
}) {
  return (
    <div className="flex justify-between items-start gap-2">
      <span className="text-gray-500 shrink-0 pt-0.5">{label}</span>
      <div className="flex flex-col items-end gap-0.5">
        {children}
        {status === 'saving' && <span className="text-[10px] text-gray-400">Guardando…</span>}
        {status === 'saved'  && <span className="text-[10px] text-green-600">Guardado</span>}
        {status === 'error'  && <span className="text-[10px] text-red-500">Error al guardar</span>}
      </div>
    </div>
  )
}

const PRIORITY_OPTIONS = [
  { value: 'low',    label: 'Baja' },
  { value: 'medium', label: 'Media' },
  { value: 'high',   label: 'Alta' },
  { value: 'urgent', label: 'Urgente' },
]

export default function TicketDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [statuses, setStatuses] = useState<TicketStatus[]>([])
  const [types, setTypes] = useState<TicketType[]>([])
  const [subtypes, setSubtypes] = useState<TicketSubtype[]>([])
  const [users, setUsers] = useState<AdminUser[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [customer, setCustomer] = useState<Customer | null>(null)
  const [body, setBody] = useState('')
  const [msgType, setMsgType] = useState<'reply' | 'comment'>('reply')
  const [sending, setSending] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [fieldStatus, setFieldStatus] = useState<Record<string, 'saving' | 'saved' | 'error'>>({})

  const clearFieldStatus = (field: string) =>
    setFieldStatus(prev => { const n = { ...prev }; delete n[field]; return n })

  const loadSubtypes = (typeId: string) => {
    getSubtypes(typeId).then(setSubtypes).catch(() => setSubtypes([]))
  }

  const loadData = () => {
    if (!id) return
    setLoading(true)
    setError(null)
    Promise.all([
      getTicket(id),
      getMessages(id),
      getStatuses(),
      getTypes(),
      getAdminUsers(0, 100),
      getDepartments(),
    ]).then(([t, m, s, ty, u, depts]) => {
      setTicket(t)
      setMessages(m)
      setStatuses(s)
      setTypes(ty)
      setUsers(u.items)
      setDepartments(depts)
      if (t.type_id) loadSubtypes(t.type_id)
      return getCustomer(t.customer_id)
    }).then(setCustomer)
      .catch(() => setError('No se pudieron cargar los datos del ticket. Verifica tu conexión.'))
      .finally(() => setLoading(false))
  }

  const handleFieldChange = async (field: string, value: string | null) => {
    if (!id || !ticket) return
    setFieldStatus(prev => ({ ...prev, [field]: 'saving' }))
    try {
      // Changing type resets subtype in the same PATCH to avoid stale subtypes
      const patch = (field === 'type_id'
        ? { type_id: value || null, subtype_id: null }
        : { [field]: value || null }
      ) as Partial<Ticket>
      const updated = await updateTicket(id, patch)
      setTicket(updated)
      if (field === 'type_id') {
        setSubtypes([])
        if (value) loadSubtypes(value)
      }
      setFieldStatus(prev => ({ ...prev, [field]: 'saved' }))
      setTimeout(() => clearFieldStatus(field), 2000)
    } catch {
      setFieldStatus(prev => ({ ...prev, [field]: 'error' }))
      setTimeout(() => clearFieldStatus(field), 3000)
    }
  }

  useEffect(() => {
    loadData()
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

  if (loading) return <div className="p-6"><LoadingSpinner /></div>
  if (error) return <div className="p-6"><ErrorMessage message={error} onRetry={loadData} /></div>
  if (!ticket) return <div className="p-6 text-sm text-gray-500">Ticket no encontrado</div>

  return (
    <div className="p-6 max-w-4xl">
      {/* Breadcrumb */}
      <button
        onClick={() => navigate('/tickets')}
        className="text-sm text-gray-500 hover:text-gray-700 mb-4 flex items-center gap-1"
      >
        ← Tickets{ticket.ticket_number != null && ` / #${ticket.ticket_number}`}
      </button>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">
            {ticket.ticket_number != null && (
              <span className="text-gray-400 font-normal mr-1">#{ticket.ticket_number} ·</span>
            )}
            {ticket.subject}
          </h1>
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
                    {ticket.channel === 'email' && msg.msg_type !== 'comment' ? (
                      // Email HTML body — rendered as markup so images, formatting and
                      // links display correctly. Sanitized with DOMPurify to prevent XSS.
                      <div
                        className="text-sm text-gray-800 overflow-x-auto
                          [&_img]:max-w-full [&_img]:h-auto
                          [&_a]:text-blue-600 [&_a]:underline
                          [&_p]:mb-2 [&_p:last-child]:mb-0"
                        dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(msg.body) }}
                      />
                    ) : (
                      <p className="text-sm text-gray-800 whitespace-pre-wrap">{msg.body}</p>
                    )}
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
            <div className="flex flex-col gap-3 text-xs">

              {/* Estado */}
              <FieldRow label="Estado" status={fieldStatus['status_id']}>
                <select
                  value={ticket.status_id}
                  disabled={fieldStatus['status_id'] === 'saving'}
                  onChange={e => handleFieldChange('status_id', e.target.value)}
                  className={SELECT_CLS}
                >
                  {statuses.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </FieldRow>

              {/* Prioridad */}
              <FieldRow label="Prioridad" status={fieldStatus['priority']}>
                <select
                  value={ticket.priority}
                  disabled={fieldStatus['priority'] === 'saving'}
                  onChange={e => handleFieldChange('priority', e.target.value)}
                  className={SELECT_CLS}
                >
                  {PRIORITY_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </FieldRow>

              {/* Tipo */}
              <FieldRow label="Tipo" status={fieldStatus['type_id']}>
                <select
                  value={ticket.type_id ?? ''}
                  disabled={fieldStatus['type_id'] === 'saving'}
                  onChange={e => handleFieldChange('type_id', e.target.value || null)}
                  className={SELECT_CLS}
                >
                  <option value="">Sin tipo</option>
                  {types.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
              </FieldRow>

              {/* Subtipo */}
              <FieldRow label="Subtipo" status={fieldStatus['subtype_id']}>
                <select
                  value={ticket.subtype_id ?? ''}
                  disabled={!ticket.type_id || fieldStatus['subtype_id'] === 'saving'}
                  onChange={e => handleFieldChange('subtype_id', e.target.value || null)}
                  className={SELECT_CLS}
                >
                  <option value="">Sin subtipo</option>
                  {subtypes.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </FieldRow>

              {/* Agente */}
              <FieldRow label="Agente" status={fieldStatus['assigned_to']}>
                <select
                  value={ticket.assigned_to ?? ''}
                  disabled={fieldStatus['assigned_to'] === 'saving'}
                  onChange={e => handleFieldChange('assigned_to', e.target.value || null)}
                  className={SELECT_CLS}
                >
                  <option value="">Sin asignar</option>
                  {users.map(u => <option key={u.id} value={u.id}>{u.full_name}</option>)}
                </select>
              </FieldRow>

              {/* Departamento */}
              <FieldRow label="Departamento" status={fieldStatus['department_id']}>
                <select
                  value={ticket.department_id ?? ''}
                  disabled={fieldStatus['department_id'] === 'saving'}
                  onChange={e => handleFieldChange('department_id', e.target.value || null)}
                  className={SELECT_CLS}
                >
                  <option value="">Sin departamento</option>
                  {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
              </FieldRow>

              {/* Canal, fechas y actividad — solo lectura */}
              <div className="flex justify-between pt-1 border-t border-gray-100">
                <span className="text-gray-500">Canal</span>
                <span className="text-gray-900 capitalize">{ticket.channel}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Creado</span>
                <span className="text-gray-900">{new Date(ticket.created_at).toLocaleString('es-MX')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Actualizado</span>
                <span className="text-gray-900">{new Date(ticket.updated_at).toLocaleString('es-MX')}</span>
              </div>
              {ticket.updated_by && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Por</span>
                  <span className="text-gray-900 text-right">
                    {users.find(u => u.id === ticket.updated_by)?.full_name ?? '—'}
                  </span>
                </div>
              )}

            </div>
          </div>
        </div>
      </div>
    </div>
  )
}