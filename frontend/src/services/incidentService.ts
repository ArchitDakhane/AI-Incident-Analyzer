
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

export async function listIncidents(
  params: IncidentQueryParams,
) {
  const response = await api.get<IncidentListResponse>(
    '/incidents',
    { params },
  )

  return response.data
}

export async function getIncident(id: number) {
  const response = await api.get<Incident>(
    `/incidents/${id}`,
  )

  return response.data
}

export async function createIncident(
  payload: IncidentFormValues,
) {
  const response = await api.post<Incident>(
    '/incidents',
    payload,
  )

  return response.data
}

export async function updateIncident(
  id: number,
  payload: Partial<IncidentFormValues>,
) {
  const response = await api.put<Incident>(
    `/incidents/${id}`,
    payload,
  )

  return response.data
}

export async function deleteIncident(id: number) {
  await api.delete(`/incidents/${id}`)
}

/**
 * Upload a log file for an incident.
 * The backend must accept a multipart/form-data field named "file".
 */
export async function uploadLogFile(
  id: number,
  file: File,
) {
  if (!Number.isInteger(id) || id < 1) {
    throw new Error('Invalid incident ID.')
  }

  if (!(file instanceof File)) {
    throw new Error('Please select a valid file.')
  }

  if (!file.name.toLowerCase().endsWith('.txt')) {
    throw new Error('Only .txt log files are supported.')
  }

  if (file.size === 0) {
    throw new Error('The selected file is empty.')
  }

  const formData = new FormData()
  formData.append('file', file, file.name)

  if (!formData.has('file')) {
    throw new Error('Unable to attach the selected file.')
  }

  console.debug('Uploading incident log:', {
    incidentId: id,
    fileName: file.name,
    fileSize: file.size,
    hasFile: formData.has('file'),
  })

  const response = await api.post<UploadResponse>(
    `/incidents/${id}/upload`,
    formData,
    {
      transformRequest: [(data) => data],
      headers: {
        'Content-Type': undefined,
      },
    },
  )

  return response.data
}

export async function getIncidentLogs(id: number) {
  const response = await api.get<UploadResponse[]>(
    `/incidents/${id}/logs`,
  )

  return response.data
}

export async function generateAIReport(
  id: number,
  logFileId?: number,
) {
  const response = await api.post<AIReport>(
    `/incidents/${id}/ai-report`,
    undefined,
    {
      params: logFileId
        ? { log_file_id: logFileId }
        : undefined,
    },
  )

  return response.data
}

export async function getSimilarIncidents(id: number) {
  const response = await api.get<SimilarIncidentListResponse>(
    `/incidents/${id}/similar`,
  )

  return response.data
}
