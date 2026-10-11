import { FormEvent, useState } from 'react'
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom'
import {
  Alert,
  Box,
  Button,
  Link,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import LoginIcon from '@mui/icons-material/Login'
import { useAuth } from '../contexts/AuthContext'
import { useUI } from '../contexts/UIContext'

interface LocationState {
  from?: {
    pathname?: string
  }
}

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const { loginUser, isLoading, error } = useAuth()
  const { notify } = useUI()
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as LocationState | null

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    await loginUser({ email, password })
    notify('Signed in', 'success')
    navigate(state?.from?.pathname || '/', { replace: true })
  }

  return (
    <Stack component="form" spacing={2.5} onSubmit={handleSubmit}>
      <Box>
        <Typography component="h1" variant="h5" sx={{ fontWeight: 800, letterSpacing: 0 }}>
          Sign in
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 0.5 }}>
          Access incident analysis
        </Typography>
      </Box>
      {error ? <Alert severity="error">{error}</Alert> : null}
      <TextField
        autoComplete="email"
        autoFocus
        label="Email"
        required
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
      />
      <TextField
        autoComplete="current-password"
        label="Password"
        required
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
      />
      <Button disabled={isLoading} startIcon={<LoginIcon />} type="submit" variant="contained">
        Sign in
      </Button>
      <Typography color="text.secondary" textAlign="center" variant="body2">
        Need an account?{' '}
        <Link component={RouterLink} to="/register">
          Register
        </Link>
      </Typography>
    </Stack>
  )
}
