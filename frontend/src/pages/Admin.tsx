import { useEffect, useState } from 'react'
import {
  getAdminUsers,
  createAdminUser,
  updateAdminUser,
  deleteAdminUser,
  getAdminTenant,
  updateAdminTenant,
} from '../api/admin'
import { getChannels, createChannel, updateChannel } from '../api/channels'
import {
  getDepartments,
  createDepartment,
  updateDepartment,
  getDepartmentAgents,
  addDepartmentAgent,
  removeDepartmentAgent,
} from '../api/departments'
import type { AdminUser, Channel, Department, DepartmentAgent, Tenant } from '../types'
import ErrorMessage from '../components/common/ErrorMessage'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Pagination from '../components/common/Pagination'

type Tab = 'users' | 'channels' | 'departments' | 'account'

const TABS: { id: Tab; label: string }[] = [
  { id: 'users', label: 'Usuarios' },
  { id: 'channels', label: 'Canales' },
  { id: 'departments', label: 'Departamentos' },
  { id: 'account', label: 'Cuenta' },
]

const ROLE_BADGE: Record<string, string> = {
  admin: 'bg-red-100 text-red-700',
  supervisor: 'bg-yellow-100 text-yellow-700',
  agent: 'bg-blue-100 text-blue-700',
}

const ROLE_LABEL: Record<string, string> = {
  admin: 'Admin',
  supervisor: 'Supervisor',
  agent: 'Agente',
}

// ── Create User Modal ──────────────────────────────────────────────────────

interface CreateUserModalProps {
  onClose: () => void
  onCreated: () => void
}

