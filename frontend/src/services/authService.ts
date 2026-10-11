import type { AuthResponse, LoginRequest, RegisterRequest, User } from '../types'
import { api } from './api'

export async function login(payload: LoginRequest) {
  const response = await api.post<AuthResponse>('/auth/login', payload)
  return response.data
}

export async function register(payload: RegisterRequest) {
  const response = await api.post<AuthResponse>('/auth/register', payload)
  return response.data
}

export async function getProfile() {
  const response = await api.get<User>('/auth/me')
  return response.data
}

export async function revokeRefreshToken(refreshToken: string) {
  await api.post<void>('/auth/logout', { refresh_token: refreshToken })
}
