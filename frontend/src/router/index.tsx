import { createBrowserRouter, Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import MainLayout from '../layouts/MainLayout'
import AuthLayout from '../layouts/AuthLayout'
import Login from '../pages/Login'
import Dashboard from '../pages/Dashboard'
import Tickets from '../pages/Tickets'
import TicketDetail from '../pages/TicketDetail'
import Customers from '../pages/Customers'
import Reports from '../pages/Reports'
import Admin from '../pages/Admin'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return !isAuthenticated ? <>{children}</> : <Navigate to="/" replace />
}

export const router = createBrowserRouter([
  {
    path: '/login',
    element: (
      <PublicRoute>
        <AuthLayout>
          <Login />
        </AuthLayout>
      </PublicRoute>
    ),
  },
  {
    path: '/',
    element: (
      <PrivateRoute>
        <MainLayout />
      </PrivateRoute>
    ),
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'tickets', element: <Tickets /> },
      { path: 'tickets/:id', element: <TicketDetail /> },
      { path: 'customers', element: <Customers /> },
      { path: 'reports', element: <Reports /> },
      { path: 'admin', element: <Admin /> },
    ],
  },
])