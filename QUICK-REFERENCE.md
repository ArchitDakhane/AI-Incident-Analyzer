# Quick Reference Guide

## Project Setup Commands

### Initial Setup (First Time)

```bash
# Clone and navigate
git clone <repo-url>
cd AI-Incident-Analyzer

# Copy environment file
cp .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your-key-here
```

### With Docker (Recommended)

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Rebuild images
docker compose build

# Remove volumes (CLEARS DATA!)
docker compose down -v
```

### Without Docker (Local Development)

```bash
# Backend Setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
poetry install
python main.py

# Frontend Setup (separate terminal)
cd frontend
npm install
npm run dev
```

---

## Development Commands

### Backend (Python)

```bash
# Install dependencies
poetry install

# Run application
python main.py

# Run tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=app

# Format code
black app/ main.py
isort app/ main.py

# Lint code
flake8 app/ main.py

# Type checking
mypy app/

# Run single test file
pytest tests/test_auth.py -v

# Run specific test
pytest tests/test_auth.py::test_login -v
```

### Frontend (JavaScript/TypeScript)

```bash
# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Preview production build locally
npm run preview

# Format code
npm run format

# Lint code
npm run lint

# Type checking
npm run type-check

# Upgrade dependencies
npm update
```

---

## Database Commands

### PostgreSQL (via Docker)

```bash
# Connect to database
docker compose exec postgres psql -U postgres -d ai_incident_analyzer

# List tables
\dt

# Describe table
\d table_name

# Run SQL query
SELECT * FROM users;

# Exit
\q
```

### Alembic Migrations (Backend)

```bash
# Navigate to backend
cd backend

# Create migration (auto-detect changes)
alembic revision --autogenerate -m "Add users table"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic current

# Create empty migration
alembic revision -m "Migration name"
```

---

## Redis Commands

### Via Docker

```bash
# Connect to Redis CLI
docker compose exec redis redis-cli

# Ping Redis
PING

# Get all keys
KEYS *

# Get key value
GET key_name

# Delete key
DEL key_name

# Clear all data
FLUSHALL

# Exit
EXIT
```

---

## Qdrant Commands

### Health Check

```bash
# Check Qdrant health
curl http://localhost:6333/health

# List collections
curl http://localhost:6333/collections

# Access Qdrant UI (if available)
# http://localhost:6333/dashboard
```

---

## Docker Commands

### Container Management

```bash
# List running containers
docker compose ps

# Stop specific service
docker compose stop postgres

# Start specific service
docker compose start postgres

# Restart service
docker compose restart backend

# View service logs
docker compose logs -f service_name

# Execute command in container
docker compose exec backend bash

# View container resource usage
docker stats
```

### Image Management

```bash
# Build specific image
docker compose build backend

# List images
docker images

# Remove image
docker rmi image_name

# Clean up unused images
docker image prune
```

---

## Git Commands

### Setup and Commits

```bash
# Initialize repository
git init

# Add files
git add .

# Commit changes
git commit -m "feat: add user authentication"

# Push to remote
git push origin main

# Pull latest changes
git pull origin main

# View status
git status

# View diff
git diff

# View log
git log --oneline
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks (one time)
pip install pre-commit
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Bypass hooks (not recommended)
git commit --no-verify
```

---

## Testing Commands

### Backend Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_auth.py::test_login -v

# Run with coverage
pytest --cov=app --cov-report=html

# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Run tests matching pattern
pytest -k "auth" -v
```

### Frontend Testing (When Available)

```bash
# Run tests
npm test

# Run tests in watch mode
npm test -- --watch

# Coverage report
npm test -- --coverage
```

---

## Useful URLs (Local Development)

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | React application |
| Frontend Dev | http://localhost:5173 | Vite dev server |
| Backend | http://localhost:8000 | FastAPI server |
| API Docs | http://localhost:8000/docs | Swagger UI |
| API ReDoc | http://localhost:8000/redoc | ReDoc API docs |
| Health Check | http://localhost:8000/api/health | API health status |
| PostgreSQL | localhost:5432 | Database (psql) |
| Redis | localhost:6379 | Cache (redis-cli) |
| Qdrant | http://localhost:6333 | Vector DB |

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port (macOS/Linux)
lsof -i :8000

# Kill process (macOS/Linux)
kill -9 <PID>

# Windows: use Task Manager or:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Docker Issues

```bash
# View Docker logs
docker logs container_name

# Reset Docker
docker compose down -v
docker compose up -d

# Check Docker disk usage
docker system df

# Clean up Docker
docker system prune
```

