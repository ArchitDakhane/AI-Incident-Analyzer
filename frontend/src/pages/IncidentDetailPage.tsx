import { useMemo, useState } from 'react'
import { Link as RouterLink, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Stack,
  Select,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import AutoAwesomeOutlinedIcon from '@mui/icons-material/AutoAwesomeOutlined'
import ArrowBackOutlinedIcon from '@mui/icons-material/ArrowBackOutlined'
import EditNoteOutlinedIcon from '@mui/icons-material/EditNoteOutlined'
import UploadFileOutlinedIcon from '@mui/icons-material/UploadFileOutlined'
import { PageHeader } from '../components/common/PageHeader'
import { SeverityChip } from '../components/incident/SeverityChip'
import { StatusChip } from '../components/incident/StatusChip'
import { IncidentForm } from '../components/incident/IncidentForm'
import { useUI } from '../contexts/UIContext'
import { getApiErrorMessage } from '../services/api'
import {
  generateAIReport,
  getIncident,
  getIncidentLogs,
  getSimilarIncidents,
  uploadLogFile,
  updateIncident,
} from '../services/incidentService'
import type { AIReport, IncidentFormValues, UploadResponse } from '../types'
import { formatDate, formatPercent } from '../utils/formatters'

export function IncidentDetailPage() {
  const { id } = useParams()
  const incidentId = Number(id)
  const { notify } = useUI()
  const queryClient = useQueryClient()
  const [generatedReport, setGeneratedReport] = useState<AIReport | null>(null)
  const [selectedLogFileId, setSelectedLogFileId] = useState<number | ''>('')

  const incidentQuery = useQuery({
    queryKey: ['incidents', incidentId],
    queryFn: () => getIncident(incidentId),
    enabled: Number.isFinite(incidentId),
  })

  const similarQuery = useQuery({
    queryKey: ['incidents', incidentId, 'similar'],
    queryFn: () => getSimilarIncidents(incidentId),
    enabled: Number.isFinite(incidentId),
  })

  const logsQuery = useQuery({
    queryKey: ['incidents', incidentId, 'logs'],
    queryFn: () => getIncidentLogs(incidentId),
    enabled: Number.isInteger(incidentId) && incidentId > 0,
  })

  const textLogs = logsQuery.data?.filter((log) => log.file_type?.toLowerCase() === 'txt') ?? []
  const activeLogFileId =
    selectedLogFileId || textLogs[0]?.id

  const updateMutation = useMutation({
    mutationFn: (values: IncidentFormValues) => updateIncident(incidentId, values),
    onSuccess: async (updatedIncident) => {
      notify('Incident updated', 'success')
      await queryClient.invalidateQueries({ queryKey: ['incidents'] })
      await queryClient.setQueryData(['incidents', incidentId], updatedIncident)
    },
    onError: (error) => notify(getApiErrorMessage(error), 'error'),
  })

  const aiReportMutation = useMutation({
    mutationFn: () => generateAIReport(incidentId, activeLogFileId || undefined),
    onSuccess: (report) => {
      setGeneratedReport(report)
      notify('AI report generated', 'success')
    },
    onError: (error) => notify(getApiErrorMessage(error), 'error'),
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadLogFile(incidentId, file),
    onSuccess: async (uploadedFile) => {
      queryClient.setQueryData<UploadResponse[]>(
        ['incidents', incidentId, 'logs'],
        (currentLogs = []) => [
          uploadedFile,
          ...currentLogs.filter((log) => log.id !== uploadedFile.id),
        ]
      )
      setSelectedLogFileId(uploadedFile.id)
      setGeneratedReport(null)
      notify('Log file uploaded. Sensitive values are redacted before AI analysis.', 'success')
      await queryClient.invalidateQueries({ queryKey: ['incidents', incidentId, 'logs'] })
    },
    onError: (error) => notify(getApiErrorMessage(error), 'error'),
  })

  const incident = incidentQuery.data

  const metaRows = useMemo(
    () => [
      { label: 'Type', value: incident?.incident_type || 'General' },
      { label: 'Created', value: incident ? formatDate(incident.created_at) : '—' },
      { label: 'Updated', value: incident ? formatDate(incident.updated_at) : '—' },
    ],
    [incident]
  )

  if (!Number.isInteger(incidentId) || incidentId < 1) {
    return <Alert severity="error">Invalid incident ID.</Alert>
  }

  if (incidentQuery.isLoading) {
    return <Typography>Loading incident...</Typography>
  }

  if (incidentQuery.isError || !incident) {
    return (
      <Alert severity="error">{getApiErrorMessage(incidentQuery.error ?? 'Incident not found')}</Alert>
    )
  }

  return (
    <Stack spacing={3}>
      <PageHeader
        title={incident.title}
        subtitle="Incident detail and AI triage"
        actions={
          <>
            <Button
              component={RouterLink}
              startIcon={<ArrowBackOutlinedIcon />}
              to="/incidents"
              variant="outlined"
            >
              Back to list
            </Button>
            <Button
              disabled={aiReportMutation.isPending}
              onClick={() => void aiReportMutation.mutateAsync()}
              startIcon={<AutoAwesomeOutlinedIcon />}
              variant="contained"
            >
              {aiReportMutation.isPending ? 'Generating...' : 'Generate AI report'}
            </Button>
          </>
        }
      />

      <Grid container spacing={3}>
        <Grid item xs={12} lg={7}>
          <Card variant="outlined" sx={{ borderRadius: 3 }}>
            <CardContent sx={{ p: 3 }}>
              <Stack spacing={2}>
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} sx={{ alignItems: 'center' }}>
                  <Typography variant="h5" sx={{ fontWeight: 800 }}>
                    Overview
                  </Typography>
                  <SeverityChip severity={incident.severity} />
                  <StatusChip status={incident.status} />
                </Stack>

                <Divider />

                <Stack spacing={2.5}>
                  {metaRows.map((item) => (
                    <Box key={item.label}>
                      <Typography color="text.secondary" variant="caption">
                        {item.label}
                      </Typography>
                      <Typography sx={{ fontWeight: 600 }}>{item.value}</Typography>
                    </Box>
                  ))}
                </Stack>

                <Box>
                  <Typography color="text.secondary" variant="caption">
                    Description
                  </Typography>
                  <Typography sx={{ mt: 0.75, whiteSpace: 'pre-line' }}>
                    {incident.description || 'No description provided.'}
                  </Typography>
                </Box>

                <Box>
                  <Typography color="text.secondary" variant="caption">
                    Summary
                  </Typography>
                  <Typography sx={{ mt: 0.75, whiteSpace: 'pre-line' }}>
                    {incident.summary || 'No summary available.'}
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} lg={5}>
          <Card variant="outlined" sx={{ borderRadius: 3, height: '100%' }}>
            <CardContent sx={{ p: 3 }}>
              <Stack spacing={2}>
                <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                  <AutoAwesomeOutlinedIcon color="primary" />
                  <Typography variant="h6" sx={{ fontWeight: 800 }}>
                    AI Analysis
                  </Typography>
                </Stack>

                {generatedReport ? (
                  <Stack spacing={2}>
                    <Chip
                      label={
                        generatedReport.confidence_score !== null
                          ? `${(generatedReport.confidence_score * 100).toFixed(0)}% confidence`
                          : 'Confidence N/A'
                      }
                      color="primary"
                      variant="outlined"
                      sx={{ alignSelf: 'flex-start' }}
                    />
                    <Box>
                      <Typography color="text.secondary" variant="caption">
                        Summary
                      </Typography>
                      <Typography sx={{ mt: 0.5, whiteSpace: 'pre-line' }}>{generatedReport.summary}</Typography>
                    </Box>
                    <Box>
                      <Typography color="text.secondary" variant="caption">
                        Findings
                      </Typography>
                      <ul>
                        {generatedReport.findings.length ? (
                          generatedReport.findings.map((finding) => <li key={finding}>{finding}</li>)
                        ) : (
                          <li>No findings detected.</li>
                        )}
                      </ul>
                    </Box>
                    <Box>
                      <Typography color="text.secondary" variant="caption">
                        Recommended actions
                      </Typography>
                      <ul>
                        {generatedReport.recommended_actions.length ? (
                          generatedReport.recommended_actions.map((action) => <li key={action}>{action}</li>)
                        ) : (
                          <li>No actions recommended.</li>
                        )}
                      </ul>
                    </Box>
                  </Stack>
                ) : (
                  <Typography color="text.secondary">
                    Generate an AI summary to review findings, recommended actions, and confidence.
                  </Typography>
                )}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Paper variant="outlined" sx={{ borderRadius: 3, p: { xs: 2, sm: 3 } }}>
        <Stack spacing={2}>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 800 }}>
              Incident logs
            </Typography>
            <Typography color="text.secondary" variant="body2">
              Upload a UTF-8 .txt log. Relevant lines and nearby context are redacted and bounded before analysis.
            </Typography>
          </Box>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <Button
              component="label"
              disabled={uploadMutation.isPending}
              startIcon={<UploadFileOutlinedIcon />}
              variant="outlined"
            >
              {uploadMutation.isPending ? 'Uploading...' : 'Upload .txt log'}
              <input
                accept=".txt,text/plain"
                aria-label="Upload .txt log"
                hidden
                type="file"
                onChange={(event) => {
                  const file = event.currentTarget.files?.[0]
                  event.currentTarget.value = ''
                  if (!file) return
                  if (!file.name.toLowerCase().endsWith('.txt')) {
                    notify('Only .txt log files are supported here.', 'error')
                    return
                  }
                  uploadMutation.mutate(file)
                }}
              />
            </Button>
            <FormControl fullWidth size="small" sx={{ maxWidth: { sm: 420 } }}>
              <InputLabel id="analysis-log-label">Log for AI analysis</InputLabel>
              <Select
                label="Log for AI analysis"
                labelId="analysis-log-label"
                value={activeLogFileId ?? ''}
                disabled={!textLogs.length || logsQuery.isLoading}
                onChange={(event) => {
                  setSelectedLogFileId(event.target.value === '' ? '' : Number(event.target.value))
                  setGeneratedReport(null)
                }}
              >
                {textLogs.map((log) => (
                  <MenuItem key={log.id} value={log.id}>
                    {log.original_filename} ({Math.ceil((log.size_bytes ?? 0) / 1024)} KB)
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
          {logsQuery.isError ? (
            <Alert severity="warning">{getApiErrorMessage(logsQuery.error)}</Alert>
          ) : null}
          {!logsQuery.isLoading && !logsQuery.isError && !logsQuery.data?.length ? (
            <Typography color="text.secondary" variant="body2">
              No logs uploaded. AI analysis can still use the incident metadata.
            </Typography>
          ) : null}
        </Stack>
      </Paper>

      <Paper variant="outlined" sx={{ borderRadius: 3, p: { xs: 2, sm: 3 } }}>
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 2 }}>
          <EditNoteOutlinedIcon color="primary" />
          <Typography variant="h6" sx={{ fontWeight: 800 }}>
            Update incident
          </Typography>
        </Stack>
        <IncidentForm
          initialIncident={incident}
          isSubmitting={updateMutation.isPending}
          submitLabel="Save changes"
          onSubmit={(values) => updateMutation.mutate(values)}
        />
      </Paper>

      <Paper variant="outlined" sx={{ borderRadius: 3, overflow: 'hidden' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider', p: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 800 }}>
            Similar incidents
          </Typography>
        </Box>

        {similarQuery.isLoading ? (
          <Typography sx={{ p: 2 }}>Loading similar incidents...</Typography>
        ) : similarQuery.isError ? (
          <Alert severity="warning" sx={{ m: 2 }}>
            {getApiErrorMessage(similarQuery.error)}
          </Alert>
        ) : !similarQuery.data?.items.length ? (
          <Typography sx={{ p: 2, color: 'text.secondary' }}>
            No similar incidents found yet.
          </Typography>
        ) : (
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Title</TableCell>
                <TableCell>Similarity</TableCell>
                <TableCell>Root cause</TableCell>
                <TableCell>Resolution</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {similarQuery.data.items.map((item) => (
                <TableRow key={item.incident_id} hover>
                  <TableCell>
                    <Button component={RouterLink} to={`/incidents/${item.incident_id}`} variant="text">
                      {item.title}
                    </Button>
                  </TableCell>
                  <TableCell>{formatPercent(item.similarity_score)}</TableCell>
                  <TableCell>{item.root_cause}</TableCell>
                  <TableCell>{item.resolution_summary}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Paper>
    </Stack>
  )
}
