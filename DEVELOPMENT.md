# Development Guide

## Module 1: Project Setup & Structure - COMPLETE ✅

This module establishes the foundation for the entire project with a clean, modular architecture ready for scalable development.

---

## Folder Structure Overview

### Backend Structure (`backend/`)

```
backend/
├── app/
│   ├── __init__.py                 # Package marker
│   ├── auth/                       # Authentication module
│   │   └── __init__.py            # Future: schemas, services, routers
│   │
│   ├── incidents/                  # Incident management module
│   │   └── __init__.py            # Future: CRUD operations
│   │
│   ├── ai/                         # AI integration module
│   │   └── __init__.py            # Future: Gemini API, embeddings, caching
│   │
│   ├── comments/                   # Comments system module
│   │   └── __init__.py            # Future: comment CRUD
│   │
│   ├── database/                   # Database configuration
│   │   └── __init__.py            # Future: session management, models
│   │
│   ├── core/                       # Core application utilities
│   │   ├── __init__.py            # Exports for core modules
│   │   ├── config.py              # Settings management (Pydantic BaseSettings)
│   │   ├── logger.py              # Logging configuration
│   │   └── exceptions.py          # Custom exception classes
│   │
│   ├── middleware/                 # HTTP middleware
│   │   └── __init__.py            # Future: error handling, auth, logging
│   │
│   ├── routers/                    # API route handlers
│   │   └── __init__.py            # Future: auth, incidents, ai, comments routes
│   │
│   ├── services/                   # Business logic layer
│   │   └── __init__.py            # Future: auth, incident, ai services
│   │
│   ├── schemas/                    # Pydantic request/response models
│   │   └── __init__.py            # Future: DTOs for all modules
│   │
│   ├── repositories/               # Data access layer (Repository pattern)
│   │   └── __init__.py            # Future: CRUD repositories for each entity
│   │
│   └── utils/                      # Utility functions
│       └── __init__.py            # Future: helpers, validators, file handlers
│
├── tests/
│   ├── __init__.py
│   └── conftest.py                # pytest fixtures and configuration
│
├── uploads/
│   └── logs/                      # Uploaded log files directory
│       └── .gitkeep
│
├── alembic/
│   ├── alembic.ini               # Alembic configuration
│   ├── env.py                    # Alembic environment setup
│   ├── script.py.mako            # Migration template
│   └── versions/                 # Database migration files
│       └── .gitkeep
│
├── main.py                        # Application entry point
├── pyproject.toml                # Poetry dependency management
├── Dockerfile                    # Backend container image
├── .env                          # Local environment variables (git-ignored)
├── .env.example                  # Environment template
└── .gitignore                    # Backend-specific git ignore rules
```

### Frontend Structure (`frontend/`)

```
frontend/
├── src/
│   ├── pages/                    # Route pages (one per major feature)
│   │   ├── LoginPage.tsx        # Future
│   │   ├── RegisterPage.tsx     # Future
│   │   ├── DashboardPage.tsx    # Future
│   │   ├── IncidentListPage.tsx # Future
│   │   ├── CreateIncidentPage.tsx # Future
│   │   ├── IncidentDetailsPage.tsx # Future
│   │   ├── ProfilePage.tsx      # Future
│   │   └── NotFoundPage.tsx     # Future
│   │
│   ├── components/              # Reusable UI components
│   │   ├── common/             # Common components (Button, Card, etc.)
│   │   ├── forms/              # Form components
│   │   ├── incident/           # Incident-specific components
│   │   └── auth/               # Auth-specific components
│   │
│   ├── layouts/                # Layout components
│   │   ├── MainLayout.tsx      # Main app layout with sidebar/navbar
│   │   ├── AuthLayout.tsx      # Auth pages layout
│   │   └── DashboardLayout.tsx # Dashboard layout
│   │
│   ├── hooks/                  # Custom React hooks
│   │   ├── useAuth.ts          # Future: authentication hook
│   │   ├── useIncidents.ts     # Future: incidents data fetching
│   │   └── usePagination.ts    # Future: pagination logic
│   │
│   ├── services/               # API client services
│   │   ├── api.ts              # Axios instance with interceptors
│   │   ├── authService.ts      # Future: auth API calls
│   │   └── incidentService.ts  # Future: incident API calls
│   │
│   ├── types/                  # TypeScript type definitions
│   │   └── index.ts            # Centralized type definitions
│   │
│   ├── contexts/               # React Context for state management
│   │   ├── AuthContext.tsx     # Future: auth state
│   │   └── UIContext.tsx       # Future: UI theme, notifications
│   │
│   ├── utils/                  # Utility functions
│   │   ├── constants.ts        # Constants and config
│   │   ├── formatters.ts       # Date, number formatting
│   │   └── validators.ts       # Form validation rules
│   │
│   ├── assets/                 # Static assets
│   │   ├── images/            # Images
│   │   ├── fonts/             # Custom fonts
│   │   └── icons/             # SVG icons
│   │
│   ├── App.tsx                 # Root App component with routing
│   ├── App.css                 # Global styles
│   ├── index.css               # Reset and base styles
│   └── main.tsx                # React entry point
│
├── public/                     # Static files served directly
├── index.html                 # HTML template
├── package.json               # npm dependencies
├── tsconfig.json              # TypeScript configuration
├── vite.config.ts            # Vite build configuration
├── .eslintrc.cjs             # ESLint configuration
├── .prettierrc.cjs           # Prettier configuration
├── Dockerfile                # Frontend container image
├── .env                      # Local environment variables (git-ignored)
├── .env.example              # Environment template
├── .gitignore                # Frontend-specific git ignore rules
└── .dockerignore             # Files to ignore in Docker build
```

