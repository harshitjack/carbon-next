# CarbonNext

![CI](https://github.com/harshitjack/carbon-next/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-98%25-brightgreen)
![Accessibility](https://img.shields.io/badge/accessibility-WCAG%202.1%20AA-brightgreen)
![Stack](https://img.shields.io/badge/stack-FastAPI%20%7C%20React%20%7C%20Supabase-blue)
![Python](https://img.shields.io/badge/python-3.11-blue)
![React](https://img.shields.io/badge/react-18.3-61dafb)
![Deployment](https://img.shields.io/badge/deployment-Render-black)

> **Understand, Track, and Reduce** your personal carbon impact with AI-powered insights via OpenRouter.

---

## Live Demo

| Service | URL |
|---------|-----|
| **Frontend** | https://carbon-next-3.onrender.com |
| **Backend API** | https://carbon-next-2.onrender.com |
| **API Docs** | https://carbon-next-2.onrender.com/api/docs |
| **Health Check** | https://carbon-next-2.onrender.com/api/health |

---

## What It Does

CarbonNext implements the **Understand → Track → Reduce** lifecycle:

| Pillar | What it does |
|--------|-------------|
| **Understand** | Users input transport, home energy, diet, and consumption data. The science-backed carbon engine returns a total in kg CO₂e with comparisons to the 4,000 kg global average and 2,000 kg Paris 1.5°C target. |
| **Track** | Every calculation is persisted to Supabase PostgreSQL, keyed anonymously by device ID. A trend-line history chart shows progress over time and survives backend restarts. |
| **Reduce** | OpenRouter (Gemini 2.0 Flash) generates 3 personalised, quantified reduction actions targeting the user's largest emission sources. A deterministic rule engine provides instant fallback if AI is unavailable. |

---

## Architecture

```
Browser (https://carbon-next-3.onrender.com)
    │
    └── React SPA (Vite + TypeScript)
            │
            └── VITE_API_URL → https://carbon-next-2.onrender.com
                    │
                    ├── POST /api/calculate
                    │       Carbon Engine (pure Python)
                    │       Transport · Home · Diet · Consumption
                    │       → total_kg, breakdown, ranked_categories
                    │       → vs_global_average_pct, vs_paris_target_pct
                    │
                    ├── POST /api/insights
                    │       Security Checkpoint (PII scrubbing + injection detection)
                    │       → OpenRouter / Gemini 2.0 Flash (primary)
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
| **AI** | OpenRouter — `google/gemini-2.0-flash` |
| **Database** | Supabase PostgreSQL via asyncpg connection pooler (port 6543, IPv4) |
| **Frontend** | React 18 · TypeScript · Vite · Tailwind CSS · Zustand · Zod · Recharts |
| **Backend** | Python 3.11 · FastAPI · Pydantic v2 · slowapi · uvicorn |
| **Deployment** | Render — separate Static Site (frontend) + Web Service (backend) |
| **CI** | GitHub Actions — lint · typecheck · test · coverage |

---

## UI Design

CarbonNext uses a premium Blueprint Grid design language:

- **Blueprint Grid Background** — subtle animated dot-grid with ambient depth
- **Bento Card Layouts** — radius hierarchy: 16px cards → 12px panels → 10px inputs/buttons
- **Ambient Cursor Glow** — requestAnimationFrame-driven CSS variable glow tracking the cursor; zero React state, zero re-renders
- **Glassmorphism Panels** — frosted glass surfaces with backdrop-filter blur
- **Micro-animations** — smooth transitions on all interactive elements
- **Accessibility** — WCAG 2.1 AA compliant; full keyboard navigation; screen-reader data-table fallback for all charts; `prefers-reduced-motion` respected

---

## Project Structure

```
carbon-next/
├── backend/
│   ├── app/
│   │   ├── carbon/             Pure Python emission calculation engine
│   │   ├── core/               Config, security headers, rate limiting
│   │   ├── models/             Pydantic v2 data models
│   │   ├── routes/             API endpoint handlers
│   │   └── services/           OpenRouter, Supabase (asyncpg), Analytics, EventQueue
│   ├── tests/                  pytest suite (101 tests)
│   ├── requirement.txt
│   └── requirements-dev.txt
├── frontend/
│   ├── src/
│   │   ├── components/         Calculator, Insights, History, Shared
│   │   ├── store/              Zustand state management
│   │   ├── api/                Typed fetch client
│   │   └── utils/              Formatters and validators
│   └── tests/                  Vitest + jest-axe suite (57 tests)
├── migrations/                 SQL migration files for Supabase
│   ├── 001_initial_schema.sql  carbon_entries table
│   ├── 002_analytics_schema.sql
│   └── 003_event_queue_schema.sql
├── docs/                       PRD, Architecture, Judge Evidence
└── .github/workflows/
    └── ci.yml                  Lint · typecheck · test
```

---

## Quick Start — Local Development

No external services required. All services have in-memory fallbacks.

```bash
# 1. Clone
git clone https://github.com/harshitjack/carbon-next.git
cd carbon-next

# 2. Backend (terminal 1)
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements-dev.txt

# Run with all external services disabled (uses in-memory fallbacks)
$env:USE_OPENROUTER="false"; $env:USE_SUPABASE="false"; $env:USE_ANALYTICS="false"; $env:USE_EVENT_QUEUE="false"; uvicorn app.main:app --reload --port 8000

# 3. Frontend (terminal 2)
cd frontend
npm install
npm run dev      # → http://localhost:5173 (proxies /api to :8000)
```

---

## Running Tests

```bash
# Backend — pytest with coverage
cd backend
pytest --cov=app --cov-report=term -v

# Backend lint
ruff check .

# Frontend — Vitest with v8 coverage
cd frontend
npm test

# Frontend type check
npm run typecheck
```

---

## Production Deployment — Render (Separate Services)

CarbonNext is deployed as two separate Render services:
- **Backend** — a Python Web Service running FastAPI
- **Frontend** — a Static Site serving the compiled React/Vite app

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

---

### Step 2: Deploy Backend (Web Service)

1. New → **Web Service** → connect your GitHub repository
2. **Root Directory:** `backend`
3. **Runtime:** Python 3
4. **Build Command:** `pip install -r requirement.txt`
5. **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. **Instance Type:** Free

**Environment Variables (Backend):**

| Variable | Value |
|---|---|
| `ENVIRONMENT` | `production` |
| `USE_SUPABASE` | `true` |
| `USE_OPENROUTER` | `true` |
| `USE_ANALYTICS` | `true` |
| `USE_EVENT_QUEUE` | `true` |
| `OPENROUTER_API_KEY` | *(your OpenRouter API key — mark as Secret)* |
| `OPENROUTER_MODEL` | `google/gemini-2.0-flash` |
| `SUPABASE_DB_URL` | *(your pooler URL — mark as Secret)* |
| `ALLOWED_ORIGINS` | *(your deployed frontend URL, e.g. `https://carbon-next-3.onrender.com`)* |
| `LOG_LEVEL` | `INFO` |
| `MAX_HISTORY_ENTRIES` | `20` |

---

### Step 3: Deploy Frontend (Static Site)

1. New → **Static Site** → connect your GitHub repository
2. **Root Directory:** `frontend`
3. **Build Command:** `npm install; npm run build`
4. **Publish Directory:** `dist`

**Environment Variables (Frontend):**

| Variable | Value |
|---|---|
| `VITE_API_URL` | *(your deployed backend URL, e.g. `https://carbon-next-2.onrender.com`)* |

> ⚠️ `VITE_API_URL` must be set before the build runs — Vite bakes env vars in at build time.

---

### Step 4: Verify Deployment

```
GET  https://carbon-next-2.onrender.com/api/health
→ {"status":"healthy","services":{"openrouter":true,"supabase":true,...}}

GET  https://carbon-next-3.onrender.com/
→ React SPA loads and connects to the backend
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
- **No secrets in code**: All credentials via environment variables only — see `.env.example`
- **CORS**: Backend restricts origins to the deployed frontend URL via `ALLOWED_ORIGINS` env var

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
