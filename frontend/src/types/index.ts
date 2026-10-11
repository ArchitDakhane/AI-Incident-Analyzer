export type Severity = 'low' | 'medium' | 'high' | 'critical'

export type IncidentStatus = 'open' | 'investigating' | 'resolved'

export interface User {
  id: number
  email: string
  username: string
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
}

export interface AuthResponse {
  user: User
  access_token: string
  refresh_token: string
  token_type: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
  full_name?: string
}

export interface Incident {
  id: number
  title: string
  incident_type: string | null
  severity: Severity | string
  status: IncidentStatus | string
  description: string | null
  summary: string | null
  created_at: string
  updated_at: string
  created_by_id: number | null
}

export interface IncidentListResponse {
  items: Incident[]
  total: number
  page: number
  size: number
}

export interface IncidentFormValues {
  title: string
  incident_type?: string
  severity: Severity
  status: IncidentStatus
  description?: string
  summary?: string
}

export interface UploadResponse {
  id: number
  filename: string
  original_filename: string
  file_type: string | null
  size_bytes: number | null
  uploaded_at: string
  incident_id: number | null
}

export interface AIReport {
  id: number
  incident_id: number
  model_name: string
  analysis_type: string
  summary: string
  findings: string[]
  recommended_actions: string[]
  confidence_score: number | null
  embedding_id: string | null
  created_at: string
  created_by_id: number | null
}

export interface SimilarIncident {
  incident_id: number
  title: string
  similarity_score: number
  root_cause: string
  resolution_summary: string
}

export interface SimilarIncidentListResponse {
  items: SimilarIncident[]
}

export interface DashboardStats {
  total_incidents: number
  open_incidents: number
  critical_incidents: number
  resolved_incidents: number
  total_ai_reports: number
  active_users: number
}

export interface ApiErrorPayload {
  detail?: string | { msg?: string }[]
  message?: string
}
