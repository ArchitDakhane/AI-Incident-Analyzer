import { Chip } from '@mui/material'
import type { Severity } from '../../types'
import { titleCase } from '../../utils/formatters'

const severityColors: Record<string, 'default' | 'success' | 'warning' | 'error'> = {
  low: 'success',
  medium: 'default',
  high: 'warning',
  critical: 'error',
}

export function SeverityChip({ severity }: { severity: Severity | string }) {
  return (
    <Chip
      label={titleCase(severity)}
      color={severityColors[severity] ?? 'default'}
      size="small"
      variant={severity === 'medium' ? 'outlined' : 'filled'}
      sx={{ minWidth: 78 }}
    />
  )
}
