import type {
  AIReport,
  Incident,
  IncidentFormValues,
  IncidentListResponse,
  SimilarIncidentListResponse,
  UploadResponse,
} from '../types'
import { api } from './api'

export interface IncidentQueryParams {
  page: number
  size: number
  search?: string
  severity?: string
  status?: string
  sort_by?: string
  sort_order?: string
}

export async function listIncidents(params: IncidentQueryParams) {
  const response = await api.get<IncidentListResponse>('/incidents', { params })
  return response.data
}

export async function getIncident(id: number) {
  const response = await api.get<Incident>(`/incidents/${id}`)
  return response.data
}

export async function createIncident(payload: IncidentFormValues) {
  const response = await api.post<Incident>('/incidents', payload)
  return response.data
}

export async function updateIncident(id: number, payload: Partial<IncidentFormValues>) {
  const response = await api.put<Incident>(`/incidents/${id}`, payload)
  return response.data
}

export async function deleteIncident(id: number) {
  await api.delete(`/incidents/${id}`)
}

export async function uploadLogFile(id: number, file: File) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post<UploadResponse>(`/incidents/${id}/upload`, formData)
  return response.data
}

export async function getIncidentLogs(id: number) {
  const response = await api.get<UploadResponse[]>(`/incidents/${id}/logs`)
  return response.data
}

export async function generateAIReport(id: number, logFileId?: number) {
  const response = await api.post<AIReport>(
    `/incidents/${id}/ai-report`,
    undefined,
    { params: logFileId ? { log_file_id: logFileId } : undefined }
  )
  return response.data
}

export async function getSimilarIncidents(id: number) {
  const response = await api.get<SimilarIncidentListResponse>(`/incidents/${id}/similar`)
  return response.data
}
