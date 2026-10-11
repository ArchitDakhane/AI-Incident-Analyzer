import type { ReactNode } from 'react'
import { Paper, Stack, Typography } from '@mui/material'
import InboxIcon from '@mui/icons-material/Inbox'

interface EmptyStateProps {
  title: string
  message: string
  action?: ReactNode
}

export function EmptyState({ title, message, action }: EmptyStateProps) {
  return (
    <Paper variant="outlined" sx={{ borderRadius: 2, p: 4 }}>
      <Stack alignItems="center" spacing={1.5} textAlign="center">
        <InboxIcon color="disabled" />
        <Typography sx={{ fontWeight: 700 }}>{title}</Typography>
        <Typography color="text.secondary">{message}</Typography>
        {action}
      </Stack>
    </Paper>
  )
}
