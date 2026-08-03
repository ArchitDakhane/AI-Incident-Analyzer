# Architecture Overview

## System Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
│                     (React + TypeScript)                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Pages | Components | Hooks | Services | State (Context) │   │
│  └────────────────────┬────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                          │ HTTP/JSON
                          │ JWT Tokens
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER                                   │
│                 (FastAPI - main.py)                             │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │   Middleware   │  │  Exception   │  │  CORS / Security   │  │
│  │  Logging, Auth │  │   Handler    │  │  JWT Validation    │  │
│  └────────────────┘  └──────────────┘  └────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
    ┌────────────┐   ┌──────────┐   ┌──────────────┐
    │  ROUTERS   │   │ ROUTERS  │   │   ROUTERS    │
    │ /api/auth  │   │/api/inc  │   │  /api/ai     │
    └─────┬──────┘   └────┬─────┘   └──────┬───────┘
          │                │                │
          └────────────┬───┴────────────┬───┘
                       │                │
                       ▼                ▼
              ┌──────────────────────────────────┐
              │      SERVICE LAYER               │
              │  (Business Logic)                │
              │  - AuthService                   │
              │  - IncidentService               │
              │  - AIService                     │
              │  - CommentService                │
              └──────────────┬───────────────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
         ┌────────────┐  ┌────────┐  ┌──────────┐
         │ REPOSITORY │  │ CACHE  │  │    AI    │
         │  PATTERN   │  │ LAYER  │  │ SERVICES │
         │ (Database) │  │(Redis) │  │(Gemini)  │
         └────────────┘  └────────┘  └──────────┘
                │            │            │
                └────────────┼────────────┘
                             │
        ┌────────────────────┼─────────────────────────┐
        │                    │                         │
        ▼                    ▼                         ▼
    ┌──────────┐        ┌────────┐              ┌──────────┐
    │PostgreSQL│        │ Redis  │              │ Qdrant   │
    │ (Neon)   │        │Cloud   │              │ Vector DB│
    └──────────┘        └────────┘              └──────────┘
```

### Data Flow: Incident Analysis

```
1. USER UPLOAD
   Frontend → Upload Form
   ↓
   Backend: POST /api/incidents/{id}/upload
   ↓
   File Validation (extension, size, content)
   ↓
   Store in /backend/uploads/logs/
   ↓
   Save metadata in PostgreSQL

2. USER ANALYZES
   Frontend → Click "Analyze"
   ↓
   Backend: POST /api/incidents/{id}/analyze
   ↓
   Service: Read log file
   ↓
   Parse log content
   ↓
   Extract important lines (ERROR, WARNING, etc.)
   ↓
   Check Redis cache
   ↓
   IF cached:
     Return cached response
   ELSE:
     Generate Gemini prompt
     ↓
     Call Google Gemini API
     ↓
     Validate JSON response
     ↓
     Save to PostgreSQL (AIReport table)
     ↓
     Generate embeddings (Gemini Embeddings)
     ↓
     Store in Qdrant
     ↓
     Cache in Redis (24h TTL)
     ↓
     Return response

3. SEARCH SIMILAR
   Backend: GET /api/incidents/{id}/similar
   ↓
   Query Qdrant for top 3 similar incidents
   ↓
   Fetch details from PostgreSQL
   ↓
   Return to Frontend

4. RESPONSE FLOW
   Backend → Frontend
   ↓
   React Query caches data
   ↓
   Display in UI with Material UI
```

---

## Module Organization

### Backend Module Dependencies

```
┌─────────────────┐
│   app/core/     │  ← Used by ALL modules
│ config.py       │     (settings, logging, exceptions)
│ logger.py       │
│ exceptions.py   │
└─────────────────┘
        ▲
        │ (imports)
        │
