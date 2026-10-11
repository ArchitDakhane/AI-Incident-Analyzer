import { Button, Card, CardContent, Divider, Stack, Typography } from '@mui/material'
import LogoutIcon from '@mui/icons-material/Logout'
import { PageHeader } from '../components/common/PageHeader'
import { useAuth } from '../contexts/AuthContext'

export function ProfilePage() {
  const { user, logout } = useAuth()

  return (
    <Stack spacing={3}>
      <PageHeader title="Profile" subtitle="Account details and workspace status" />

      <Card variant="outlined" sx={{ borderRadius: 3 }}>
        <CardContent sx={{ p: 3 }}>
          <Stack spacing={2}>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ alignItems: 'center' }}>
              <Typography variant="h5" sx={{ fontWeight: 800 }}>
                {user?.full_name || user?.username || 'User'}
              </Typography>
              <Typography color="text.secondary" variant="body2">
                {user?.is_superuser ? 'Administrator' : 'Analyst'}
              </Typography>
            </Stack>

            <Divider />

            <Stack spacing={1}>
              <Typography variant="body2" color="text.secondary">
                Username
              </Typography>
              <Typography fontWeight={600}>{user?.username}</Typography>
            </Stack>

            <Stack spacing={1}>
              <Typography variant="body2" color="text.secondary">
                Email
              </Typography>
              <Typography fontWeight={600}>{user?.email}</Typography>
            </Stack>

            <Stack spacing={1}>
              <Typography variant="body2" color="text.secondary">
                Account status
              </Typography>
              <Typography fontWeight={600}>{user?.is_active ? 'Active' : 'Inactive'}</Typography>
            </Stack>

            <Button
              color="error"
              onClick={logout}
              startIcon={<LogoutIcon />}
              variant="outlined"
              sx={{ alignSelf: 'flex-start' }}
            >
              Sign out
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  )
}
