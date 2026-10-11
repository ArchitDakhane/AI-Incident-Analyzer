import { FormEvent, useState } from 'react'
import { Link as RouterLink, useNavigate } from 'react-router-dom'
import {
  Alert,
  Box,
  Button,
  Link,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import PersonAddAlt1Icon from '@mui/icons-material/PersonAddAlt1'
import { useAuth } from '../contexts/AuthContext'
import { useUI } from '../contexts/UIContext'

export function RegisterPage() {
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const { registerUser, isLoading, error } = useAuth()
  const { notify } = useUI()
  const navigate = useNavigate()

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    await registerUser({
      email,
      username,
      password,
      full_name: fullName.trim() || undefined,
    })
    notify('Account created', 'success')
    navigate('/', { replace: true })
  }

  return (
    <Stack component="form" spacing={2.5} onSubmit={handleSubmit}>
      <Box>
        <Typography component="h1" variant="h5" sx={{ fontWeight: 800, letterSpacing: 0 }}>
          Register
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 0.5 }}>
          Create your workspace account
        </Typography>
      </Box>
      {error ? <Alert severity="error">{error}</Alert> : null}
      <TextField
        autoComplete="name"
        label="Full name"
        value={fullName}
        onChange={(event) => setFullName(event.target.value)}
      />
      <TextField
        autoComplete="username"
        inputProps={{ minLength: 3, maxLength: 50 }}
        label="Username"
        required
        value={username}
        onChange={(event) => setUsername(event.target.value)}
      />
      <TextField
        autoComplete="email"
        label="Email"
        required
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
      />
      <TextField
        autoComplete="new-password"
        helperText="Minimum 8 characters"
        inputProps={{ minLength: 8 }}
        label="Password"
        required
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
      />
      <Button disabled={isLoading} startIcon={<PersonAddAlt1Icon />} type="submit" variant="contained">
        Register
      </Button>
      <Typography color="text.secondary" textAlign="center" variant="body2">
        Already registered?{' '}
        <Link component={RouterLink} to="/login">
          Sign in
        </Link>
      </Typography>
    </Stack>
  )
}