┌─────────────────────────────────────────────────────────┐
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │app/auth/     │  │app/incidents/│  │app/ai/       │  │
│  │              │  │              │  │              │  │
│  │schemas/      │  │schemas/      │  │schemas/      │  │
│  │services/     │  │services/     │  │services/     │  │
│  │repositories/ │  │repositories/ │  │repositories/ │  │
│  │routers/      │  │routers/      │  │routers/      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │app/comments/ │  │app/database/ │                    │
│  │              │  │              │                    │
│  │schemas/      │  │session.py    │ ← Database setup   │
│  │services/     │  │models.py     │                    │
│  │repositories/ │  │              │                    │
│  │routers/      │  │              │                    │
│  └──────────────┘  └──────────────┘                    │
└─────────────────────────────────────────────────────────┘
        ▲
        │ (imports)
        │
┌─────────────────────────────────────────────────────────┐
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │app/middleware│  │app/services/ │  │app/utils/    │  │
│  │              │  │              │  │              │  │
│  │error_handler │  │(cross-module)│  │file_handler  │  │
│  │auth_handler  │  │              │  │validators    │  │
│  │logger_handler│  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
        ▲
        │ (imports)
        │
┌─────────────────────────────────────────────────────────┐
│  main.py (FastAPI Application)                          │
│  - Imports all routers                                  │
│  - Configures middleware                                │
│  - Sets up lifespan                                     │
└─────────────────────────────────────────────────────────┘
```

---

## Design Patterns Used

### 1. Repository Pattern

**Purpose**: Abstract database access

```python
# Instead of:
@app.post("/incidents")
def create_incident(data: dict):
    incident = db.query(Incident).create(data)  # ❌ Business logic in route

# Correct:
@app.post("/incidents")
def create_incident(data: IncidentCreate, repo: IncidentRepository = Depends()):
    incident = repo.create(data)  # ✅ Clean separation
    return incident
```

**Benefits:**
- Database-agnostic (can swap PostgreSQL for MongoDB)
- Testable (mock repositories in tests)
- Reusable (same repo used by different routes)

### 2. Dependency Injection

**Purpose**: Manage dependencies declaratively

```python
# FastAPI auto-injects dependencies
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/incidents")
def get_incidents(db: Session = Depends(get_db)):
    # db is automatically provided
    return db.query(Incident).all()
```

**Benefits:**
- Loose coupling between components
- Easy to mock for testing
- Configuration centralized

### 3. Service Layer Pattern

**Purpose**: Encapsulate business logic

```python
# Service handles complex logic
class IncidentService:
    def __init__(self, repo: IncidentRepository):
        self.repo = repo
    
    def create_incident(self, data: IncidentCreate) -> Incident:
        # Validation
        if not data.title:
            raise ValidationException("Title required")
        
        # Business logic
        incident = self.repo.create(data)
        
        # Side effects
        log_incident_created(incident)
        send_notification(incident)
        
        return incident

# Router calls service
@app.post("/incidents")
def create(data: IncidentCreate, svc: IncidentService = Depends()):
    return svc.create_incident(data)
```

**Benefits:**
- Business logic separated from HTTP handling
- Reusable across routes/webhooks/tasks
- Testable without HTTP layer

### 4. Pydantic Schemas

**Purpose**: Validate and transform data

```python
# Request schema (input)
class IncidentCreate(BaseModel):
    title: str  # Required
    description: str
    severity: Literal["Low", "Medium", "High", "Critical"]
    
    # Validation
    @field_validator('title')
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v

# Response schema (output)
class IncidentResponse(BaseModel):
    id: int
    title: str
    description: str
    created_at: datetime
    
    class Config:
        from_attributes = True  # Can init from ORM objects
```

**Benefits:**
- Automatic validation
- Type hints for IDE
- Automatic OpenAPI docs
- Serialization/deserialization

### 5. Context Managers for Resources

**Purpose**: Guaranteed cleanup of resources

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("App starting")
    redis_client.connect()
    yield
    # Shutdown
    logger.info("App shutting down")
    redis_client.close()

app = FastAPI(lifespan=lifespan)
```

