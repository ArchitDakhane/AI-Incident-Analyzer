import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider, createTheme } from '@mui/material'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { AuthResponse, Incident, SimilarIncidentListResponse, UploadResponse } from '../src/types'
import { LoginPage } from '../src/pages/LoginPage'
import { CreateIncidentPage } from '../src/pages/CreateIncidentPage'
import { IncidentDetailPage } from '../src/pages/IncidentDetailPage'

const mocks = vi.hoisted(() => ({
  loginUser: vi.fn(),
  notify: vi.fn(),
  createIncident: vi.fn(),
  getIncident: vi.fn(),
  getIncidentLogs: vi.fn(),
  getSimilarIncidents: vi.fn(),
  generateAIReport: vi.fn(),
  updateIncident: vi.fn(),
  uploadLogFile: vi.fn(),
}))

vi.mock('../src/contexts/AuthContext', () => ({
  useAuth: () => ({
    loginUser: mocks.loginUser,
    isLoading: false,
    error: null,
    user: null,
    isAuthenticated: false,
    registerUser: vi.fn(),
    logout: vi.fn(),
  }),
}))

vi.mock('../src/contexts/UIContext', () => ({
  useUI: () => ({ notify: mocks.notify, mode: 'light', toggleMode: vi.fn() }),
}))

vi.mock('../src/services/api', () => ({
  api: { post: vi.fn().mockResolvedValue(undefined) },
  getApiErrorMessage: (error: unknown) => error instanceof Error ? error.message : 'Request failed',
}))

vi.mock('../src/services/incidentService', () => ({
  createIncident: mocks.createIncident,
  getIncident: mocks.getIncident,
  getIncidentLogs: mocks.getIncidentLogs,
  getSimilarIncidents: mocks.getSimilarIncidents,
  generateAIReport: mocks.generateAIReport,
  updateIncident: mocks.updateIncident,
  uploadLogFile: mocks.uploadLogFile,
}))

function renderRoute(path: string, route: string, element: React.ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={createTheme()}>
        <MemoryRouter
          future={{ v7_relativeSplatPath: true, v7_startTransition: true }}
          initialEntries={[path]}
        >
          <Routes>
            <Route path={route} element={element} />
            <Route path="*" element={<div />} />
          </Routes>
        </MemoryRouter>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

const incident: Incident = {
  id: 42,
  title: 'Checkout API outage',
  incident_type: 'availability',
  severity: 'high',
  status: 'open',
  description: 'Requests time out',
  summary: null,
  created_at: '2026-10-10T10:00:00Z',
  updated_at: '2026-10-10T10:00:00Z',
  created_by_id: 7,
}

const uploadedLog: UploadResponse = {
  id: 91,
  filename: 'incident_42_unique_app.txt',
  original_filename: 'app.txt',
  file_type: 'txt',
  size_bytes: 128,
  uploaded_at: '2026-10-10T10:00:00Z',
  incident_id: 42,
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.loginUser.mockResolvedValue({} as AuthResponse)
  mocks.createIncident.mockResolvedValue(incident)
  mocks.getIncident.mockResolvedValue(incident)
  mocks.getIncidentLogs.mockResolvedValue([])
  mocks.getSimilarIncidents.mockResolvedValue({ items: [] } as SimilarIncidentListResponse)
  mocks.uploadLogFile.mockResolvedValue(uploadedLog)
  mocks.updateIncident.mockResolvedValue(incident)
})

describe('core application pages', () => {
  it('submits login credentials and shows the sign-in confirmation', async () => {
    const user = userEvent.setup()
    renderRoute('/login', '/login', <LoginPage />)

    await user.type(screen.getByLabelText(/Email/), 'analyst@example.com')
    await user.type(screen.getByLabelText(/Password/), 'safe-password')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    await waitFor(() => expect(mocks.loginUser).toHaveBeenCalledWith({
      email: 'analyst@example.com',
      password: 'safe-password',
    }))
    expect(mocks.notify).toHaveBeenCalledWith('Signed in', 'success')
  })

  it('creates an incident from the incident form', async () => {
    const user = userEvent.setup()
    renderRoute('/incidents/new', '/incidents/new', <CreateIncidentPage />)

    await user.type(screen.getByLabelText(/Title/), 'Checkout API outage')
    await user.type(screen.getByLabelText(/Description/), 'Requests timing out')
    await user.click(screen.getByRole('button', { name: 'Create Incident' }))

    await waitFor(() =>
      expect(mocks.createIncident.mock.calls[0]?.[0]).toEqual(
        expect.objectContaining({
          title: 'Checkout API outage',
          description: 'Requests timing out',
        })
      )
    )
  })

  it('uploads a selected .txt log through the incident upload service', async () => {
    const user = userEvent.setup()
    mocks.getIncidentLogs.mockResolvedValue([uploadedLog])
    renderRoute('/incidents/42', '/incidents/:id', <IncidentDetailPage />)

    const file = new File(['database timeout'], 'app.txt', { type: 'text/plain' })
    await user.upload(await screen.findByLabelText('Upload .txt log'), file)

    await waitFor(() => expect(mocks.uploadLogFile).toHaveBeenCalledWith(42, file))
    await waitFor(() => expect(mocks.getIncidentLogs).toHaveBeenCalledWith(42))
    expect(mocks.notify).toHaveBeenCalledWith(
      'Log file uploaded. Sensitive values are redacted before AI analysis.',
      'success'
    )
  })

  it('renders a generated AI report with findings and actions', async () => {
    const user = userEvent.setup()
    mocks.getIncidentLogs.mockResolvedValue([uploadedLog])
    mocks.generateAIReport.mockResolvedValue({
      id: 3,
      incident_id: 42,
      model_name: 'gemini-test',
      analysis_type: 'incident_summary',
      summary: 'The database connection timed out.',
      findings: ['Connection pool exhausted'],
      recommended_actions: ['Increase pool capacity'],
      confidence_score: 0.9,
      embedding_id: null,
      created_at: '2026-10-10T10:00:00Z',
      created_by_id: 7,
    })
    renderRoute('/incidents/42', '/incidents/:id', <IncidentDetailPage />)

    await user.click(await screen.findByRole('button', { name: 'Generate AI report' }))

    expect(await screen.findByText('The database connection timed out.')).toBeInTheDocument()
    expect(screen.getByText('Connection pool exhausted')).toBeInTheDocument()
    expect(screen.getByText('Increase pool capacity')).toBeInTheDocument()
    expect(mocks.generateAIReport).toHaveBeenCalledWith(42, 91)
  })
})
