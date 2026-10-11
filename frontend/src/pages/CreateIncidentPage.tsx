import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Box, Paper } from '@mui/material'
import { PageHeader } from '../components/common/PageHeader'
import { IncidentForm } from '../components/incident/IncidentForm'
import { useUI } from '../contexts/UIContext'
import { getApiErrorMessage } from '../services/api'
import { createIncident } from '../services/incidentService'
import type { IncidentFormValues } from '../types'

export function CreateIncidentPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { notify } = useUI()

  const mutation = useMutation({
    mutationFn: createIncident,
    onSuccess: async (incident) => {
      notify('Incident created', 'success')
      await queryClient.invalidateQueries({ queryKey: ['incidents'] })
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      navigate(`/incidents/${incident.id}`)
    },
    onError: (error) => notify(getApiErrorMessage(error), 'error'),
  })

  const handleSubmit = (values: IncidentFormValues) => {
    mutation.mutate(values)
  }

  return (
    <Box>
      <PageHeader title="Create Incident" subtitle="Record a production event" />
      <Paper variant="outlined" sx={{ borderRadius: 2, maxWidth: 820, p: { xs: 2, sm: 3 } }}>
        <IncidentForm
          isSubmitting={mutation.isPending}
          submitLabel="Create Incident"
          onSubmit={handleSubmit}
        />
      </Paper>
    </Box>
  )
}
