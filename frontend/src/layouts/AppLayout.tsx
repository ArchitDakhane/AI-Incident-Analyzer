import { useState } from 'react'
import { Link as RouterLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  AppBar,
  Avatar,
  Box,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'
import AnalyticsOutlinedIcon from '@mui/icons-material/AnalyticsOutlined'
import DashboardOutlinedIcon from '@mui/icons-material/DashboardOutlined'
import DarkModeOutlinedIcon from '@mui/icons-material/DarkModeOutlined'
import LightModeOutlinedIcon from '@mui/icons-material/LightModeOutlined'
import LogoutIcon from '@mui/icons-material/Logout'
import MenuIcon from '@mui/icons-material/Menu'
import PersonOutlineIcon from '@mui/icons-material/PersonOutline'
import ReportProblemOutlinedIcon from '@mui/icons-material/ReportProblemOutlined'
import { useAuth } from '../contexts/AuthContext'
import { useUI } from '../contexts/UIContext'

const drawerWidth = 260

const navigationItems = [
  { label: 'Dashboard', path: '/', icon: <DashboardOutlinedIcon /> },
  { label: 'Incidents', path: '/incidents', icon: <ReportProblemOutlinedIcon /> },
  { label: 'New Incident', path: '/incidents/new', icon: <AddCircleOutlineIcon /> },
  { label: 'Profile', path: '/profile', icon: <PersonOutlineIcon /> },
]

function NavigationList({ onNavigate }: { onNavigate?: () => void }) {
  const location = useLocation()

  return (
    <List sx={{ px: 1 }}>
      {navigationItems.map((item) => {
        const selected =
          item.path === '/'
            ? location.pathname === '/'
            : location.pathname === item.path || location.pathname.startsWith(`${item.path}/`)

        return (
          <ListItemButton
            key={item.path}
            component={RouterLink}
            onClick={onNavigate}
            selected={selected}
            sx={{ borderRadius: 1.5, mb: 0.5 }}
            to={item.path}
          >
            <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItemButton>
        )
      })}
    </List>
  )
}

export function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const { user, logout } = useAuth()
  const { mode, toggleMode } = useUI()
  const theme = useTheme()
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'))
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const drawer = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Stack spacing={1.5} sx={{ px: 2.25, py: 2.5 }}>
        <Stack direction="row" spacing={1.25} sx={{ alignItems: 'center' }}>
          <Avatar sx={{ bgcolor: 'primary.main', height: 40, width: 40 }}>
            <AnalyticsOutlinedIcon />
          </Avatar>
          <Box>
            <Typography sx={{ fontWeight: 800, letterSpacing: 0 }}>AI Incidents</Typography>
            <Typography color="text.secondary" variant="caption">
              Analyzer
            </Typography>
          </Box>
        </Stack>
      </Stack>
      <Divider />
      <Box sx={{ flex: 1, overflowY: 'auto', py: 1.5 }}>
        <NavigationList onNavigate={() => setMobileOpen(false)} />
      </Box>
      <Divider />
      <Stack spacing={1.5} sx={{ p: 2 }}>
        <Stack direction="row" spacing={1.25} sx={{ alignItems: 'center' }}>
          <Avatar sx={{ height: 34, width: 34 }}>
            {(user?.full_name || user?.username || 'U').charAt(0).toUpperCase()}
          </Avatar>
          <Box sx={{ minWidth: 0 }}>
            <Typography noWrap variant="body2" sx={{ fontWeight: 700 }}>
              {user?.full_name || user?.username}
            </Typography>
            <Typography noWrap color="text.secondary" variant="caption">
              {user?.email}
            </Typography>
          </Box>
        </Stack>
      </Stack>
    </Box>
  )

  return (
    <Box sx={{ bgcolor: 'background.default', minHeight: '100vh' }}>
      <AppBar
        color="inherit"
        elevation={0}
        position="fixed"
        sx={{
          borderBottom: 1,
          borderColor: 'divider',
          ml: { md: `${drawerWidth}px` },
          width: { md: `calc(100% - ${drawerWidth}px)` },
        }}
      >
        <Toolbar sx={{ gap: 1 }}>
          {!isDesktop ? (
            <IconButton edge="start" onClick={() => setMobileOpen(true)}>
              <MenuIcon />
            </IconButton>
          ) : null}
          <Box sx={{ flex: 1 }} />
          <Tooltip title={mode === 'dark' ? 'Light mode' : 'Dark mode'}>
            <IconButton onClick={toggleMode}>
              {mode === 'dark' ? <LightModeOutlinedIcon /> : <DarkModeOutlinedIcon />}
            </IconButton>
          </Tooltip>
          <Tooltip title="Log out">
            <IconButton onClick={handleLogout}>
              <LogoutIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      <Box component="nav" sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}>
        <Drawer
          ModalProps={{ keepMounted: true }}
          onClose={() => setMobileOpen(false)}
          open={mobileOpen}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          variant="temporary"
        >
          {drawer}
        </Drawer>
        <Drawer
          open
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          variant="permanent"
        >
          {drawer}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          ml: { md: `${drawerWidth}px` },
          px: { xs: 2, sm: 3 },
          py: 3,
          pt: 11,
        }}
      >
        <Outlet />
      </Box>
    </Box>
  )
}
