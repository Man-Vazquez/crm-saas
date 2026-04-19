import { useEffect, useState } from 'react'
import {
  getAdminUsers,
  createAdminUser,
  updateAdminUser,
  deleteAdminUser,
  getAdminTenant,
  updateAdminTenant,
} from '../api/admin'
import { getChannels, createChannel } from '../api/channels'
import type { AdminUser, Channel, Tenant } from '../types'
import ErrorMessage from '../components/common/ErrorMessage'
import LoadingSpinner from '../components/common/LoadingSpinner'

type Tab = 'users' | 'channels' | 'account'

const TABS: { id: Tab; label: string }[] = [
  { id: 'users', label: 'Usuarios' },
  { id: 'channels', label: 'Canales' },
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
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

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

// ── Main page ──────────────────────────────────────────────────────────────

export default function Admin() {
  const [activeTab, setActiveTab] = useState<Tab>('users')

  // Users
  const [users, setUsers] = useState<AdminUser[]>([])
  const [usersLoading, setUsersLoading] = useState(false)
  const [usersError, setUsersError] = useState<string | null>(null)
  const [showCreateUser, setShowCreateUser] = useState(false)
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null)

  // Channels
  const [channels, setChannels] = useState<Channel[]>([])
  const [channelsLoading, setChannelsLoading] = useState(false)
  const [channelsError, setChannelsError] = useState<string | null>(null)
  const [showCreateChannel, setShowCreateChannel] = useState(false)

  // Account
  const [tenant, setTenant] = useState<Tenant | null>(null)
  const [tenantLoading, setTenantLoading] = useState(false)
  const [tenantError, setTenantError] = useState<string | null>(null)
  const [tenantName, setTenantName] = useState('')
  const [savingTenant, setSavingTenant] = useState(false)
  const [tenantSaved, setTenantSaved] = useState(false)

  const loadUsers = () => {
    setUsersLoading(true)
    setUsersError(null)
    getAdminUsers()
      .then(setUsers)
      .catch(() => setUsersError('No se pudieron cargar los usuarios. Verifica tu conexión.'))
      .finally(() => setUsersLoading(false))
  }

  const loadChannels = () => {
    setChannelsLoading(true)
    setChannelsError(null)
    getChannels()
      .then(setChannels)
      .catch(() => setChannelsError('No se pudieron cargar los canales. Verifica tu conexión.'))
      .finally(() => setChannelsLoading(false))
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
    if (activeTab === 'users' && users.length === 0) loadUsers()
    if (activeTab === 'channels' && channels.length === 0) loadChannels()
    if (activeTab === 'account' && !tenant) loadTenant()
  }, [activeTab])

  const handleDeactivate = async (user: AdminUser) => {
    if (!confirm(`¿Desactivar al usuario ${user.full_name}?`)) return
    await deleteAdminUser(user.id)
    loadUsers()
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
          {showCreateUser && (
            <CreateUserModal
              onClose={() => setShowCreateUser(false)}
              onCreated={() => { setShowCreateUser(false); loadUsers() }}
            />
          )}
          {editingUser && (
            <EditUserModal
              user={editingUser}
              onClose={() => setEditingUser(null)}
              onSaved={() => { setEditingUser(null); loadUsers() }}
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
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
          {showCreateChannel && (
            <CreateChannelModal
              onClose={() => setShowCreateChannel(false)}
              onCreated={() => { setShowCreateChannel(false); loadChannels() }}
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
