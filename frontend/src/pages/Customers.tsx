import { useEffect, useState } from 'react'
import { getCustomers } from '../api/customers'
import type { Customer } from '../types'
import Pagination from '../components/common/Pagination'

const LIMIT = 20

export default function Customers() {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  const loadCustomers = (currentPage: number) => {
    setLoading(true)
    getCustomers({
      skip: (currentPage - 1) * LIMIT,
      limit: LIMIT,
      search: search || undefined,
    })
      .then((res) => {
        setCustomers(res.items)
        setTotal(res.total)
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    setPage(1)
    loadCustomers(1)
  }, [search])

  useEffect(() => {
    loadCustomers(page)
  }, [page])

  const handlePageChange = (newPage: number) => {
    setPage(newPage)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Clientes</h1>
          <p className="text-sm text-gray-500 mt-0.5">{total} clientes en total</p>
        </div>
      </div>

      <div className="flex gap-3 mb-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar por nombre..."
          className="px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 w-64"
        />
      </div>

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-sm text-gray-500">Cargando...</div>
        ) : customers.length === 0 ? (
          <div className="p-8 text-center text-sm text-gray-500">No hay clientes</div>
        ) : (
          <>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Nombre</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Email</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Teléfono</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Empresa</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Fecha</th>
                </tr>
              </thead>
              <tbody>
                {customers.map((customer) => (
                  <tr
                    key={customer.id}
                    className="border-b border-gray-100 hover:bg-gray-50 transition-colors last:border-0"
                  >
                    <td className="px-4 py-3 font-medium text-gray-900">{customer.full_name}</td>
                    <td className="px-4 py-3 text-gray-600">{customer.email ?? '—'}</td>
                    <td className="px-4 py-3 text-gray-600">{customer.phone ?? '—'}</td>
                    <td className="px-4 py-3 text-gray-600">{customer.company ?? '—'}</td>
                    <td className="px-4 py-3 text-gray-500">
                      {new Date(customer.created_at).toLocaleDateString('es-MX')}
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