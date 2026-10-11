# Deployment Guide

This guide covers local Docker Compose and the production split deployment:

- React/Vite frontend on Vercel
- FastAPI backend on Render
- PostgreSQL on Neon
- Redis on Redis Cloud
- Vector storage on Qdrant Cloud

The repository contains a Render Blueprint at `render.yaml` and Vercel configuration at `frontend/vercel.json`. Cloud accounts and credentials are not included; create the managed resources in their providers and enter credentials only in provider dashboards.

## Local deployment with Docker Compose

Requirements: Docker Desktop with Docker Compose v2.

1. From the repository root, create a local environment file by copying `.env.example` to `.env`.
2. Replace `SECRET_KEY` with a long random value. Add `GEMINI_API_KEY` to enable AI report generation and embedding search.
3. Start the stack: `docker compose up --build -d`.
4. Open the frontend at `http://localhost:3000`; API docs at `http://localhost:8000/docs`; health check at `http://localhost:8000/api/health`.
5. Follow logs with `docker compose logs -f backend` and stop services with `docker compose down`. Persistent named volumes are retained; `docker compose down -v` deletes local data.

Compose runs Postgres, Redis, Qdrant, the API, and the static frontend. The API applies Alembic migrations before starting. Log uploads are stored in a named Docker volume. Database, Redis, and Qdrant remain private to the Compose network; only the app and API are published to localhost.

## Production architecture

Provision the managed services first, then deploy the backend and frontend. Use the nearest supported region for Render, Neon, Redis Cloud, and Qdrant Cloud to reduce latency. Use TLS-enabled service URLs. Do not use local Docker URLs in production.

### 1. Create managed services

#### Neon PostgreSQL

1. Create a Neon project and database.
2. Copy the pooled or direct connection URI and ensure it uses TLS (`sslmode=require`).
3. Set `DATABASE_URL` on Render to the URI, for example `postgresql://USER:PASSWORD@HOST/DB?sslmode=require`.
4. Keep the database credentials private. The API uses SQLAlchemy with Psycopg 3 for standard PostgreSQL URLs; verify the Neon pooled URI against the selected pooler mode.

#### Redis Cloud

1. Create a Redis Cloud database with TLS enabled and copy its TLS connection URI.
2. Set `REDIS_URL` on Render to the complete `rediss://` URI including credentials and TLS port. Do not remove URL-encoded characters in its password.
3. Restrict network access as much as the plan permits. Verify the API can connect from Render before enabling rate limits/cache use.

#### Qdrant Cloud

1. Create a Qdrant Cloud cluster and collection access key.
2. Copy the cluster HTTPS endpoint (hostname or full `https://` URL) and API key.
3. Set `QDRANT_HOST` to the HTTPS endpoint, `QDRANT_PORT` to `6333`, `QDRANT_API_KEY` to the cluster key, and `QDRANT_COLLECTION_NAME` to `incidents` on Render.
4. Qdrant's API key protects the endpoint; keep it secret. Similar-incident indexing also requires `GEMINI_API_KEY` for embeddings.

### 2. Deploy the API to Render

1. Push this repository to a Git provider supported by Render.
2. In Render, create a Blueprint instance from the repository and approve the `render.yaml` service definition, or create a Docker Web Service manually with:
   - Root directory: `backend`
   - Dockerfile: `backend/Dockerfile`
   - Docker context: `backend`
   - Health check path: `/api/health`
   - Pre-deploy command: `alembic -c alembic/alembic.ini upgrade head`
3. Set the secrets/values in the Render service environment:
   - `DATABASE_URL` — Neon PostgreSQL connection URI
   - `REDIS_URL` — Redis Cloud TLS URI
   - `QDRANT_HOST`, `QDRANT_PORT`, `QDRANT_API_KEY`, `QDRANT_COLLECTION_NAME`
   - `GEMINI_API_KEY`
   - `CORS_ORIGINS` — JSON array containing the deployed Vercel origin, e.g. `["https://your-app.vercel.app"]`
   - `SECRET_KEY` — long cryptographically random value; Render Blueprint generates one by default
   - `ENVIRONMENT=production`, `DEBUG=false`, `LOG_LEVEL=INFO`
4. Deploy. Render runs migrations before deployment using the database URL. Confirm `https://YOUR-API.onrender.com/api/health` returns a healthy response.