function CreateUserModal({ onClose, onCreated }: CreateUserModalProps) {
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('agent')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await createAdminUser({ email, full_name: fullName, password, role })
      onCreated()
    } catch {
      setError('Error al crear el usuario. Verifica los datos.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-base font-semibold text-gray-900">Nuevo usuario</h2>
          <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">{error}</p>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nombre completo <span className="text-red-500">*</span></label>
            <input
              type="text"
              value={fullName}
              onChange={e => setFullName(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email <span className="text-red-500">*</span></label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña <span className="text-red-500">*</span></label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Rol</label>
            <select
              value={role}
              onChange={e => setRole(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="agent">Agente</option>
              <option value="supervisor">Supervisor</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50">Cancelar</button>
            <button type="submit" disabled={saving} className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50">
              {saving ? 'Creando...' : 'Crear usuario'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Edit User Modal ────────────────────────────────────────────────────────

interface EditUserModalProps {
  user: AdminUser
  onClose: () => void
  onSaved: () => void
}

function EditUserModal({ user, onClose, onSaved }: EditUserModalProps) {
  const [fullName, setFullName] = useState(user.full_name)
  const [role, setRole] = useState(user.role)
  const [isActive, setIsActive] = useState(user.is_active)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await updateAdminUser(user.id, { full_name: fullName, role, is_active: isActive })
      onSaved()
    } catch {
      setError('Error al guardar los cambios.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-base font-semibold text-gray-900">Editar usuario</h2>
          <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">{error}</p>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nombre completo</label>
            <input
              type="text"
              value={fullName}
              onChange={e => setFullName(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Rol</label>
            <select
              value={role}
              onChange={e => setRole(e.target.value as AdminUser['role'])}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="agent">Agente</option>
              <option value="supervisor">Supervisor</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div className="flex items-center gap-3">
            <input
              id="is_active"
              type="checkbox"
              checked={isActive}
              onChange={e => setIsActive(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300 text-blue-600"
            />
            <label htmlFor="is_active" className="text-sm text-gray-700">Usuario activo</label>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50">Cancelar</button>
            <button type="submit" disabled={saving} className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50">
              {saving ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Create Channel Modal ───────────────────────────────────────────────────

interface CreateChannelModalProps {
  onClose: () => void
  onCreated: () => void
}

function CreateChannelModal({ onClose, onCreated }: CreateChannelModalProps) {
  const [name, setName] = useState('')
  const [smtpHost, setSmtpHost] = useState('')
  const [smtpPort, setSmtpPort] = useState('587')
  const [smtpUser, setSmtpUser] = useState('')
  const [smtpPassword, setSmtpPassword] = useState('')
  const [imapHost, setImapHost] = useState('')
  const [imapPort, setImapPort] = useState('993')
  const [fromName, setFromName] = useState('')
  const [departmentId, setDepartmentId] = useState<string>('')
  const [departments, setDepartments] = useState<Department[]>([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getDepartments().then(setDepartments).catch(() => {})
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await createChannel({
        channel_type: 'email',
        name,
        config: {
          smtp_host: smtpHost,
          smtp_port: smtpPort,
          smtp_user: smtpUser,
          smtp_password: smtpPassword,
          imap_host: imapHost,
          imap_port: imapPort,
          from_name: fromName,
        },
        department_id: departmentId || null,
      })
      onCreated()
    } catch {
      setError('Error al crear el canal. Verifica los datos.')
    } finally {
      setSaving(false)
    }
  }

  const field = (label: string, value: string, setter: (v: string) => void, opts?: { type?: string; placeholder?: string }) => (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type={opts?.type ?? 'text'}
        value={value}
        onChange={e => setter(e.target.value)}
        placeholder={opts?.placeholder}
        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        required
      />
    </div>
  )

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-screen overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-base font-semibold text-gray-900">Nuevo canal Email</h2>
          <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">{error}</p>
          )}
          {field('Nombre del canal', name, setName, { placeholder: 'Email soporte' })}
          {field('Nombre remitente', fromName, setFromName, { placeholder: 'Soporte Empresa' })}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Departamento</label>
            <select
              value={departmentId}
              onChange={e => setDepartmentId(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Sin departamento</option>
              {departments.filter(d => d.is_active).map(d => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide pt-1">Configuración SMTP (envío)</p>
          {field('SMTP Host', smtpHost, setSmtpHost, { placeholder: 'smtp.gmail.com' })}
          <div className="grid grid-cols-2 gap-3">
            {field('Puerto SMTP', smtpPort, setSmtpPort)}
            {field('Usuario SMTP', smtpUser, setSmtpUser, { placeholder: 'cuenta@empresa.com' })}
          </div>
          {field('Contraseña SMTP', smtpPassword, setSmtpPassword, { type: 'password' })}
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide pt-1">Configuración IMAP (recepción)</p>
          <div className="grid grid-cols-2 gap-3">
            {field('IMAP Host', imapHost, setImapHost, { placeholder: 'imap.gmail.com' })}
            {field('Puerto IMAP', imapPort, setImapPort)}
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50">Cancelar</button>
            <button type="submit" disabled={saving} className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50">
              {saving ? 'Creando...' : 'Crear canal'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Create / Edit Department Modal ─────────────────────────────────────────

interface DeptModalProps {
  dept?: Department
  onClose: () => void
  onSaved: () => void
}

function DeptModal({ dept, onClose, onSaved }: DeptModalProps) {
  const [name, setName] = useState(dept?.name ?? '')
  const [description, setDescription] = useState(dept?.description ?? '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const isEdit = !!dept

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return
    setSaving(true)
    setError('')
    try {
      if (isEdit) {
        await updateDepartment(dept.id, { name: name.trim(), description: description.trim() || null })
      } else {
        await createDepartment({ name: name.trim(), description: description.trim() || null })
      }
      onSaved()
    } catch {
      setError('Error al guardar el departamento.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-base font-semibold text-gray-900">
            {isEdit ? 'Editar departamento' : 'Nuevo departamento'}
          </h2>
          <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">{error}</p>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nombre <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50">Cancelar</button>
            <button type="submit" disabled={saving} className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50">
              {saving ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Manage Department Modal (Agentes + Canales tabs) ──────────────────────

interface ManageDeptModalProps {
  dept: Department
  onClose: () => void
}

function ManageDeptModal({ dept, onClose }: ManageDeptModalProps) {
  const [activeTab, setActiveTab] = useState<'agents' | 'channels'>('agents')

  // ── Agents state ──
  const [agents, setAgents] = useState<DepartmentAgent[]>([])
  const [allUsers, setAllUsers] = useState<AdminUser[]>([])
  const [selectedUserId, setSelectedUserId] = useState('')
  const [agentsLoading, setAgentsLoading] = useState(true)
  const [adding, setAdding] = useState(false)
  const [removingAgentId, setRemovingAgentId] = useState<string | null>(null)
  const [agentsError, setAgentsError] = useState('')

  // ── Channels state ──
  const [allChannels, setAllChannels] = useState<Channel[]>([])
  const [deptAgents, setDeptAgents] = useState<DepartmentAgent[]>([])
  const [selectedChannelId, setSelectedChannelId] = useState('')
  const [channelsLoading, setChannelsLoading] = useState(true)
  const [assigningChannel, setAssigningChannel] = useState(false)
  const [removingChannelId, setRemovingChannelId] = useState<string | null>(null)
  const [channelAgentSaving, setChannelAgentSaving] = useState<string | null>(null)
  const [channelsError, setChannelsError] = useState('')

  const loadAgents = () => {
    setAgentsLoading(true)
    Promise.all([
      getDepartmentAgents(dept.id),
      getAdminUsers(0, 100).then(r => r.items),
    ])
      .then(([agts, users]) => { setAgents(agts); setAllUsers(users) })
      .catch(() => setAgentsError('Error al cargar los datos.'))
      .finally(() => setAgentsLoading(false))
  }

  const loadChannels = () => {
    setChannelsLoading(true)
    Promise.all([
      getChannels(0, 100).then(r => r.items),
      getDepartmentAgents(dept.id),
    ])
      .then(([chs, agts]) => { setAllChannels(chs); setDeptAgents(agts) })
      .catch(() => setChannelsError('Error al cargar los canales.'))
      .finally(() => setChannelsLoading(false))
  }

  useEffect(() => { loadAgents(); loadChannels() }, [])

  // ── Agent handlers ──
  const assignedAgentIds = new Set(agents.map(a => a.id))
  const availableUsers = allUsers.filter(u => !assignedAgentIds.has(u.id) && u.is_active)

  const handleAddAgent = async () => {
    if (!selectedUserId) return
    setAdding(true)
    setAgentsError('')
    try {
      await addDepartmentAgent(dept.id, selectedUserId)
      setSelectedUserId('')
      loadAgents()
    } catch {
      setAgentsError('Error al agregar el agente.')
    } finally {
      setAdding(false)
    }
  }

  const handleRemoveAgent = async (userId: string) => {
    setRemovingAgentId(userId)
    setAgentsError('')
    try {
      await removeDepartmentAgent(dept.id, userId)
      loadAgents()
    } catch {
      setAgentsError('Error al quitar el agente.')
    } finally {
      setRemovingAgentId(null)
    }
  }

  // ── Channel handlers ──
  const deptChannels = allChannels.filter(c => c.department_id === dept.id)
  const freeChannels = allChannels.filter(c => c.department_id === null && c.is_active)

  const handleAssignChannel = async () => {
    if (!selectedChannelId) return
    setAssigningChannel(true)
    setChannelsError('')
    try {
      await updateChannel(selectedChannelId, { department_id: dept.id })
      setSelectedChannelId('')
      loadChannels()
    } catch {
      setChannelsError('Error al asignar el canal.')
    } finally {
      setAssigningChannel(false)
    }
  }

  const handleRemoveChannel = async (channelId: string) => {
    setRemovingChannelId(channelId)
    setChannelsError('')
    try {
      await updateChannel(channelId, { department_id: null })
      loadChannels()
    } catch {
      setChannelsError('Error al quitar el canal.')
    } finally {
      setRemovingChannelId(null)
    }
  }

  const handleChannelAgentChange = async (channelId: string, agentId: string) => {
    setChannelAgentSaving(channelId)
    setChannelsError('')
    try {
      await updateChannel(channelId, { agent_id: agentId || null })
      setAllChannels(prev => prev.map(c => c.id === channelId ? { ...c, agent_id: agentId || null } : c))
    } catch {
      setChannelsError('Error al asignar el agente al canal.')
    } finally {
      setChannelAgentSaving(null)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-base font-semibold text-gray-900">
            Gestionar — {dept.name}
          </h2>
          <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 border-b border-gray-200 px-6">
          {(['agents', 'channels'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-2 text-sm font-medium border-b-2 transition-colors -mb-px ${
                activeTab === tab
                  ? 'border-blue-600 text-blue-700'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab === 'agents' ? 'Agentes' : 'Canales'}
            </button>
          ))}
        </div>

        <div className="px-6 py-5 space-y-4 min-h-[260px]">
          {/* ── Agents tab ── */}
          {activeTab === 'agents' && (
            <>
              {agentsError && (
                <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">{agentsError}</p>
              )}
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                  Agentes actuales ({agents.length})
                </p>
                {agentsLoading ? (
                  <LoadingSpinner />
                ) : agents.length === 0 ? (
                  <p className="text-sm text-gray-400 italic">Sin agentes asignados</p>
                ) : (
                  <ul className="space-y-1 max-h-40 overflow-y-auto">
                    {agents.map(a => (
                      <li key={a.id} className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-gray-50">
                        <div className="min-w-0">
                          <p className="text-sm text-gray-900 truncate">{a.full_name}</p>
                          <p className="text-xs text-gray-400 truncate">{a.email}</p>
                        </div>
                        <button
                          onClick={() => handleRemoveAgent(a.id)}
                          disabled={removingAgentId === a.id}
                          className="ml-3 text-xs text-red-500 hover:text-red-700 shrink-0 disabled:opacity-50"
                        >
                          {removingAgentId === a.id ? '...' : 'Quitar'}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              {!agentsLoading && (
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                    Agregar agente
                  </p>
                  {availableUsers.length === 0 ? (
                    <p className="text-sm text-gray-400 italic">Todos los usuarios ya están asignados</p>
                  ) : (
                    <div className="flex gap-2">
                      <select
                        value={selectedUserId}
                        onChange={e => setSelectedUserId(e.target.value)}
                        className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">Seleccionar usuario...</option>
                        {availableUsers.map(u => (
                          <option key={u.id} value={u.id}>{u.full_name} ({u.email})</option>
                        ))}
                      </select>
                      <button
                        onClick={handleAddAgent}
                        disabled={!selectedUserId || adding}
                        className="px-3 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 shrink-0"
                      >
                        {adding ? '...' : 'Agregar'}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {/* ── Channels tab ── */}
          {activeTab === 'channels' && (
            <>
              {channelsError && (
                <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">{channelsError}</p>
              )}
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                  Canales asignados ({deptChannels.length})
                </p>
                {channelsLoading ? (
                  <LoadingSpinner />
                ) : deptChannels.length === 0 ? (
                  <p className="text-sm text-gray-400 italic">Sin canales asignados</p>
                ) : (
                  <ul className="space-y-2 max-h-52 overflow-y-auto">
                    {deptChannels.map(c => (
                      <li key={c.id} className="py-2 px-2 rounded bg-gray-50">
                        <div className="flex items-center justify-between mb-1.5">
                          <div className="min-w-0">
                            <p className="text-sm text-gray-900 truncate">{c.name}</p>
                            <p className="text-xs text-gray-400 capitalize">{c.channel_type}</p>
                          </div>
                          <button
                            onClick={() => handleRemoveChannel(c.id)}
                            disabled={removingChannelId === c.id}
                            className="ml-3 text-xs text-red-500 hover:text-red-700 shrink-0 disabled:opacity-50"
                          >
                            {removingChannelId === c.id ? '...' : 'Quitar'}
                          </button>
                        </div>
                        <div className="flex items-center gap-2">
                          <label className="text-xs text-gray-500 shrink-0">Agente:</label>
                          <select
                            value={c.agent_id ?? ''}
                            disabled={channelAgentSaving === c.id}
                            onChange={e => handleChannelAgentChange(c.id, e.target.value)}
                            className="flex-1 px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-400 disabled:opacity-50"
                          >
                            <option value="">Sin agente</option>
                            {deptAgents.map(a => (
                              <option key={a.id} value={a.id}>{a.full_name}</option>
                            ))}
                          </select>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              {!channelsLoading && (
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                    Agregar canal
                  </p>
                  {freeChannels.length === 0 ? (
                    <p className="text-sm text-gray-400 italic">No hay canales disponibles sin departamento</p>
                  ) : (
                    <div className="flex gap-2">
                      <select
                        value={selectedChannelId}
                        onChange={e => setSelectedChannelId(e.target.value)}
                        className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">Seleccionar canal...</option>
                        {freeChannels.map(c => (
                          <option key={c.id} value={c.id}>{c.name}</option>
                        ))}
                      </select>
                      <button
                        onClick={handleAssignChannel}
                        disabled={!selectedChannelId || assigningChannel}
                        className="px-3 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 shrink-0"
                      >
                        {assigningChannel ? '...' : 'Asignar'}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        <div className="px-6 pb-5 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Edit Channel Modal ─────────────────────────────────────────────────────

interface EditChannelModalProps {
  channel: Channel
  onClose: () => void
  onSaved: () => void
}

function EditChannelModal({ channel, onClose, onSaved }: EditChannelModalProps) {
  const [fromName, setFromName] = useState('')
  const [smtpHost, setSmtpHost] = useState('')
  const [smtpPort, setSmtpPort] = useState('')
  const [smtpUser, setSmtpUser] = useState('')
  const [smtpPassword, setSmtpPassword] = useState('')
  const [imapHost, setImapHost] = useState('')
  const [imapPort, setImapPort] = useState('')
  const [departmentId, setDepartmentId] = useState<string>(channel.department_id ?? '')
  const [agentId, setAgentId] = useState<string>(channel.agent_id ?? '')
  const [departments, setDepartments] = useState<Department[]>([])
  const [deptAgents, setDeptAgents] = useState<DepartmentAgent[]>([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getDepartments().then(setDepartments).catch(() => {})
  }, [])

  // Reload dept agents whenever department selection changes
  useEffect(() => {
    if (!departmentId) { setDeptAgents([]); return }
    getDepartmentAgents(departmentId).then(setDeptAgents).catch(() => setDeptAgents([]))
  }, [departmentId])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      const patch: Parameters<typeof updateChannel>[1] = {
        department_id: departmentId || null,
        agent_id: agentId || null,
      }
      // Only include config if the user filled in at least one config field
      const hasConfig = fromName || smtpHost || smtpPort || smtpUser || smtpPassword || imapHost || imapPort
      if (hasConfig) {
        patch.config = {
          from_name: fromName,
          smtp_host: smtpHost,
          smtp_port: smtpPort,
          smtp_user: smtpUser,
          smtp_password: smtpPassword,
          imap_host: imapHost,
          imap_port: imapPort,
        }
      }
      await updateChannel(channel.id, patch)
      onSaved()
    } catch {
      setError('Error al guardar los cambios.')
    } finally {
      setSaving(false)
    }
  }

  const configField = (label: string, value: string, setter: (v: string) => void, opts?: { type?: string; placeholder?: string }) => (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type={opts?.type ?? 'text'}
        value={value}
        onChange={e => setter(e.target.value)}
        placeholder={opts?.placeholder ?? 'Sin cambios'}
        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
    </div>
  )

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-screen overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-base font-semibold text-gray-900">Editar canal</h2>
          <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">{error}</p>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nombre del canal</label>
            <input
              type="text"
              value={channel.name}
              readOnly
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-md bg-gray-50 text-gray-500 cursor-not-allowed"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Departamento</label>
            <select
              value={departmentId}
              onChange={e => { setDepartmentId(e.target.value); setAgentId('') }}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Sin departamento</option>
              {departments.filter(d => d.is_active).map(d => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Agente responsable</label>
            {!departmentId ? (
              <p className="text-xs text-gray-400 italic">Asigna un departamento primero para seleccionar agente</p>
            ) : (
              <select
                value={agentId}
                onChange={e => setAgentId(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Sin agente asignado</option>
                {deptAgents.map(a => (
                  <option key={a.id} value={a.id}>{a.full_name}</option>
                ))}
              </select>
            )}
          </div>
          <p className="text-xs text-gray-400 italic">Deja en blanco los campos de configuración para no modificarlos.</p>
          {configField('Nombre remitente', fromName, setFromName, { placeholder: 'Sin cambios' })}
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide pt-1">Configuración SMTP (envío)</p>
          {configField('SMTP Host', smtpHost, setSmtpHost, { placeholder: 'Sin cambios' })}
          <div className="grid grid-cols-2 gap-3">
            {configField('Puerto SMTP', smtpPort, setSmtpPort)}
            {configField('Usuario SMTP', smtpUser, setSmtpUser)}
          </div>
          {configField('Contraseña SMTP', smtpPassword, setSmtpPassword, { type: 'password', placeholder: 'Sin cambios' })}
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide pt-1">Configuración IMAP (recepción)</p>
          <div className="grid grid-cols-2 gap-3">
            {configField('IMAP Host', imapHost, setImapHost)}
            {configField('Puerto IMAP', imapPort, setImapPort)}
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50">Cancelar</button>
            <button type="submit" disabled={saving} className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50">
              {saving ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────

const LIMIT = 20

export default function Admin() {
  const [activeTab, setActiveTab] = useState<Tab>('users')

  // Users
  const [users, setUsers] = useState<AdminUser[]>([])
  const [usersLoading, setUsersLoading] = useState(false)
  const [usersError, setUsersError] = useState<string | null>(null)
  const [showCreateUser, setShowCreateUser] = useState(false)
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null)
  const [userPage, setUserPage] = useState(1)
  const [userTotal, setUserTotal] = useState(0)

  // Channels
  const [channels, setChannels] = useState<Channel[]>([])
  const [channelsLoading, setChannelsLoading] = useState(false)
  const [channelsError, setChannelsError] = useState<string | null>(null)
  const [showCreateChannel, setShowCreateChannel] = useState(false)
  const [editingChannel, setEditingChannel] = useState<Channel | null>(null)
  const [channelPage, setChannelPage] = useState(1)
  const [channelTotal, setChannelTotal] = useState(0)

  // Departments
  const [depts, setDepts] = useState<Department[]>([])
  const [deptsLoading, setDeptsLoading] = useState(false)
  const [deptsError, setDeptsError] = useState<string | null>(null)
  const [showCreateDept, setShowCreateDept] = useState(false)
  const [editingDept, setEditingDept] = useState<Department | null>(null)
  const [managingDept, setManagingDept] = useState<Department | null>(null)

  // Account
  const [tenant, setTenant] = useState<Tenant | null>(null)
  const [tenantLoading, setTenantLoading] = useState(false)
  const [tenantError, setTenantError] = useState<string | null>(null)
  const [tenantName, setTenantName] = useState('')
  const [savingTenant, setSavingTenant] = useState(false)
  const [tenantSaved, setTenantSaved] = useState(false)

  const loadUsers = (page = 1) => {
    setUsersLoading(true)
    setUsersError(null)
    getAdminUsers((page - 1) * LIMIT, LIMIT)
      .then(({ items, total }) => { setUsers(items); setUserTotal(total) })
      .catch(() => setUsersError('No se pudieron cargar los usuarios. Verifica tu conexión.'))
      .finally(() => setUsersLoading(false))
  }

  const loadChannels = (page = 1) => {
    setChannelsLoading(true)
    setChannelsError(null)
    getChannels((page - 1) * LIMIT, LIMIT)
      .then(({ items, total }) => { setChannels(items); setChannelTotal(total) })
      .catch(() => setChannelsError('No se pudieron cargar los canales. Verifica tu conexión.'))
      .finally(() => setChannelsLoading(false))
  }

  const loadDepts = () => {
    setDeptsLoading(true)
    setDeptsError(null)
    getDepartments()
      .then(setDepts)
      .catch(() => setDeptsError('No se pudieron cargar los departamentos. Verifica tu conexión.'))
      .finally(() => setDeptsLoading(false))
  }

  const loadTenant = () => {
    setTenantLoading(true)
    setTenantError(null)
    getAdminTenant()
      .then(t => {
        setTenant(t)
        setTenantName(t.name)
      })
      .catch(() => setTenantError('No se pudieron cargar los datos de la cuenta. Verifica tu conexión.'))
      .finally(() => setTenantLoading(false))
  }

  useEffect(() => {
    if (activeTab === 'users') loadUsers(userPage)
  }, [activeTab, userPage])

  useEffect(() => {
    if (activeTab === 'channels') loadChannels(channelPage)
  }, [activeTab, channelPage])

  useEffect(() => {
    if (activeTab === 'departments') loadDepts()
  }, [activeTab])

  useEffect(() => {
    if (activeTab === 'account' && !tenant) loadTenant()
  }, [activeTab])

  const handleDeactivate = async (user: AdminUser) => {
    if (!confirm(`¿Desactivar al usuario ${user.full_name}?`)) return
    await deleteAdminUser(user.id)
    setUserPage(1)
    loadUsers(1)
  }

  const handleToggleDept = async (dept: Department) => {
    const action = dept.is_active ? 'desactivar' : 'activar'
    if (!confirm(`¿${action.charAt(0).toUpperCase() + action.slice(1)} el departamento "${dept.name}"?`)) return
    try {
      await updateDepartment(dept.id, { is_active: !dept.is_active })
      loadDepts()
    } catch {
      // ignore
    }
  }

  const handleSaveTenant = async (e: React.FormEvent) => {
    e.preventDefault()
    setSavingTenant(true)
    try {
      const updated = await updateAdminTenant({ name: tenantName })
      setTenant(updated)
      setTenantSaved(true)
      setTimeout(() => setTenantSaved(false), 2000)
    } finally {
      setSavingTenant(false)
    }
  }

  return (
    <div className="p-6 max-w-5xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Administración</h1>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200 mb-6">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px ${
              activeTab === tab.id
                ? 'border-blue-600 text-blue-700'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Users tab ── */}
      {activeTab === 'users' && (
        <>
          <div className="flex justify-end mb-4">
            <button
              onClick={() => setShowCreateUser(true)}
              className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
              Nuevo usuario
            </button>
          </div>
          {usersError && (
            <ErrorMessage message={usersError} onRetry={loadUsers} />
          )}
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            {usersLoading ? (
              <LoadingSpinner />
            ) : users.length === 0 ? (
              <div className="p-8 text-center text-sm text-gray-400">No hay usuarios</div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Nombre</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Email</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Rol</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Estado</th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-900">{u.full_name}</td>
                      <td className="px-4 py-3 text-gray-500">{u.email}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${ROLE_BADGE[u.role] ?? 'bg-gray-100 text-gray-600'}`}>
                          {ROLE_LABEL[u.role] ?? u.role}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${u.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-400'}`}>
                          {u.is_active ? 'Activo' : 'Inactivo'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => setEditingUser(u)}
                            className="text-xs text-blue-600 hover:text-blue-800"
                          >
                            Editar
                          </button>
                          {u.is_active && (
                            <button
                              onClick={() => handleDeactivate(u)}
                              className="text-xs text-red-500 hover:text-red-700"
                            >
                              Desactivar
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
          <Pagination total={userTotal} page={userPage} limit={LIMIT} onChange={setUserPage} />
          {showCreateUser && (
            <CreateUserModal
              onClose={() => setShowCreateUser(false)}
              onCreated={() => { setShowCreateUser(false); setUserPage(1); loadUsers(1) }}
            />
          )}
          {editingUser && (
            <EditUserModal
              user={editingUser}
              onClose={() => setEditingUser(null)}
              onSaved={() => { setEditingUser(null); loadUsers(userPage) }}
            />
          )}
        </>
      )}

      {/* ── Channels tab ── */}
      {activeTab === 'channels' && (
        <>
          <div className="flex justify-end mb-4">
            <button
              onClick={() => setShowCreateChannel(true)}
              className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
              Nuevo canal
            </button>
          </div>
          {channelsError && (
            <ErrorMessage message={channelsError} onRetry={loadChannels} />
          )}
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            {channelsLoading ? (
              <LoadingSpinner />
            ) : channels.length === 0 ? (
              <div className="p-8 text-center text-sm text-gray-400">No hay canales configurados</div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Nombre</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Tipo</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Estado</th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {channels.map(c => (
                    <tr key={c.id} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-900">{c.name}</td>
                      <td className="px-4 py-3 text-gray-600 capitalize">{c.channel_type}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${c.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-400'}`}>
                          {c.is_active ? 'Activo' : 'Inactivo'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => setEditingChannel(c)}
                          className="text-xs text-blue-600 hover:text-blue-800"
                        >
                          Editar
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
          <Pagination total={channelTotal} page={channelPage} limit={LIMIT} onChange={setChannelPage} />
          {showCreateChannel && (
            <CreateChannelModal
              onClose={() => setShowCreateChannel(false)}
              onCreated={() => { setShowCreateChannel(false); setChannelPage(1); loadChannels(1) }}
            />
          )}
          {editingChannel && (
            <EditChannelModal
              channel={editingChannel}
              onClose={() => setEditingChannel(null)}
              onSaved={() => { setEditingChannel(null); loadChannels(channelPage) }}
            />
          )}
        </>
      )}

      {/* ── Departments tab ── */}
      {activeTab === 'departments' && (
        <>
          <div className="flex justify-end mb-4">
            <button
              onClick={() => setShowCreateDept(true)}
              className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
              Nuevo departamento
            </button>
          </div>
          {deptsError && (
            <ErrorMessage message={deptsError} onRetry={loadDepts} />
          )}
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            {deptsLoading ? (
              <LoadingSpinner />
            ) : depts.length === 0 ? (
              <div className="p-8 text-center text-sm text-gray-400">No hay departamentos</div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Nombre</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Descripción</th>
                    <th className="text-center px-4 py-3 font-medium text-gray-600">Agentes</th>
                    <th className="text-center px-4 py-3 font-medium text-gray-600">Canales</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Estado</th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {depts.map(d => (
                    <tr key={d.id} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-900">{d.name}</td>
                      <td className="px-4 py-3 text-gray-500 max-w-[200px] truncate">
                        {d.description ?? <span className="text-gray-300">—</span>}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700">
                          {d.agent_count}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-xs font-medium bg-purple-50 text-purple-700">
                          {d.channel_count}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${d.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-400'}`}>
                          {d.is_active ? 'Activo' : 'Inactivo'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex justify-end gap-2 whitespace-nowrap">
                          <button
                            onClick={() => setManagingDept(d)}
                            className="text-xs text-blue-600 hover:text-blue-800"
                          >
                            Gestionar
                          </button>
                          <button
                            onClick={() => setEditingDept(d)}
                            className="text-xs text-blue-600 hover:text-blue-800"
                          >
                            Editar
                          </button>
                          <button
                            onClick={() => handleToggleDept(d)}
                            className={`text-xs ${d.is_active ? 'text-red-500 hover:text-red-700' : 'text-green-600 hover:text-green-800'}`}
                          >
                            {d.is_active ? 'Desactivar' : 'Activar'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
          {showCreateDept && (
            <DeptModal
              onClose={() => setShowCreateDept(false)}
              onSaved={() => { setShowCreateDept(false); loadDepts() }}
            />
          )}
          {editingDept && (
            <DeptModal
              dept={editingDept}
              onClose={() => setEditingDept(null)}
              onSaved={() => { setEditingDept(null); loadDepts() }}
            />
          )}
          {managingDept && (
            <ManageDeptModal
              dept={managingDept}
              onClose={() => { setManagingDept(null); loadDepts() }}
            />
          )}
        </>
      )}

      {/* ── Account tab ── */}
      {activeTab === 'account' && (
        <div className="max-w-md">
          {tenantError && (
            <ErrorMessage message={tenantError} onRetry={loadTenant} />
          )}
          {tenantLoading ? (
            <LoadingSpinner />
          ) : (
            <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
              <form onSubmit={handleSaveTenant} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nombre de la empresa
                  </label>
                  <input
                    type="text"
                    value={tenantName}
                    onChange={e => setTenantName(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Slug</label>
                  <input
                    type="text"
                    value={tenant?.slug ?? ''}
                    readOnly
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-md bg-gray-50 text-gray-500 cursor-not-allowed"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Plan</label>
                  <input
                    type="text"
                    value={tenant?.plan ?? ''}
                    readOnly
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-md bg-gray-50 text-gray-500 capitalize cursor-not-allowed"
                  />
                </div>
                <div className="flex items-center gap-3 pt-2">
                  <button
                    type="submit"
                    disabled={savingTenant}
                    className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {savingTenant ? 'Guardando...' : 'Guardar cambios'}
                  </button>
                  {tenantSaved && (
                    <span className="text-sm text-green-600">Guardado</span>
                  )}
                </div>
              </form>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
