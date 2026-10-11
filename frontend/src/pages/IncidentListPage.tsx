import { useMemo, useState } from 'react'
import { Link as RouterLink, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Box,
  Button,
  FormControl,
  Grid,
  IconButton,
  InputAdornment,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Skeleton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TablePagination,
  TableRow,
  TextField,
  Tooltip,
} from '@mui/material'
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline'
import SearchIcon from '@mui/icons-material/Search'
import VisibilityOutlinedIcon from '@mui/icons-material/VisibilityOutlined'
import { ConfirmDialog } from '../components/common/ConfirmDialog'
import { EmptyState } from '../components/common/EmptyState'
import { ErrorState } from '../components/common/ErrorState'
import { PageHeader } from '../components/common/PageHeader'
import { SeverityChip } from '../components/incident/SeverityChip'
import { StatusChip } from '../components/incident/StatusChip'
import { useUI } from '../contexts/UIContext'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import { getApiErrorMessage } from '../services/api'
import { deleteIncident, listIncidents } from '../services/incidentService'
import { formatCompactDate } from '../utils/formatters'

const severityOptions = ['', 'low', 'medium', 'high', 'critical']
const statusOptions = ['', 'open', 'investigating', 'resolved']

export function IncidentListPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [search, setSearch] = useState(searchParams.get('search') ?? '')
  const [incidentToDelete, setIncidentToDelete] = useState<number | null>(null)
  const debouncedSearch = useDebouncedValue(search, 350)
  const queryClient = useQueryClient()
  const { notify } = useUI()

  const page = Number(searchParams.get('page') ?? 1)
  const size = Number(searchParams.get('size') ?? 10)
  const severity = searchParams.get('severity') ?? ''
  const status = searchParams.get('status') ?? ''

  const queryParams = useMemo(
    () => ({
      page,
      size,
      search: debouncedSearch || undefined,
      severity: severity || undefined,
      status: status || undefined,
      sort_by: 'created_at',
      sort_order: 'desc',
    }),
    [debouncedSearch, page, severity, size, status]
  )

  const incidentsQuery = useQuery({
    queryKey: ['incidents', queryParams],
    queryFn: () => listIncidents(queryParams),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteIncident,
    onSuccess: async () => {
      notify('Incident deleted', 'success')
      setIncidentToDelete(null)
      await queryClient.invalidateQueries({ queryKey: ['incidents'] })
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
    onError: (error) => notify(getApiErrorMessage(error), 'error'),
  })

  const updateParam = (key: string, value: string) => {
    const nextParams = new URLSearchParams(searchParams)
    if (value) {
      nextParams.set(key, value)
    } else {
      nextParams.delete(key)
    }
    nextParams.set('page', '1')
    setSearchParams(nextParams)
  }

  return (
    <Box>
      <PageHeader
        title="Incidents"
        subtitle="Search, filter, and manage production incidents"
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

      <Paper variant="outlined" sx={{ borderRadius: 2, mb: 2.5, p: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="Search incidents"
              value={search}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              onChange={(event) => {
                setSearch(event.target.value)
                updateParam('search', event.target.value)
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel id="severity-filter-label">Severity</InputLabel>
              <Select
                label="Severity"
                labelId="severity-filter-label"
                value={severity}
                onChange={(event) => updateParam('severity', event.target.value)}
              >
                {severityOptions.map((option) => (
                  <MenuItem key={option || 'all-severity'} value={option}>
                    {option || 'All severities'}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel id="status-filter-label">Status</InputLabel>
              <Select
                label="Status"
                labelId="status-filter-label"
                value={status}
                onChange={(event) => updateParam('status', event.target.value)}
              >
                {statusOptions.map((option) => (
                  <MenuItem key={option || 'all-status'} value={option}>
                    {option || 'All statuses'}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      <Paper variant="outlined" sx={{ borderRadius: 2, overflow: 'hidden' }}>
        {incidentsQuery.isLoading ? (
          <Stack spacing={1} sx={{ p: 2 }}>
            {Array.from({ length: 8 }).map((_, index) => (
              <Skeleton key={index} height={54} variant="rounded" />
            ))}
          </Stack>
        ) : incidentsQuery.isError ? (
          <Box sx={{ p: 2 }}>
            <ErrorState
              message={getApiErrorMessage(incidentsQuery.error)}
              onRetry={() => void incidentsQuery.refetch()}
            />
          </Box>
        ) : incidentsQuery.data?.items.length ? (
          <>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Title</TableCell>
                  <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>Type</TableCell>
                  <TableCell>Severity</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Updated</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {incidentsQuery.data.items.map((incident) => (
                  <TableRow hover key={incident.id}>
                    <TableCell>{incident.title}</TableCell>
                    <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>
                      {incident.incident_type || 'General'}
                    </TableCell>
                    <TableCell>
                      <SeverityChip severity={incident.severity} />
                    </TableCell>
                    <TableCell>
                      <StatusChip status={incident.status} />
                    </TableCell>
                    <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                      {formatCompactDate(incident.updated_at)}
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="View incident">
                        <IconButton component={RouterLink} to={`/incidents/${incident.id}`}>
                          <VisibilityOutlinedIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete incident">
                        <IconButton color="error" onClick={() => setIncidentToDelete(incident.id)}>
                          <DeleteOutlineIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <TablePagination
              component="div"
              count={incidentsQuery.data.total}
              page={page - 1}
              rowsPerPage={size}
              rowsPerPageOptions={[5, 10, 20, 50]}
              onPageChange={(_, nextPage) => {
                const nextParams = new URLSearchParams(searchParams)
                nextParams.set('page', String(nextPage + 1))
                setSearchParams(nextParams)
              }}
              onRowsPerPageChange={(event) => {
                const nextParams = new URLSearchParams(searchParams)
                nextParams.set('size', event.target.value)
                nextParams.set('page', '1')
                setSearchParams(nextParams)
              }}
            />
          </>
        ) : (
          <Box sx={{ p: 2 }}>
            <EmptyState
              title="No matching incidents"
              message="Adjust filters or create a new incident."
              action={
                <Button component={RouterLink} to="/incidents/new" variant="contained">
                  New Incident
                </Button>
              }
            />
          </Box>
        )}
      </Paper>

      <ConfirmDialog
        confirmLabel="Delete"
        isDanger
        message="This incident and its uploaded files will be removed."
        open={incidentToDelete !== null}
        title="Delete incident"
        onClose={() => setIncidentToDelete(null)}
        onConfirm={() => {
          if (incidentToDelete !== null) {
            deleteMutation.mutate(incidentToDelete)
          }
        }}
      />
    </Box>
  )
}