---

## Configuration Files Explained

### Backend Configuration

#### `pyproject.toml` - Dependency Management
- Uses Poetry for reproducible Python environments
- Specifies Python 3.13 as minimum version
- Dependencies organized in production and dev groups
- Tool configurations for Black, isort, mypy, and pytest

#### `app/core/config.py` - Settings Management
- Uses Pydantic `BaseSettings` for environment variable loading
- Loads from `.env` file automatically
- Provides type-safe access to all settings
- Includes computed properties (e.g., `max_upload_size_bytes`)
- Differentiates between production/development environments

#### `app/core/logger.py` - Structured Logging
- Rotating file handler (10MB max, 5 backups)
- Separate console and file output
- Detailed formatting with timestamps and line numbers
- Module-specific loggers for different components
- SQL queries logged at WARNING level (suppress noise)

#### `app/core/exceptions.py` - Custom Exception Classes
Hierarchy:
- `AppException` (base) → status_code, message
- `ValidationException` (422)
- `AuthenticationException` (401)
- `AuthorizationException` (403)
- `ResourceNotFoundException` (404)
- `ConflictException` (409)
- `ServiceException` (503)

#### `main.py` - Application Entry Point
- Creates FastAPI app with lifespan context manager
- Configures CORS middleware
- Includes health check endpoints (`/api/health`, `/api/info`)
- Initializes logging on startup
- Reload mode enabled in debug environment

#### `Dockerfile` - Backend Container
- Multi-stage build for smaller image size
- Stage 1: Installs Poetry and Python dependencies
- Stage 2: Copies only necessary files
- Health check endpoint validation
- Runs with `uvicorn` on port 8000

### Frontend Configuration

#### `package.json` - Dependency Management
- React 18.2.0 with latest hooks
- Material UI (MUI) for component library
- Vite for ultra-fast builds
- React Query for server state management
- TypeScript for type safety

#### `vite.config.ts` - Build Configuration
- Development server on port 5173
- Proxy setup: `/api/*` → `http://localhost:8000/api`
- Source maps disabled for production
- Optimized output directory

#### `tsconfig.json` - TypeScript Configuration
- ES2020 target
- Strict type checking enabled
- Module resolution: bundler
- JSX: react-jsx (new JSX transform)

#### `.eslintrc.cjs` - Linting Configuration
- TypeScript parser
- React Hooks rules
- React Refresh plugin for Fast Refresh
- Warnings for explicit `any` types

#### `.prettierrc.cjs` - Code Formatting
- 2-space indentation
- Single quotes for consistency
- Trailing commas for ES5
- 100-character line length

#### `Dockerfile` - Frontend Container
- Multi-stage build
- Node 20 Alpine for small size
- Builds with `npm run build`
- Serves static files with `serve` package
- Health check on port 3000

### Root Configuration

#### `docker-compose.yml` - Local Development Orchestration
Services included:
1. **PostgreSQL** (port 5432) - Primary database
2. **Redis** (port 6379) - Cache layer
3. **Qdrant** (port 6333) - Vector database
4. **Backend** (port 8000) - FastAPI app
5. **Frontend** (port 3000) - React app

