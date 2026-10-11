import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import type { PaletteMode } from '@mui/material'

type SnackbarSeverity = 'success' | 'info' | 'warning' | 'error'

interface SnackbarState {
  open: boolean
  message: string
  severity: SnackbarSeverity
}

interface UIContextValue {
  mode: PaletteMode
  snackbar: SnackbarState
  toggleMode: () => void
  notify: (message: string, severity?: SnackbarSeverity) => void
  closeSnackbar: () => void
}

const UIContext = createContext<UIContextValue | undefined>(undefined)

export function UIProvider({ children }: { children: React.ReactNode }) {
  const [mode, setMode] = useState<PaletteMode>(() => {
    return (localStorage.getItem('ai_incident_color_mode') as PaletteMode) || 'light'
  })
  const [snackbar, setSnackbar] = useState<SnackbarState>({
    open: false,
    message: '',
    severity: 'info',
  })

  const toggleMode = useCallback(() => {
    setMode((currentMode) => {
      const nextMode = currentMode === 'light' ? 'dark' : 'light'
      localStorage.setItem('ai_incident_color_mode', nextMode)
      return nextMode
    })
  }, [])

  const notify = useCallback((message: string, severity: SnackbarSeverity = 'info') => {
    setSnackbar({ open: true, message, severity })
  }, [])

  const closeSnackbar = useCallback(() => {
    setSnackbar((current) => ({ ...current, open: false }))
  }, [])

  const value = useMemo(
    () => ({ mode, snackbar, toggleMode, notify, closeSnackbar }),
    [closeSnackbar, mode, notify, snackbar, toggleMode]
  )

  return <UIContext.Provider value={value}>{children}</UIContext.Provider>
}

export function useUI() {
  const context = useContext(UIContext)
  if (!context) {
    throw new Error('useUI must be used within UIProvider')
  }
  return context
}
