import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import type { AuthResponse, LoginRequest, RegisterRequest, User } from '../types'
import { getApiErrorMessage } from '../services/api'
import { getProfile, login, register, revokeRefreshToken } from '../services/authService'
import { clearSession, getAccessToken, getRefreshToken, getStoredUser, storeSession, storeUser } from '../services/storage'

interface AuthContextValue {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  loginUser: (payload: LoginRequest) => Promise<AuthResponse>
  registerUser: (payload: RegisterRequest) => Promise<AuthResponse>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(() => getStoredUser())
  const [error, setError] = useState<string | null>(null)
  const hasToken = Boolean(getAccessToken())

  const profileQuery = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: getProfile,
    enabled: hasToken,
    retry: false,
  })

  useEffect(() => {
    if (profileQuery.data) {
      setUser(profileQuery.data)
      storeUser(profileQuery.data)
    }
  }, [profileQuery.data])

  useEffect(() => {
    if (profileQuery.error) {
      clearSession()
      setUser(null)
    }
  }, [profileQuery.error])

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: (data) => {
      storeSession(data.access_token, data.refresh_token, data.user)
      setUser(data.user)
      setError(null)
    },
    onError: (mutationError) => {
      setError(getApiErrorMessage(mutationError))
    },
  })

  const registerMutation = useMutation({
    mutationFn: register,
    onSuccess: (data) => {
      storeSession(data.access_token, data.refresh_token, data.user)
      setUser(data.user)
      setError(null)
    },
    onError: (mutationError) => {
      setError(getApiErrorMessage(mutationError))
    },
  })

  const logout = useCallback(async () => {
    const refreshToken = getRefreshToken()
    if (refreshToken) {
      try {
        await revokeRefreshToken(refreshToken)
      } catch {
        // The local session is cleared even if the server cannot be reached.
      }
    }
    clearSession()
    setUser(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: Boolean(user && getAccessToken()),
      isLoading: profileQuery.isLoading || loginMutation.isPending || registerMutation.isPending,
      error,
      loginUser: loginMutation.mutateAsync,
      registerUser: registerMutation.mutateAsync,
      logout,
    }),
    [
      error,
      loginMutation.isPending,
      loginMutation.mutateAsync,
      logout,
      profileQuery.isLoading,
      registerMutation.isPending,
      registerMutation.mutateAsync,
      user,
    ]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