### Module Import Errors (Python)

```bash
# Reinstall dependencies
poetry install --no-cache

# Update Poetry
poetry self update

# Clear pip cache
pip cache purge
```

### Node Module Issues

```bash
# Clean install
rm -rf node_modules package-lock.json
npm install

# Clear npm cache
npm cache clean --force
```

---

## Performance Profiling

### Backend Profiling

```bash
# Profile endpoint with time
time curl http://localhost:8000/api/incidents

# Use pytest-benchmark for tests
pytest tests/test_performance.py --benchmark
```

### Frontend Performance

```bash
# Build analysis
npm run build -- --analyze

# Chrome DevTools
# Open http://localhost:5173
# F12 → Performance tab
```

---

## Deployment Commands

### Build for Production

```bash
# Backend
cd backend
docker build -t ai-incident-analyzer-backend:latest .

# Frontend
cd frontend
docker build -t ai-incident-analyzer-frontend:latest .

# Docker Compose
docker compose build
```

### Push to Registry

```bash
# Tag image
docker tag ai-incident-analyzer-backend:latest username/repo:latest

# Push
docker push username/repo:latest
```

---

## Environment Variable Quick Reference

```bash
# Backend
DATABASE_URL=postgresql://user:pass@localhost:5432/db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret
GEMINI_API_KEY=your-key
QDRANT_HOST=localhost
QDRANT_PORT=6333
LOG_LEVEL=INFO
DEBUG=True

# Frontend
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_NAME=AI Incident Analyzer

# Root (for docker-compose)
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=ai_incident_analyzer
SECRET_KEY=dev-secret
GEMINI_API_KEY=your-key
```

---

## Common Workflows

### Adding a New Feature

1. Create feature branch
   ```bash
   git checkout -b feature/my-feature
   ```

2. Make changes (backend and/or frontend)

3. Format code
   ```bash
   black app/ main.py  # Backend
   npm run format      # Frontend
   ```

4. Run tests
   ```bash
   pytest tests/
   npm test
   ```

5. Commit (pre-commit hooks run automatically)
   ```bash
   git add .
   git commit -m "feat: add my feature"
   ```

6. Push to remote
   ```bash
   git push origin feature/my-feature
   ```

### Debugging an Issue

1. Check logs
   ```bash
   docker compose logs -f backend
   ```

2. Run in debug mode
   ```bash
   # Backend: Modify main.py and set DEBUG=True
   python main.py
   ```

3. Use breakpoints (PyCharm/VS Code)
   ```python
   breakpoint()  # Python 3.7+
   ```

4. Check database state
   ```bash
   docker compose exec postgres psql -U postgres
   SELECT * FROM incidents WHERE id = 1;
   ```

5. Check Redis cache
   ```bash
   docker compose exec redis redis-cli
   GET incident:1:analysis
   ```

---

## Useful Documentation

- **Framework Docs**
  - [FastAPI Documentation](https://fastapi.tiangolo.com)
  - [React Documentation](https://react.dev)
  - [SQLAlchemy Documentation](https://docs.sqlalchemy.org)
  - [Material UI Documentation](https://material-ui.com)

- **Project Docs**
  - [README.md](README.md) - Project overview
  - [DEVELOPMENT.md](DEVELOPMENT.md) - Setup guide
  - [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture decisions

- **Tools**
  - [Docker Documentation](https://docs.docker.com)
  - [Alembic Documentation](https://alembic.sqlalchemy.org)
  - [Pytest Documentation](https://docs.pytest.org)
  - [Vite Documentation](https://vitejs.dev)

---

## Quick Diagnostics

```bash
# Check everything is working
./scripts/health-check.sh  # (create this if needed)

# or manually:
echo "Backend:" && curl -s http://localhost:8000/api/health
echo "Frontend:" && curl -s http://localhost:3000 | head -c 100
echo "Database:" && docker compose exec postgres psql -U postgres -c "SELECT 1;"
echo "Redis:" && docker compose exec redis redis-cli PING
echo "Qdrant:" && curl -s http://localhost:6333/health | jq .

# If all return success/OK, everything is working!
```

---

## Notes

- Always use `docker compose` (not `docker-compose` which is deprecated)
- Pre-commit hooks run on `git commit`, bypass with `git commit --no-verify`
- TypeScript compilation happens on build, use `npm run type-check` for validation
- Backend uses async with FastAPI, normal functions also work
- Poetry lock file should be committed to version control
- `.env` file is git-ignored, create locally from `.env.example`
