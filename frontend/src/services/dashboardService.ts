import type { DashboardStats } from '../types'
import { api } from './api'

export async function getDashboardStats() {
  const response = await api.get<DashboardStats>('/dashboard/stats')
  return response.data
}