Features:
- Named volumes for persistence
- Health checks for all services
- Dependency management (backend waits for DB)
- Environment variable injection
- Bridge network for service communication

#### `.env` - Local Environment Variables
Configured for development:
- PostgreSQL: user/password authentication
- Redis: local connection
- Gemini API: placeholder (requires actual key)
- Qdrant: local connection
- JWT: dev-only secret
- Debug: enabled
- CORS: allows localhost:5173 and :3000

#### `.env.example` - Environment Template
- All required variables documented
- Serves as template for new developers
- Prevents accidental commits of secrets

#### `.gitignore` - Version Control Rules
Ignores:
- Python: `__pycache__/`, `*.pyc`, `venv/`
- Node: `node_modules/`, `dist/`
- IDE: `.vscode/`, `.idea/`
- Environment: `.env` (except `.env.example`)
- OS: `.DS_Store`, `Thumbs.db`
- Logs and uploads

#### `.pre-commit-config.yaml` - Code Quality Automation
Hooks configured:
- **Black**: Python code formatting
- **isort**: Python import sorting
- **Flake8**: Python linting
- **Prettier**: JavaScript/TypeScript formatting
- **ESLint**: JavaScript/TypeScript linting
- **Standard**: General file checks (YAML, line endings, etc.)

---

## Architecture Decisions Explained

### 1. Backend: Layered Architecture Pattern

```
HTTP Request
    ↓
[Routers] - HTTP handling, request validation
    ↓
[Services] - Business logic, orchestration
    ↓
[Repositories] - Data access abstraction
    ↓
[Database] - SQLAlchemy ORM
```

**Why?**
- **Separation of Concerns**: Each layer has a single responsibility
- **Testability**: Mock repositories for service tests
- **Reusability**: Services can be called from different routes
- **Maintainability**: Changes to DB schema don't affect business logic

### 2. Frontend: Component-Based Architecture

```
App (Root)
├── Routes
├── Pages (route-level)
├── Layouts (shared structure)
├── Components (reusable)
├── Hooks (logic)
├── Contexts (state)
└── Services (API)
```

**Why?**
- **Modularity**: Components are independent and reusable
- **Scalability**: Easy to add new pages and features
- **Performance**: Code splitting via route-based pages
- **Maintainability**: Self-contained component logic

### 3. FastAPI Application Factory Pattern

```python
def create_app() -> FastAPI:
    app = FastAPI()
    # Configure middleware
    # Register routes
    # Setup logging
    return app
```

**Why?**
- **Testability**: Easily create test instances
- **Flexibility**: Different configs for dev/prod
- **Modularity**: Separate initialization logic
- **Lifespan Management**: Proper startup/shutdown handling

### 4. Settings via Pydantic BaseSettings

**Why not hardcoded or environment.py?**
- **Type Safety**: Validation at load time
- **Auto-documentation**: IDE intellisense works
- **Computed Properties**: Can derive values
- **Production-Ready**: Built-in for apps like Django

### 5. Docker Multi-Stage Builds

```dockerfile
FROM python:3.13-slim as builder
# Install dependencies in heavy layer

FROM python:3.13-slim
# Copy only dist to final, smaller image
```

**Why?**
- **Smaller Images**: Builder artifacts not included
- **Faster Deployments**: Smaller push/pull times
- **Security**: Fewer build tools in final image
- **Cost**: Smaller images = less bandwidth

### 6. React Query for Server State

**Why not Redux or Zustand?**
- **Built for API Data**: Automatic caching, refetching
- **Less Boilerplate**: No actions/reducers
- **Background Sync**: Refetch in background
- **Devtools**: Built-in debugging

### 7. Material UI for Components

**Why not Bootstrap or Tailwind?**
- **Accessibility**: WCAG compliance built-in
- **Theming**: Complete design system
- **Components**: Pre-built complex UI
- **TypeScript**: Full type definitions
- **Professional**: Enterprise look

### 8. Vite over Create React App

**Why?**
- **Speed**: 50-100x faster builds
- **ES Modules**: Native browser support
- **HMR**: Instant updates on save
- **Future-Proof**: Industry direction

---

## Environment Variables Explained

### Backend (`.env`)

