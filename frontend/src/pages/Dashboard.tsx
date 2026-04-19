import { useEffect, useState } from 'react'
import {
  ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell,
  PieChart, Pie, Legend,
  AreaChart, Area,
} from 'recharts'
import {
  getMetricsSummary,
  getMetricsByStatus,
  getMetricsByPriority,
  getMetricsDaily,
} from '../api/tickets'
import type {
  DashboardSummary,
  TicketsByStatusItem,
  TicketsByPriorityItem,
  DailyTicketsItem,
} from '../types'

const PRIORITY_COLOR: Record<string, string> = {
  low: '#9CA3AF',
  medium: '#F59E0B',
  high: '#F97316',
  urgent: '#EF4444',
}

const PRIORITY_LABEL: Record<string, string> = {
  low: 'Baja',
  medium: 'Media',
  high: 'Alta',
  urgent: 'Urgente',
}

function SummaryCard({
  label,
  value,
  accent,
}: {
  label: string
  value: string | number
  accent: string
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">{label}</p>
      <p className={`text-3xl font-bold ${accent}`}>{value}</p>
    </div>
  )
}

export default function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [byStatus, setByStatus] = useState<TicketsByStatusItem[]>([])
  const [byPriority, setByPriority] = useState<TicketsByPriorityItem[]>([])
  const [daily, setDaily] = useState<DailyTicketsItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    Promise.all([
      getMetricsSummary(),
      getMetricsByStatus(),
      getMetricsByPriority(),
      getMetricsDaily(),
    ])
      .then(([s, st, p, d]) => {
        setSummary(s)
        setByStatus(st)
        setByPriority(p)
        setDaily(d)
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="p-6">
        <div className="h-6 w-32 bg-gray-200 rounded animate-pulse mb-6" />
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-200 rounded-lg animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-2 gap-6 mb-6">
          <div className="h-48 bg-gray-200 rounded-lg animate-pulse" />
          <div className="h-48 bg-gray-200 rounded-lg animate-pulse" />
        </div>
        <div className="h-40 bg-gray-200 rounded-lg animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md px-4 py-3">
          Error al cargar el dashboard. Verifica tu conexión e intenta de nuevo.
        </p>
      </div>
    )
  }

  // Pie data needs a `name` field for the Legend
  const pieData = byPriority.map(p => ({
    name: PRIORITY_LABEL[p.priority] ?? p.priority,
    value: p.count,
    priority: p.priority,
  }))

  // Daily: shorten date label to MM-DD for axis
  const dailyData = daily.map(d => ({ ...d, label: d.date.slice(5) }))

  return (
    <div className="p-6 max-w-6xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
      </div>

      {/* Row 1 — Summary cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 mb-6">
        <SummaryCard
          label="Tickets abiertos"
          value={summary?.total_open ?? 0}
          accent="text-green-600"
        />
        <SummaryCard
          label="En progreso"
          value={summary?.total_in_progress ?? 0}
          accent="text-blue-600"
        />
        <SummaryCard
          label="Resueltos"
          value={summary?.total_resolved ?? 0}
          accent="text-purple-600"
        />
        <SummaryCard
          label="Tiempo prom. resolución"
          value={
            summary?.avg_resolution_hours != null
              ? `${summary.avg_resolution_hours}h`
              : '—'
          }
          accent="text-gray-700"
        />
      </div>

      {/* Row 2 — Status BarChart + Priority PieChart */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        {/* Tickets por estado */}
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <h2 className="text-sm font-medium text-gray-700 mb-4">Tickets por estado</h2>
          {byStatus.length === 0 ? (
            <p className="text-sm text-gray-400">Sin datos disponibles</p>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={byStatus} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis
                  dataKey="status_name"
                  tick={{ fontSize: 11, fill: '#6B7280' }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  allowDecimals={false}
                  tick={{ fontSize: 11, fill: '#6B7280' }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  formatter={(value: number) => [value, 'Tickets']}
                  contentStyle={{ fontSize: 12, borderRadius: 6, border: '1px solid #E5E7EB' }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {byStatus.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Tickets por prioridad */}
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <h2 className="text-sm font-medium text-gray-700 mb-4">Tickets por prioridad</h2>
          {pieData.length === 0 ? (
            <p className="text-sm text-gray-400">Sin datos disponibles</p>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={95}
                  paddingAngle={2}
                >
                  {pieData.map((entry, i) => (
                    <Cell key={i} fill={PRIORITY_COLOR[entry.priority] ?? '#6B7280'} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number) => [value, 'Tickets']}
                  contentStyle={{ fontSize: 12, borderRadius: 6, border: '1px solid #E5E7EB' }}
                />
                <Legend
                  iconType="circle"
                  iconSize={8}
                  formatter={(value) => (
                    <span style={{ fontSize: 12, color: '#374151' }}>{value}</span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Row 3 — Daily AreaChart */}
      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <h2 className="text-sm font-medium text-gray-700 mb-4">
          Tickets creados — últimos 30 días
        </h2>
        {dailyData.length === 0 ? (
          <p className="text-sm text-gray-400">Sin datos disponibles</p>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={dailyData} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
              <defs>
                <linearGradient id="blueGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 11, fill: '#6B7280' }}
                tickLine={false}
                axisLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                allowDecimals={false}
                tick={{ fontSize: 11, fill: '#6B7280' }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                formatter={(value: number) => [value, 'Tickets']}
                labelFormatter={(label) => `Fecha: ${label}`}
                contentStyle={{ fontSize: 12, borderRadius: 6, border: '1px solid #E5E7EB' }}
              />
              <Area
                type="monotone"
                dataKey="count"
                stroke="#3B82F6"
                strokeWidth={2}
                fill="url(#blueGradient)"
                dot={false}
                activeDot={{ r: 4, fill: '#3B82F6' }}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
