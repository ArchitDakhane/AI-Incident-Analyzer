import { Alert, Snackbar } from '@mui/material'
import { useUI } from '../../contexts/UIContext'

export function GlobalSnackbar() {
  const { snackbar, closeSnackbar } = useUI()

  return (
    <Snackbar
      open={snackbar.open}
      autoHideDuration={4500}
      onClose={closeSnackbar}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
    >
      <Alert
        onClose={closeSnackbar}
        severity={snackbar.severity}
        variant="filled"
        sx={{ width: '100%' }}
      >
        {snackbar.message}
      </Alert>
    </Snackbar>
  )
}
