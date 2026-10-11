import { CssBaseline, ThemeProvider, createTheme } from '@mui/material'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Navigate, Route, Routes, BrowserRouter } from 'react-router-dom'
import { useMemo } from 'react'
import { AuthProvider } from './contexts/AuthContext'
import { UIProvider, useUI } from './contexts/UIContext'
import { AppLayout } from './layouts/AppLayout'
import { AuthLayout } from './layouts/AuthLayout'
import { ProtectedRoute } from './components/common/ProtectedRoute'
import { GuestRoute } from './components/common/GuestRoute'
import { GlobalSnackbar } from './components/common/GlobalSnackbar'
import { DashboardPage } from './pages/DashboardPage'
import { IncidentListPage } from './pages/IncidentListPage'
import { CreateIncidentPage } from './pages/CreateIncidentPage'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { IncidentDetailPage } from './pages/IncidentDetailPage'
import { ProfilePage } from './pages/ProfilePage'
import './App.css'

// Create a client for React Query
const queryClient = new QueryClient()

function AppShell() {
  const { mode } = useUI()

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          primary: {
            main: '#2f6fed',
          },
          secondary: {
            main: '#8b5cf6',
          },
        },
        shape: {
          borderRadius: 12,
        },
        typography: {
          fontFamily: 'Inter, system-ui, sans-serif',
        },
      }),
    [mode]
  )

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <GlobalSnackbar />
      <BrowserRouter>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route index element={<DashboardPage />} />
              <Route path="incidents" element={<IncidentListPage />} />
              <Route path="incidents/new" element={<CreateIncidentPage />} />
              <Route path="incidents/:id" element={<IncidentDetailPage />} />
              <Route path="profile" element={<ProfilePage />} />
            </Route>
          </Route>

          <Route element={<GuestRoute />}>
            <Route element={<AuthLayout />}>
              <Route path="login" element={<LoginPage />} />
              <Route path="register" element={<RegisterPage />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <UIProvider>
          <AppShell />
        </UIProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
