import { Link as RouterLink } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Button,
  Grid,
  Paper,
  Skeleton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'
import AnalyticsOutlinedIcon from '@mui/icons-material/AnalyticsOutlined'
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline'
import FolderOpenOutlinedIcon from '@mui/icons-material/FolderOpenOutlined'
import ReportProblemOutlinedIcon from '@mui/icons-material/ReportProblemOutlined'
import SmartToyOutlinedIcon from '@mui/icons-material/SmartToyOutlined'
import { ErrorState } from '../components/common/ErrorState'
import { EmptyState } from '../components/common/EmptyState'
import { PageHeader } from '../components/common/PageHeader'
import { StatCard } from '../components/common/StatCard'
import { SeverityChip } from '../components/incident/SeverityChip'
import { StatusChip } from '../components/incident/StatusChip'
import { getApiErrorMessage } from '../services/api'
import { getDashboardStats } from '../services/dashboardService'
import { listIncidents } from '../services/incidentService'
import { formatCompactDate } from '../utils/formatters'

export function DashboardPage() {
  const statsQuery = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: getDashboardStats,
  })

  const recentQuery = useQuery({
    queryKey: ['incidents', 'recent'],
    queryFn: () =>
      listIncidents({
        page: 1,
        size: 5,
        sort_by: 'created_at',
        sort_order: 'desc',
      }),
  })

  const stats = statsQuery.data

  return (
    <Box>
      <PageHeader
        title="Dashboard"
        subtitle="Operational incident overview"
        actions={
          <Button
            component={RouterLink}
            startIcon={<AddCircleOutlineIcon />}
            to="/incidents/new"
            variant="contained"
          >
            New Incident
          </Button>
        }
      />

      {statsQuery.isError ? (
        <ErrorState
          message={getApiErrorMessage(statsQuery.error)}
          onRetry={() => void statsQuery.refetch()}
        />
      ) : (
        <Grid container spacing={2.5}>
          {[
            {
              label: 'Total Incidents',
              value: stats?.total_incidents,
              icon: <FolderOpenOutlinedIcon />,
              accent: '#2f6fed',
            },
            {
              label: 'Open',
              value: stats?.open_incidents,
              icon: <ReportProblemOutlinedIcon />,
              accent: '#d97706',
            },
            {
              label: 'Critical',
              value: stats?.critical_incidents,
              icon: <ErrorOutlineIcon />,
              accent: '#dc2626',
            },
            {
              label: 'Resolved',
              value: stats?.resolved_incidents,
              icon: <CheckCircleOutlineIcon />,
              accent: '#15803d',
            },
            {
              label: 'AI Reports',
              value: stats?.total_ai_reports,
              icon: <SmartToyOutlinedIcon />,
              accent: '#7c3aed',
            },
            {
              label: 'Active Users',
              value: stats?.active_users,
              icon: <AnalyticsOutlinedIcon />,
              accent: '#0f766e',
            },
          ].map((item) => (
            <Grid item key={item.label} xs={12} sm={6} lg={4}>
              {statsQuery.isLoading ? (
                <Skeleton height={92} sx={{ borderRadius: 2 }} variant="rounded" />
              ) : (
                <StatCard
                  accent={item.accent}
                  icon={item.icon}
                  label={item.label}
                  value={item.value ?? 0}
                />
              )}
            </Grid>
          ))}
        </Grid>
      )}

      <Paper variant="outlined" sx={{ borderRadius: 2, mt: 3, overflow: 'hidden' }}>
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          spacing={1.5}
          sx={{
            alignItems: { xs: 'stretch', sm: 'center' },
            borderBottom: 1,
            borderColor: 'divider',
            justifyContent: 'space-between',
            p: 2,
          }}
        >
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 800 }}>
              Recent Incidents
            </Typography>
            <Typography color="text.secondary" variant="body2">
              Latest records by creation time
            </Typography>
          </Box>
          <Button component={RouterLink} to="/incidents" variant="outlined">
            View all
          </Button>
        </Stack>

        {recentQuery.isLoading ? (
          <Stack spacing={1} sx={{ p: 2 }}>
            {[0, 1, 2, 3, 4].map((item) => (
              <Skeleton key={item} height={48} variant="rounded" />
            ))}
          </Stack>
        ) : recentQuery.isError ? (
          <Box sx={{ p: 2 }}>
            <ErrorState
              message={getApiErrorMessage(recentQuery.error)}
              onRetry={() => void recentQuery.refetch()}
            />
          </Box>
        ) : recentQuery.data?.items.length ? (
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Title</TableCell>
                <TableCell>Severity</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Created</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {recentQuery.data.items.map((incident) => (
                <TableRow
                  hover
                  key={incident.id}
                  component={RouterLink}
                  to={`/incidents/${incident.id}`}
                  sx={{ textDecoration: 'none' }}
                >
                  <TableCell>{incident.title}</TableCell>
                  <TableCell>
                    <SeverityChip severity={incident.severity} />
                  </TableCell>
                  <TableCell>
                    <StatusChip status={incident.status} />
                  </TableCell>
                  <TableCell>{formatCompactDate(incident.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <Box sx={{ p: 2 }}>
            <EmptyState
              title="No incidents"
              message="Create an incident to start tracking analysis."
              action={
                <Button component={RouterLink} to="/incidents/new" variant="contained">
                  New Incident
                </Button>
              }
            />
          </Box>
        )}
      </Paper>
    </Box>
  )
}
