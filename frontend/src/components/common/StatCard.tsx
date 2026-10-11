import type { ReactNode } from 'react'
import { Paper, Stack, Typography } from '@mui/material'

interface StatCardProps {
  label: string
  value: number | string
  icon: ReactNode
  accent: string
}

export function StatCard({ label, value, icon, accent }: StatCardProps) {
  return (
    <Paper
      variant="outlined"
      sx={{
        borderRadius: 2,
        height: '100%',
        overflow: 'hidden',
        p: 2.25,
        position: 'relative',
      }}
    >
      <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
        <Stack
          sx={{
            alignItems: 'center',
            bgcolor: accent,
            borderRadius: 1.5,
            color: '#fff',
            height: 44,
            justifyContent: 'center',
            width: 44,
          }}
        >
          {icon}
        </Stack>
        <Stack spacing={0.25}>
          <Typography color="text.secondary" variant="body2">
            {label}
          </Typography>
          <Typography variant="h5" sx={{ fontWeight: 800, letterSpacing: 0 }}>
            {value}
          </Typography>
        </Stack>
      </Stack>
    </Paper>
  )
}
