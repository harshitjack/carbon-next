# ClimateIQ

![CI](https://github.com/AbhishekK7860/Promptwars-Challenge-3/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-98%25-brightgreen)
![Accessibility](https://img.shields.io/badge/accessibility-WCAG%202.1%20AA-brightgreen)
![Stack](https://img.shields.io/badge/stack-FastAPI%20%7C%20React%20%7C%20Supabase-blue)
![Python](https://img.shields.io/badge/python-3.11-blue)
![React](https://img.shields.io/badge/react-18.3-61dafb)
![Docker](https://img.shields.io/badge/deployment-Docker%20%7C%20Render-black)

> **Understand, Track, and Reduce** your personal carbon impact with AI-powered insights via OpenRouter.

---

## Live Demo

Deployed as a single unified Docker service on Render. The FastAPI backend serves both the API and the compiled React SPA from the same container.

---

## What It Does

ClimateIQ implements the **Understand → Track → Reduce** lifecycle:

| Pillar | What it does |
|--------|-------------|
| **Understand** | Users input transport, home energy, diet, and consumption data. The science-backed carbon engine returns a total in kg CO₂e with comparisons to the 4,000 kg global average and 2,000 kg Paris 1.5°C target. |
| **Track** | Every calculation is persisted to Supabase PostgreSQL, keyed anonymously by device ID. A trend-line history chart shows progress over time and survives backend restarts. |
| **Reduce** | OpenRouter (Gemini 2.5 Flash) generates 3 personalised, quantified reduction actions targeting the user's largest emission sources. A deterministic rule engine provides instant fallback if AI is unavailable. |

---

## Architecture

```
Browser
    │
    ├── / (React SPA)
    │       Served as static files by FastAPI
    │       Blueprint Grid UI · Bento Layout · Glassmorphism
    │
    └── /api/* (JSON API)
            │
            ├── POST /api/calculate
            │       Carbon Engine (pure Python)
            │       Transport · Home · Diet · Consumption
            │       → total_kg, breakdown, ranked_categories
            │       → vs_global_average_pct, vs_paris_target_pct
            │
            ├── POST /api/insights
            │       Security Checkpoint (PII scrubbing + injection detection)
            │       → OpenRouter / Gemini 2.5 Flash (primary)
            │       → Rule Engine (deterministic fallback)
            │
            ├── POST /api/entries
            │       asyncpg → Supabase PostgreSQL (carbon_entries table)
            │       Connection Pooler (IPv4, port 6543)
            │
            ├── GET  /api/entries/{device_id}
            │       asyncpg ← Supabase PostgreSQL
            │       Returns history ordered newest-first
            │
            └── GET  /api/health
                    Returns service status map for all feature flags
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **AI** | OpenRouter — `google/gemini-2.5-flash` |
| **Database** | Supabase PostgreSQL via asyncpg connection pooler (port 6543, IPv4) |
| **Frontend** | React 18 · TypeScript · Vite · Tailwind CSS · Zustand · Zod · Recharts |
| **Backend** | Python 3.11 · FastAPI · Pydantic v2 · slowapi · uvicorn |
| **Deployment** | Docker (multi-stage) · Render (single unified service) |
| **CI** | GitHub Actions — lint · typecheck · test · coverage · Docker build + health check |

---

## UI Design

ClimateIQ uses a premium Blueprint Grid design language:

- **Blueprint Grid Background** — subtle animated dot-grid with ambient depth
- **Bento Card Layouts** — radius hierarchy: 16px cards → 12px panels → 10px inputs/buttons
- **Ambient Cursor Glow** — requestAnimationFrame-driven CSS variable glow tracking the cursor; zero React state, zero re-renders
- **Glassmorphism Panels** — frosted glass surfaces with backdrop-filter blur
- **Micro-animations** — smooth transitions on all interactive elements
- **Accessibility** — WCAG 2.1 AA compliant; full keyboard navigation; screen-reader data-table fallback for all charts; `prefers-reduced-motion` respected

---

## Project Structure

```
carbon-platform/
├── Dockerfile                  Multi-stage build (Node → Python)
├── backend/
│   ├── app/
│   │   ├── carbon/             Pure Python emission calculation engine
│   │   ├── core/               Config, security headers, rate limiting
│   │   ├── models/             Pydantic v2 data models
│   │   ├── routes/             API endpoint handlers
│   │   └── services/           OpenRouter, Supabase (asyncpg), Analytics, EventQueue
│   ├── tests/                  pytest suite (101 tests)
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend/
│   ├── src/
│   │   ├── components/         Calculator, Insights, History, Shared
│   │   ├── store/              Zustand state management
│   │   ├── api/                Typed fetch client (relative /api paths)
│   │   └── utils/              Formatters and validators
│   └── tests/                  Vitest + jest-axe suite (57 tests)
├── migrations/                 SQL migration files for Supabase
│   ├── 001_initial_schema.sql  carbon_entries table
│   ├── 002_analytics_schema.sql
│   └── 003_event_queue_schema.sql
├── docs/                       PRD, Architecture, Judge Evidence
└── .github/workflows/
    ├── ci.yml                  Lint · typecheck · test · Docker health check
    └── deploy.yml              Build verification pipeline
```

---

## Quick Start — Local Development

No external services required. All services have in-memory fallbacks.

```bash
# 1. Clone
git clone https://github.com/AbhishekK7860/Promptwars-Challenge-3.git
cd Promptwars-Challenge-3

# 2. Backend (terminal 1)
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements-dev.txt

# Run with all external services disabled (uses in-memory fallbacks)
$env:USE_OPENROUTER="false"; $env:USE_SUPABASE="false"; $env:USE_FIRESTORE="false"; $env:USE_ANALYTICS="false"; $env:USE_EVENT_QUEUE="false"; uvicorn app.main:app --reload --port 8000

# 3. Frontend (terminal 2)
cd frontend
npm install
npm run dev      # → http://localhost:5173 (proxies /api to :8000)
```

---

## Running Tests

```bash
# Backend — 101 tests, coverage enforced at ≥90%
cd backend
pytest --cov=app --cov-report=term -v

# Backend lint
ruff check .

# Frontend — 57 tests with v8 coverage
cd frontend
npm test

# Frontend type check
npm run typecheck
```

---

## Docker — Local Build & Run

The Dockerfile is a production-grade multi-stage build:
- **Stage 1** — Node 20 Alpine: installs npm dependencies and runs `vite build`
- **Stage 2** — Python 3.11 Slim: installs Python dependencies, copies `frontend/dist` into `backend/static`, runs as a non-root user

```bash
# Build
docker build -t climate-iq .

# Run locally (all services disabled for testing)
docker run -p 8080:8080 \
  -e USE_OPENROUTER=false \
  -e USE_SUPABASE=false \
  -e USE_FIRESTORE=false \
  -e USE_ANALYTICS=false \
  -e USE_EVENT_QUEUE=false \
  -e ENVIRONMENT=development \
  climate-iq

# Visit http://localhost:8080
# Health check: http://localhost:8080/api/health
```

---

## Production Deployment — Render (Single Docker Service)

ClimateIQ is deployed as a single Docker container on Render. FastAPI serves the React SPA from `backend/static/` at runtime, eliminating the need for a separate frontend host, CORS configuration, or API proxy rewrites.

### Step 1: Supabase — Database Setup

Run the following migrations **in order** in your Supabase SQL Editor:

```
migrations/001_initial_schema.sql    — carbon_entries table (required)
migrations/002_analytics_schema.sql  — analytics_events table (optional)
migrations/003_event_queue_schema.sql — event_queue table (optional)
```

Use the **Connection Pooler** URL from your Supabase dashboard (not the direct database URL). The pooler resolves to IPv4 (port 6543), which is required for Render compatibility.

**Pooler URL format:**
```
postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres
```

### Step 2: Render — Create Web Service

1. New → Web Service → connect your GitHub repository
2. **Root Directory:** leave blank (`.`)
3. **Runtime:** Docker (auto-detected from `Dockerfile`)
4. **Docker Build Context:** `.`
5. **Dockerfile Path:** `Dockerfile`
6. **Docker Command:** leave blank (uses `CMD` from Dockerfile)
7. **Instance Type:** Free or Starter
8. **Health Check Path:** `/api/health`

### Step 3: Environment Variables

Set these in the Render dashboard → Environment tab:

| Variable | Value |
|---|---|
| `ENVIRONMENT` | `production` |
| `USE_SUPABASE` | `true` |
| `USE_FIRESTORE` | `true` (backward-compatibility alias for USE_SUPABASE) |
| `USE_OPENROUTER` | `true` |
| `USE_GEMINI` | `true` (backward-compatibility alias for USE_OPENROUTER) |
| `USE_ANALYTICS` | `false` |
| `USE_BIGQUERY` | `false` |
| `USE_EVENT_QUEUE` | `false` |
| `USE_PUBSUB` | `false` |
| `OPENROUTER_API_KEY` | *(your OpenRouter API key — mark as Secret)* |
| `OPENROUTER_MODEL` | `google/gemini-2.5-flash` |
| `SUPABASE_DB_URL` | *(your pooler URL — mark as Secret, ensure password is URL-encoded)* |

### Step 4: Verify Deployment

Once the service status turns Live:

```
GET  https://climate-iq.onrender.com/api/health
→ {"status":"healthy","services":{"openrouter":true,"supabase":true,...}}

GET  https://climate-iq.onrender.com/
→ React SPA loads (served by FastAPI from backend/static/)
```

---

## Database Setup Details

The `carbon_entries` table is the only mandatory migration for full functionality:

```sql
-- From migrations/001_initial_schema.sql
CREATE TABLE IF NOT EXISTS carbon_entries (
    id                    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id             TEXT        NOT NULL,
    timestamp             TIMESTAMPTZ NOT NULL DEFAULT now(),
    total_kg              FLOAT       NOT NULL CHECK (total_kg >= 0),
    breakdown             JSONB       NOT NULL DEFAULT '{}',
    ranked_categories     JSONB       NOT NULL DEFAULT '[]',
    vs_global_average_pct FLOAT       NOT NULL DEFAULT 0,
    vs_paris_target_pct   FLOAT       NOT NULL DEFAULT 0,
    insights              JSONB       NOT NULL DEFAULT '[]'
);
```

JSONB columns (`breakdown`, `ranked_categories`, `insights`) are serialized and deserialized natively by the asyncpg JSONB codec — no manual `json.dumps()` is applied in the application layer.

---

## Privacy & Security

- **No PII stored**: `device_id` is a random session-scoped token — never a name, email, or real identifier
- **Security checkpoint**: PII (SSNs, credit-card numbers) is scrubbed from AI prompts; prompt-injection attempts are blocked before reaching the LLM
- **Security headers**: CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy on every response
- **Rate limiting**: 30/min calculate · 10/min insights · 20/min entries
- **Non-root Docker user**: Container runs as `appuser`, not root
- **No secrets in code**: All credentials via environment variables only — see `.env.example`

---

## Emission Factor Sources

| Factor | Source |
|--------|--------|
| Transport (car, bus, train) | UK DEFRA 2023 |
| Aviation | ICAO Carbon Calculator 2023 |
| Electricity | US EPA eGRID 2023 |
| Natural gas | UK DEFRA 2023 |
| Diet | Our World in Data 2023 (Poore & Nemecek 2018) |
| Consumption | IPCC AR6 WG3 Ch.5 |
| Global average (4,000 kg) | Our World in Data 2023 |
| Paris target (2,000 kg) | IPCC SR1.5 2018 |

---

## Accessibility

WCAG 2.1 AA compliant. All interactive components tested with `jest-axe` (axe-core). See [ACCESSIBILITY_COMPLIANCE_REPORT.md](./ACCESSIBILITY_COMPLIANCE_REPORT.md).

- Skip-to-main-content link
- All form inputs: `label` + `htmlFor` + `aria-describedby`
- Radio groups: `fieldset` + `legend`
- Charts: `role="img"` + screen-reader data-table fallback
- Live regions: `aria-live="polite"` on results and insights
- Error alerts: `role="alert"` + `aria-live="assertive"`
- Full keyboard navigation on all interactive elements
- `prefers-reduced-motion` respected for all animations