| Variable | Purpose | Example |
|----------|---------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@localhost:5432/db` |
| `REDIS_URL` | Redis cache connection | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT signing key | `dev-secret-key` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `30` |
| `GEMINI_API_KEY` | Google Gemini API key | `your-api-key` |
| `QDRANT_HOST` | Vector DB host | `localhost` |
| `QDRANT_PORT` | Vector DB port | `6333` |
| `MAX_UPLOAD_SIZE_MB` | Max file size | `5` |
| `UPLOAD_DIRECTORY` | File storage path | `uploads/logs` |
| `ENVIRONMENT` | dev/production | `development` |
| `DEBUG` | Enable debug mode | `True` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CORS_ORIGINS` | Allowed origins | `["http://localhost:5173"]` |

### Frontend (`.env`)

| Variable | Purpose | Example |
|----------|---------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000/api` |
| `VITE_APP_NAME` | App name in UI | `AI Incident Analyzer` |

---

## Getting Started

### Option 1: Docker (Recommended for Local Development)

```bash
# 1. Navigate to project directory
cd AI-Incident-Analyzer

# 2. Copy environment file
cp .env.example .env

# 3. Update .env with your Gemini API key
# Edit .env and set GEMINI_API_KEY=your-key-here

# 4. Start all services
docker compose up -d

# 5. Verify services are running
docker compose ps

# 6. Access services
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Logs: docker compose logs -f backend
```

### Option 2: Local Development (Without Docker)

#### Backend Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 4. Install Poetry
pip install poetry

# 5. Install dependencies
poetry install

# 6. Start PostgreSQL and Redis separately
# (using system package manager or other method)

# 7. Run application
python main.py
# App runs on http://localhost:8000
```

#### Frontend Setup

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
# App runs on http://localhost:5173
```

---

## Verifying Setup

### All Services Running

```bash
# Backend health check
curl http://localhost:8000/api/health

# Should return:
# {"status":"healthy","version":"0.1.0"}

# Frontend accessible at
# http://localhost:3000 or http://localhost:5173
```

### Database Connection

```bash
# Connect to PostgreSQL
psql postgresql://postgres:postgres@localhost:5432/ai_incident_analyzer

# List tables (empty on first run)
\dt

# Exit
\q
```

### Redis Connection

```bash
# Connect to Redis
redis-cli

# Ping Redis
PING
# Should return: PONG

# Exit
EXIT
```

---

## Code Quality Tools

### Pre-commit Hooks

```bash
# Install pre-commit (one time)
pip install pre-commit
pre-commit install

# Hooks run automatically on commit
# Or run manually:
pre-commit run --all-files
```

### Black (Python Formatting)

```bash
cd backend
black app/ main.py
```

### isort (Import Sorting)

```bash
cd backend
isort app/ main.py
```

### Flake8 (Python Linting)

```bash
cd backend
flake8 app/ main.py
```

### Prettier (JavaScript/TypeScript Formatting)

```bash
cd frontend
npm run format
```

### ESLint (JavaScript/TypeScript Linting)

```bash
cd frontend
npm run lint
```

---

## Development Workflow

1. **Start Services**
   ```bash
   docker compose up -d
   ```

2. **Verify Health**
   ```bash
   curl http://localhost:8000/api/health
   ```

3. **Make Changes**
   - Backend: Edit files in `backend/app/`
   - Frontend: Edit files in `frontend/src/`
   - Auto-reload enabled via Docker volumes

4. **Format Code**
   ```bash
   # Backend
   cd backend && black app/ main.py && isort app/ main.py

   # Frontend
   cd frontend && npm run format
   ```

5. **Commit Changes**
   - Pre-commit hooks run automatically
   - Fixes formatting issues
   - Runs linters

6. **Check Logs**
   ```bash
   docker compose logs -f backend
   docker compose logs -f frontend
   ```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :8000  # Backend
lsof -i :3000  # Frontend
lsof -i :5432  # Database

# Kill process
kill -9 <PID>
```

### Database Connection Fails

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Check credentials in .env
cat .env | grep DATABASE_URL

# Restart database
docker compose restart postgres
```

### Redis Connection Fails

```bash
# Check Redis is running
docker compose ps redis

# Clear Redis data if needed
docker compose exec redis redis-cli FLUSHALL
```

### Frontend Can't Connect to API

Check `vite.config.ts` proxy configuration:
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

---

## Next Steps (Module 2)

Module 2 will configure:
- Docker image optimization
- Docker Compose best practices
- Production-ready configurations

**Status**: ✅ Module 1 Complete - Ready for Module 2
