import { Chip } from '@mui/material'
import type { IncidentStatus } from '../../types'
import { titleCase } from '../../utils/formatters'

const statusColors: Record<string, 'default' | 'info' | 'success' | 'warning'> = {
  open: 'warning',
  investigating: 'info',
  resolved: 'success',
}

export function StatusChip({ status }: { status: IncidentStatus | string }) {
  return (
    <Chip
      label={titleCase(status)}
      color={statusColors[status] ?? 'default'}
      size="small"
      variant={status === 'open' ? 'filled' : 'outlined'}
      sx={{ minWidth: 104 }}
    />
  )
}
