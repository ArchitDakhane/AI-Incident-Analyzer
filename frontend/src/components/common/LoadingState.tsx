import { Box, CircularProgress, Typography } from '@mui/material'

export function LoadingState({ label = 'Loading' }: { label?: string }) {
  return (
    <Box
      sx={{
        alignItems: 'center',
        display: 'flex',
        gap: 1.5,
        justifyContent: 'center',
        minHeight: 240,
      }}
    >
      <CircularProgress size={24} />
      <Typography color="text.secondary">{label}</Typography>
    </Box>
  )
}
