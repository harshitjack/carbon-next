# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [2.0.0] - 2026-06-21

### Changed (Infrastructure Migration)
- **AI**: Replaced Vertex AI / Gemini SDK with OpenRouter API (google/gemini-flash-1.5)
- **Database**: Replaced Firestore with Supabase PostgreSQL (asyncpg)
- **Analytics**: Replaced BigQuery with PostgreSQL analytics tables
- **Event System**: Replaced Pub/Sub with database-backed event_queue table
- **Secrets**: Replaced Secret Manager with environment variables + startup validation
- **Deployment**: Replaced Cloud Run + Cloud Build with Vercel (frontend) + GHCR Docker (backend)

### Added
- Security checkpoint in AI service: PII scrubbing (SSN, credit-card) + prompt-injection detection
- SQL migrations: `migrations/001_initial_schema.sql`, `002_analytics_schema.sql`, `003_event_queue_schema.sql`
- New services: `supabase_service.py`, `analytics_service.py`, `event_queue_service.py`
- `vercel.json` for frontend deployment
- `.github/workflows/deploy.yml` for CI/CD to Vercel + GHCR
- `validate_config()` startup function with actionable warnings for missing credentials
- Backward-compatible feature flag aliases (USE_GEMINI→USE_OPENROUTER, etc.)

### Removed
- `google-cloud-aiplatform`, `vertexai`, `google-cloud-firestore`, `google-cloud-bigquery`
- `google-cloud-pubsub`, `google-cloud-secret-manager` from requirements
- `firebase.json`, `firestore.rules` (Firestore-specific files)

## [1.0.0] - 2025-06-01

### Added
- Carbon footprint calculator with transport, home energy, diet, and consumption inputs
- Science-backed emission factors (UK DEFRA 2023, US EPA eGRID 2023, IPCC AR6)
- AI-powered personalised insight generation with rule-engine fallback
- Per-device carbon history storage
- Anonymised aggregate analytics logging
- Real-time event streaming for downstream consumers
- React 18 + TypeScript frontend with Zustand state management
- WCAG 2.1 AA accessibility compliance (jest-axe verified)
- Rate limiting: 30/min calculate, 10/min insights, 20/min entries
- Security headers: CSP, HSTS, X-Frame-Options, Permissions-Policy
- Multi-stage Docker build with non-root user
- GitHub Actions CI with lint, typecheck, test, and coverage gates
