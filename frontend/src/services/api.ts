
import axios, { AxiosError } from 'axios'
import type { ApiErrorPayload, TokenResponse } from '../types'
import {
  clearSession,
  getAccessToken,
  getRefreshToken,
  storeTokens,
} from './storage'

const baseURL = import.meta.env.VITE_API_BASE_URL ?? '/api'

export const api = axios.create({
  baseURL,
})

declare module 'axios' {
  interface InternalAxiosRequestConfig {
    _retry?: boolean
  }
}

let refreshPromise: Promise<string> | null = null

function refreshAccessToken(): Promise<string> {
  if (!refreshPromise) {
    const refreshToken = getRefreshToken()

    if (!refreshToken) {
      clearSession()
      return Promise.reject(new Error('Session expired'))
    }

    refreshPromise = axios
      .post<TokenResponse>(
        `${baseURL}/auth/refresh`,
        { refresh_token: refreshToken },
      )
      .then(({ data }) => {
        storeTokens(data.access_token, data.refresh_token)
        return data.access_token
      })
      .catch((error: unknown) => {
        clearSession()
        throw error
      })
      .finally(() => {
        refreshPromise = null
      })
  }

  return refreshPromise
}

api.interceptors.request.use((config) => {
  const token = getAccessToken()

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorPayload>) => {
    const request = error.config

    const isAuthEndpoint =
      /\/auth\/(login|register|refresh|logout)(?:$|\?)/.test(
        request?.url ?? '',
      )

    if (
      error.response?.status === 401 &&
      request &&
      !request._retry &&
      !isAuthEndpoint &&
      getAccessToken()
    ) {
      request._retry = true

      try {
        const token = await refreshAccessToken()

        request.headers.Authorization = `Bearer ${token}`

        return api.request(request)
      } catch {
        clearSession()
      }
    } else if (
      error.response?.status === 401 &&
      !isAuthEndpoint
    ) {
      clearSession()
    }

    return Promise.reject(error)
  },
)

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError<ApiErrorPayload>(error)) {
    const detail = error.response?.data?.detail

    if (typeof detail === 'string') {
      return detail
    }

    if (Array.isArray(detail) && detail.length > 0) {
      return detail
        .map((item) => item.msg ?? 'Validation error')
        .join(', ')
    }

    if (error.response?.data?.message) {
      return error.response.data.message
    }

    if (error.response?.statusText) {
      return error.response.statusText
    }
  }

  if (error instanceof Error) {
    return error.message
  }

  return 'Something went wrong'
}
