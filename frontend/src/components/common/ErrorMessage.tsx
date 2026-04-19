interface ErrorMessageProps {
  message?: string
  onRetry?: () => void
}

export default function ErrorMessage({
  message = 'Ocurrió un error inesperado.',
  onRetry,
}: ErrorMessageProps) {
  return (
    <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
      <svg
        className="w-5 h-5 text-red-500 mt-0.5 shrink-0"
        viewBox="0 0 20 20"
        fill="currentColor"
        aria-hidden="true"
      >
        <path
          fillRule="evenodd"
          d="M10 18a8 8 0 100-16 8 8 0 000 16zm-.75-11.25a.75.75 0 011.5 0v4.5a.75.75 0 01-1.5 0v-4.5zm.75 7.5a.75.75 0 100-1.5.75.75 0 000 1.5z"
          clipRule="evenodd"
        />
      </svg>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-red-700">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-2 text-sm font-medium text-red-700 underline hover:text-red-900"
          >
            Reintentar
          </button>
        )}
      </div>
    </div>
  )
}
