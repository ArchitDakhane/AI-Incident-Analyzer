import { Button, Paper, Stack, Typography } from '@mui/material'
import RefreshIcon from '@mui/icons-material/Refresh'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline'

interface ErrorStateProps {
  message: string
  onRetry?: () => void
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <Paper variant="outlined" sx={{ borderRadius: 2, p: 3 }}>
      <Stack alignItems="center" spacing={1.5} textAlign="center">
        <ErrorOutlineIcon color="error" />
        <Typography sx={{ fontWeight: 700 }}>Request failed</Typography>
        <Typography color="text.secondary">{message}</Typography>
        {onRetry ? (
          <Button startIcon={<RefreshIcon />} variant="outlined" onClick={onRetry}>
            Retry
          </Button>
        ) : null}
      </Stack>
    </Paper>
  )
}