**Benefits:**
- Guaranteed cleanup even if errors occur
- Clear startup/shutdown flow
- Resource pooling

---

## Frontend Architecture

### Component Hierarchy

```
<App>                           # Root component
├── <BrowserRouter>            # Routing setup
├── <ThemeProvider>            # Material UI theming
├── <QueryClientProvider>      # React Query setup
├── <AuthProvider>             # Auth context
└── <Routes>
    ├── <Route path="/">
    │   └── <MainLayout>
    │       ├── <Sidebar>
    │       ├── <Navbar>
    │       └── <Outlet>
    │           ├── <DashboardPage>
    │           │   ├── <StatsCard>
    │           │   ├── <RecentIncidents>
    │           │   └── <ChartWidget>
    │           ├── <IncidentListPage>
    │           │   ├── <SearchBar>
    │           │   ├── <FilterBar>
    │           │   └── <IncidentTable>
    │           └── ...
    ├── <Route path="/login">
    │   └── <AuthLayout>
    │       └── <LoginPage>
    │           └── <LoginForm>
    └── <Route path="*">
        └── <NotFoundPage>
```

### State Management Strategy

**Local State (useState)**
```typescript
// Component-level state for UI interactions
const [isOpen, setIsOpen] = useState(false)
const [selectedIncident, setSelectedIncident] = useState(null)
```

**Global State (Context)**
```typescript
// User authentication state
const { user, isAuthenticated, login, logout } = useAuth()

// UI theme state
const { theme, toggleDarkMode } = useTheme()
```

**Server State (React Query)**
```typescript
// API data with caching, refetch, mutations
const { data: incidents, isLoading } = useQuery({
  queryKey: ['incidents'],
  queryFn: () => incidentService.getIncidents(),
})

const mutation = useMutation({
  mutationFn: (data) => incidentService.createIncident(data),
  onSuccess: () => queryClient.invalidateQueries(['incidents']),
})
```

**Benefits:**
- Clear data ownership
- No over-engineering (no Redux/Zustand needed)
- Minimal boilerplate
- Built-in caching and sync

### Styling Strategy

**Material UI + Emotion**
```typescript
// Use MUI components
<Button variant="contained" color="primary">
  Click me
</Button>

// Extend with sx prop
<Box sx={{
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  height: '100vh',
}}>
  Content
</Box>

// Or createTheme for app-wide styling
const theme = createTheme({
  palette: {
    primary: { main: '#1976d2' },
  },
})
```

**Benefits:**
- No CSS files to maintain
- Type-safe styling
- Responsive design built-in
- Dark mode support

---

## Security Considerations

### Backend Security

1. **Authentication**
   - JWT tokens signed with SECRET_KEY
   - Tokens expire after ACCESS_TOKEN_EXPIRE_MINUTES
   - Refresh tokens (future implementation)

2. **Authorization**
   - Users can only access their own incidents
   - Comments belong to users
   - Admins have escalated permissions (future)

3. **Input Validation**
   - Pydantic validates all request data
   - File upload validation (extension, size)
   - SQL injection protection via ORM

4. **Secrets Management**
   - Never hardcode secrets
   - Use .env files (not in version control)
   - Environment-specific configurations

5. **CORS**
   - Only allow specified origins
   - Prevents unauthorized cross-domain requests

### Frontend Security

1. **Token Storage**
   - Stored in memory (not localStorage by default)
   - Sent in Authorization header
   - Lost on page refresh (secure but UX tradeoff)

2. **Input Validation**
   - Form validation before submission
   - Sanitization of user input
   - XSS prevention (React escapes by default)

3. **HTTPS**
   - Enforced in production
   - All API calls over HTTPS

---

## Performance Considerations

### Backend

1. **Database Indexing**
   - Indexes on frequently queried columns
   - Foreign key indexes for joins
   - Created in Alembic migrations

