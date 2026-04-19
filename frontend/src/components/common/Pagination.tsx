interface PaginationProps {
  total: number
  page: number
  limit: number
  onChange: (page: number) => void
}

export default function Pagination({ total, page, limit, onChange }: PaginationProps) {
  const totalPages = Math.ceil(total / limit)

  if (totalPages <= 1) return null

  const from = (page - 1) * limit + 1
  const to = Math.min(page * limit, total)

  // Build the window of up to 5 page numbers centered around the current page
  const getPageNumbers = (): number[] => {
    if (totalPages <= 5) {
      return Array.from({ length: totalPages }, (_, i) => i + 1)
    }
    let start = Math.max(1, page - 2)
    const end = Math.min(totalPages, start + 4)
    // Slide window left if we're near the end
    start = Math.max(1, end - 4)
    return Array.from({ length: end - start + 1 }, (_, i) => start + i)
  }

  const pageNumbers = getPageNumbers()

  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
      <p className="text-sm text-gray-500">
        Mostrando <span className="font-medium text-gray-700">{from}–{to}</span>{' '}
        de <span className="font-medium text-gray-700">{total}</span> resultados
      </p>

      <div className="flex items-center gap-1">
        <button
          onClick={() => onChange(page - 1)}
          disabled={page === 1}
          className="px-3 py-1.5 text-sm rounded-md border border-gray-300 text-gray-600
                     hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed
                     transition-colors"
        >
          Anterior
        </button>

        {pageNumbers[0] > 1 && (
          <>
            <button
              onClick={() => onChange(1)}
              className="w-8 h-8 text-sm rounded-md border border-gray-300 text-gray-600 hover:bg-gray-50 transition-colors"
            >
              1
            </button>
            {pageNumbers[0] > 2 && (
              <span className="px-1 text-gray-400 text-sm">…</span>
            )}
          </>
        )}

        {pageNumbers.map((n) => (
          <button
            key={n}
            onClick={() => onChange(n)}
            className={`w-8 h-8 text-sm rounded-md border transition-colors ${
              n === page
                ? 'border-blue-600 bg-blue-600 text-white'
                : 'border-gray-300 text-gray-600 hover:bg-gray-50'
            }`}
          >
            {n}
          </button>
        ))}

        {pageNumbers[pageNumbers.length - 1] < totalPages && (
          <>
            {pageNumbers[pageNumbers.length - 1] < totalPages - 1 && (
              <span className="px-1 text-gray-400 text-sm">…</span>
            )}
            <button
              onClick={() => onChange(totalPages)}
              className="w-8 h-8 text-sm rounded-md border border-gray-300 text-gray-600 hover:bg-gray-50 transition-colors"
            >
              {totalPages}
            </button>
          </>
        )}

        <button
          onClick={() => onChange(page + 1)}
          disabled={page === totalPages}
          className="px-3 py-1.5 text-sm rounded-md border border-gray-300 text-gray-600
                     hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed
                     transition-colors"
        >
          Siguiente
        </button>
      </div>
    </div>
  )
}
