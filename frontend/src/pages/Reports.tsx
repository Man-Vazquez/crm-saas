import { useEffect, useState } from 'react'
import { getMetricsByAgent, getMetricsByType, getMetricsByChannel } from '../api/tickets'
import type { TicketsByAgentItem, TicketsByTypeItem, TicketsByChannelItem } from '../types'
import ErrorMessage from '../components/common/ErrorMessage'
import LoadingSpinner from '../components/common/LoadingSpinner'

type Tab = 'agents' | 'types' | 'channels'

const TABS: { id: Tab; label: string }[] = [
  { id: 'agents', label: 'Por agente' },
  { id: 'types', label: 'Por tipificación' },
  { id: 'channels', label: 'Por canal' },
]

export default function Reports() {
  const [activeTab, setActiveTab] = useState<Tab>('agents')
  const [agents, setAgents] = useState<TicketsByAgentItem[]>([])
  const [types, setTypes] = useState<TicketsByTypeItem[]>([])
  const [channels, setChannels] = useState<TicketsByChannelItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = () => {
    setLoading(true)
    setError(null)
    Promise.all([getMetricsByAgent(), getMetricsByType(), getMetricsByChannel()])
      .then(([a, t, c]) => {
        setAgents(a)
        setTypes(t)
        setChannels(c)
      })
      .catch(() => setError('No se pudieron cargar los reportes. Verifica tu conexión.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadData()
  }, [])

  return (
    <div className="p-6 max-w-5xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Reportes</h1>
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

      {error && (
        <ErrorMessage message={error} onRetry={loadData} />
      )}

      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          {/* By agent */}
          {activeTab === 'agents' && (
            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
              {agents.length === 0 ? (
                <div className="p-8 text-center text-sm text-gray-400">Sin datos disponibles</div>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 bg-gray-50">
                      <th className="text-left px-4 py-3 font-medium text-gray-600">Agente</th>
                      <th className="text-right px-4 py-3 font-medium text-gray-600">Total</th>
                      <th className="text-right px-4 py-3 font-medium text-gray-600">Abiertos</th>
                      <th className="text-right px-4 py-3 font-medium text-gray-600">Resueltos</th>
                    </tr>
                  </thead>
                  <tbody>
                    {agents.map(a => (
                      <tr
                        key={a.agent_name}
                        className="border-b border-gray-100 last:border-0 hover:bg-gray-50"
                      >
                        <td className="px-4 py-3 font-medium text-gray-900">{a.agent_name}</td>
                        <td className="px-4 py-3 text-right text-gray-700">{a.total}</td>
                        <td className="px-4 py-3 text-right">
                          <span className="px-2 py-0.5 rounded-full text-xs bg-green-100 text-green-700">
                            {a.open}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span className="px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-700">
                            {a.resolved}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {/* By type */}
          {activeTab === 'types' && (
            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
              {types.length === 0 ? (
                <div className="p-8 text-center text-sm text-gray-400">Sin datos disponibles</div>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 bg-gray-50">
                      <th className="text-left px-4 py-3 font-medium text-gray-600">Tipo</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-600">Subtipo</th>
                      <th className="text-right px-4 py-3 font-medium text-gray-600">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {types.map((t, i) => (
                      <tr
                        key={i}
                        className="border-b border-gray-100 last:border-0 hover:bg-gray-50"
                      >
                        <td className="px-4 py-3 font-medium text-gray-900">{t.type_name}</td>
                        <td className="px-4 py-3 text-gray-500">{t.subtype_name ?? '—'}</td>
                        <td className="px-4 py-3 text-right text-gray-700">{t.count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {/* By channel */}
          {activeTab === 'channels' && (
            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
              {channels.length === 0 ? (
                <div className="p-8 text-center text-sm text-gray-400">Sin datos disponibles</div>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 bg-gray-50">
                      <th className="text-left px-4 py-3 font-medium text-gray-600">Canal</th>
                      <th className="text-right px-4 py-3 font-medium text-gray-600">Total tickets</th>
                    </tr>
                  </thead>
                  <tbody>
                    {channels.map(c => (
                      <tr
                        key={c.channel}
                        className="border-b border-gray-100 last:border-0 hover:bg-gray-50"
                      >
                        <td className="px-4 py-3 font-medium text-gray-900 capitalize">
                          {c.channel}
                        </td>
                        <td className="px-4 py-3 text-right text-gray-700">{c.count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