The Blueprint provisions an attached disk for uploads at `/var/data` and configures `UPLOAD_DIRECTORY=/var/data/uploads/logs`. Attached disks require a compatible paid Render service plan and limit horizontal scaling/zero-downtime deployment. For multi-instance or ephemeral deployment, replace local uploads with object storage before production use. Keep database backups enabled and test restores.

### 3. Deploy the frontend to Vercel

1. Import the repository into Vercel.
2. Set the project Root Directory to `frontend` and enable inclusion of files outside the root only if your project settings require it (frontend itself is self-contained).
3. Use the Vite framework preset; the build command is `npm run build` and output directory is `dist` (also declared in `frontend/vercel.json`).
4. Set the build-time environment variable `VITE_API_BASE_URL` to `https://YOUR-API.onrender.com/api`. Vite embeds this value into the built JavaScript; redeploy after changing it.
5. Add the exact Vercel production origin to Render's `CORS_ORIGINS` JSON array and redeploy the API.
6. Deploy and test registration, sign-in, incident creation, file upload, and the health/API requests from the frontend.

Vercel serves React Router paths through the SPA rewrite. Never put database, Redis, Qdrant, Gemini, or JWT secrets in Vercel variables prefixed with `VITE_`; Vite variables are public client-side values.

## Environment variables

### Backend runtime

| Variable                      | Purpose                                 | Example                               |
| ----------------------------- | --------------------------------------- | ------------------------------------- |
| `DATABASE_URL`                | PostgreSQL connection string            | `postgresql://...?...sslmode=require` |
| `REDIS_URL`                   | Redis connection string                 | `rediss://...`                        |
| `SECRET_KEY`                  | JWT signing secret                      | generated random secret               |
| `ALGORITHM`                   | JWT algorithm                           | `HS256`                               |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime                   | `30`                                  |
| `GEMINI_API_KEY`              | Gemini analysis and embeddings          | secret from Google AI Studio          |
| `QDRANT_HOST`                 | Qdrant HTTPS cluster endpoint           | `https://...cloud.qdrant.io`          |
| `QDRANT_PORT`                 | Qdrant API port                         | `6333`                                |
| `QDRANT_API_KEY`              | Qdrant cluster key                      | secret from Qdrant Cloud              |
| `QDRANT_COLLECTION_NAME`      | Embedding collection                    | `incidents`                           |
| `CORS_ORIGINS`                | JSON list of allowed browser origins    | `["https://your-app.vercel.app"]`     |
| `ENVIRONMENT`                 | Runtime environment                     | `production`                          |
| `DEBUG`                       | Debug mode                              | `false`                               |
| `LOG_LEVEL`                   | Logging threshold                       | `INFO`                                |
| `MAX_UPLOAD_SIZE_MB`          | Maximum uploaded log size               | `5`                                   |
| `MAX_ANALYSIS_LOG_CHARS`      | Maximum redacted excerpt sent to Gemini | `30000`                               |
| `UPLOAD_DIRECTORY`            | Writable upload directory               | `/var/data/uploads/logs` on Render    |

### Frontend build

| Variable            | Purpose                                  | Example                             |
| ------------------- | ---------------------------------------- | ----------------------------------- |
| `VITE_API_BASE_URL` | Public backend API base URL (build-time) | `https://your-api.onrender.com/api` |

Local templates: `.env.example` and `frontend/.env.example`. Never commit real `.env` files or paste secrets into source control/issues.

## Deployment verification checklist

- Render health endpoint returns HTTP 200.
- API logs show the latest Alembic revision applied without error.
- Browser requests to the API succeed without CORS errors.
- Registration, login, CRUD, and pagination work against Neon.
- Redis-backed features operate with Redis Cloud, and errors are reviewed in logs.
- AI reports and vector similarity work when Gemini and Qdrant credentials are configured.
- Uploaded files remain accessible after an API restart/redeploy; backups/retention are defined.
- Secrets are set in provider dashboards and are absent from tracked files and frontend bundles.

## Rollback and operations

- Roll back API/frontend to a previously successful deployment from provider dashboards.
- Database schema changes are forward migrations. Take a Neon backup before risky schema changes; do not assume a code rollback automatically reverses migrations.
- Rotate JWT, database, Redis, Qdrant, and Gemini credentials after exposure. A JWT secret rotation invalidates outstanding tokens.
- Monitor provider logs, database storage, Redis memory, Qdrant capacity, and upload disk usage.
