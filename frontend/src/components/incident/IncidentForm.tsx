import { FormEvent, useState } from 'react'
import {
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
} from '@mui/material'
import SaveIcon from '@mui/icons-material/Save'
import type { Incident, IncidentFormValues, IncidentStatus, Severity } from '../../types'

const severities: Severity[] = ['low', 'medium', 'high', 'critical']
const statuses: IncidentStatus[] = ['open', 'investigating', 'resolved']

interface IncidentFormProps {
  initialIncident?: Incident
  submitLabel: string
  isSubmitting?: boolean
  onSubmit: (values: IncidentFormValues) => void
}

function getInitialValues(incident?: Incident): IncidentFormValues {
  return {
    title: incident?.title ?? '',
    incident_type: incident?.incident_type ?? '',
    severity: (incident?.severity as Severity) ?? 'medium',
    status: (incident?.status as IncidentStatus) ?? 'open',
    description: incident?.description ?? '',
    summary: incident?.summary ?? '',
  }
}

export function IncidentForm({
  initialIncident,
  submitLabel,
  isSubmitting = false,
  onSubmit,
}: IncidentFormProps) {
  const [values, setValues] = useState<IncidentFormValues>(() => getInitialValues(initialIncident))

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    onSubmit({
      ...values,
      title: values.title.trim(),
      incident_type: values.incident_type?.trim() || undefined,
      description: values.description?.trim() || undefined,
      summary: values.summary?.trim() || undefined,
    })
  }

  return (
    <Box component="form" onSubmit={handleSubmit}>
      <Stack spacing={2.5}>
        <TextField
          required
          label="Title"
          value={values.title}
          inputProps={{ minLength: 3, maxLength: 255 }}
          onChange={(event) => setValues((current) => ({ ...current, title: event.target.value }))}
        />
        <TextField
          label="Incident type"
          value={values.incident_type}
          inputProps={{ maxLength: 100 }}
          onChange={(event) => {
            setValues((current) => ({ ...current, incident_type: event.target.value }))
          }}
        />
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <FormControl fullWidth>
            <InputLabel id="severity-label">Severity</InputLabel>
            <Select
              labelId="severity-label"
              label="Severity"
              value={values.severity}
              onChange={(event) => {
                setValues((current) => ({ ...current, severity: event.target.value as Severity }))
              }}
            >
              {severities.map((severity) => (
                <MenuItem key={severity} value={severity}>
                  {severity}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth>
            <InputLabel id="status-label">Status</InputLabel>
            <Select
              labelId="status-label"
              label="Status"
              value={values.status}
              onChange={(event) => {
                setValues((current) => ({ ...current, status: event.target.value as IncidentStatus }))
              }}
            >
              {statuses.map((status) => (
                <MenuItem key={status} value={status}>
                  {status}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>
        <TextField
          multiline
          minRows={5}
          label="Description"
          value={values.description}
          onChange={(event) => {
            setValues((current) => ({ ...current, description: event.target.value }))
          }}
        />
        <TextField
          multiline
          minRows={3}
          label="Summary"
          value={values.summary}
          onChange={(event) => setValues((current) => ({ ...current, summary: event.target.value }))}
        />
        <Box>
          <Button
            disabled={isSubmitting}
            startIcon={<SaveIcon />}
            type="submit"
            variant="contained"
          >
            {submitLabel}
          </Button>
        </Box>
      </Stack>
    </Box>
  )
}
