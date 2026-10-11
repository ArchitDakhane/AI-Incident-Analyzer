import { Outlet } from 'react-router-dom'
import { Box, Paper, Stack, Typography } from '@mui/material'

export function AuthLayout() {
  return (
    <Box
      sx={{
        alignItems: 'center',
        bgcolor: 'background.default',
        display: 'grid',
        minHeight: '100vh',
        px: 2,
        py: 4,
      }}
    >
      <Stack spacing={3} sx={{ mx: 'auto', width: '100%', maxWidth: 440 }}>
        <Stack spacing={0.75}>
          <Typography variant="h4" sx={{ fontWeight: 800, letterSpacing: 0 }}>
            AI Incident Analyzer
          </Typography>
          <Typography color="text.secondary">Production incident workspace</Typography>
        </Stack>
        <Paper variant="outlined" sx={{ borderRadius: 2, p: { xs: 2.5, sm: 3 } }}>
          <Outlet />
        </Paper>
      </Stack>
    </Box>
  )
}