2. **Caching Strategy**
   - Gemini API responses cached in Redis (24h TTL)
   - Dashboard stats cached (5min TTL)
   - User sessions cached

3. **Async Processing**
   - Embeddings generation as background tasks
   - File uploads don't block responses
   - Long-running operations async

4. **Query Optimization**
   - Eager loading relationships (prevent N+1)
   - Pagination for large result sets
   - SELECT specific columns when possible

### Frontend

1. **Code Splitting**
   - Route-based code splitting
   - Lazy load pages
   - Dynamic imports for heavy components

2. **Caching**
   - React Query handles API caching
   - Browser cache for static assets
   - Service workers (future)

3. **Optimization**
   - Image optimization (next/image equivalent needed)
   - CSS-in-JS minification
   - Tree-shaking unused code

4. **Bundle Size**
   - Material UI with tree-shaking
   - Vite's optimized chunking
   - Monitor with build analysis

---

## Deployment Architecture

### Development Environment
```
Docker Compose
├── PostgreSQL
├── Redis
├── Qdrant
├── Backend (uvicorn --reload)
└── Frontend (Vite dev server)
```

### Production Environment (Free Tier)
```
Frontend (Vercel)
    ↓
Backend (Render)
    ├── PostgreSQL (Neon)
    ├── Redis (Redis Cloud)
    └── Qdrant (Qdrant Cloud)
```

**Why separate services?**
- Each service scaled independently
- Better security (separate credentials)
- Lower cost (free tier utilization)
- Industry standard architecture

---

## Monitoring & Logging

### Backend Logging
```python
# App startup
logger.info(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")

# Request/response
logger.info(f"POST /api/incidents - {status_code}")

# Errors
logger.error(f"Database error: {exc}", exc_info=True)

# Business logic
logger.info(f"Incident created: id={incident.id}")
```

**Output:**
- Console (development)
- File with rotation (production)
- JSON structured logging (future)

### Frontend Logging
```typescript
// Error tracking
try {
  await createIncident(data)
} catch (error) {
  console.error('Failed to create incident', error)
  toast.error('Failed to create incident')
}
```

### Monitoring (Future)
- Prometheus for metrics
- Grafana for dashboards
- Sentry for error tracking

---

## Testing Strategy

### Backend Testing

**Unit Tests**
- Services in isolation
- Mock repositories
- Test business logic

**Integration Tests**
- Routes with real database
- Test API contracts
- Migration testing

**Example:**
```python
def test_create_incident(client, db):
    response = client.post(
        "/api/incidents",
        json={
            "title": "Test",
            "description": "Test incident",
            "severity": "High",
        }
    )
    assert response.status_code == 201
    assert response.json()["id"] > 0
```

### Frontend Testing

**Component Tests**
- Render components
- Test user interactions
- Mock API calls

**Example:**
```typescript
test('LoginForm submits correctly', async () => {
  render(<LoginForm />)
  
  await userEvent.type(screen.getByPlaceholderText('Email'), 'test@example.com')
  await userEvent.type(screen.getByPlaceholderText('Password'), 'password')
  await userEvent.click(screen.getByRole('button', { name: /login/i }))
  
  expect(mockAuthService.login).toHaveBeenCalledWith({
    email: 'test@example.com',
    password: 'password',
  })
})
```

---

## Future Improvements

### Phase 2 (Next Modules)
- Database models and migrations
- Authentication implementation
- CRUD APIs for incidents
- Log upload functionality

### Phase 3
- AI integration with Gemini
- Vector search with Qdrant
- Redis caching

### Phase 4
- Frontend implementation
- Testing suite
- Deployment automation

### Phase 5 (Nice to have)
- Real-time updates (WebSockets)
- Advanced analytics
- Machine learning model training
- Admin dashboard
- API rate limiting improvements
- Webhook integrations
