# Security Architecture
## ClimateIQ

---

## 1. Threat Model

| Threat | Mitigation |
|--------|-----------|
| XSS | Content-Security-Policy header; React escapes all JSX output by default |
| Clickjacking | `X-Frame-Options: DENY`; CSP `frame-ancestors 'none'` |
| MIME sniffing | `X-Content-Type-Options: nosniff` |
| Man-in-the-middle | HSTS: `max-age=31536000; includeSubDomains` |
| API abuse (DDoS) | slowapi rate limiting: 30/10/20 req/min per IP |
| Injection (JSON body) | Pydantic v2 strict field validation before any processing |
| Path traversal | device_id regex: `^[a-zA-Z0-9_-]+$` — no slashes or dots |
| Credential exposure | Application Default Credentials (ADC) — no secrets in code/env |
| Excessive data exposure | API returns only computed results, never raw DB records |
| Privacy violation | device_id is a random token; BigQuery logs exclude device_id |

---

## 2. Security Headers (SecurityHeadersMiddleware)

Applied to every HTTP response via Starlette middleware:

```
Content-Security-Policy: default-src 'self';
                         script-src 'self' 'unsafe-inline';
                         style-src 'self' 'unsafe-inline';
                         img-src 'self' data:;
                         connect-src 'self'

X-Content-Type-Options:  nosniff
X-Frame-Options:          DENY
X-XSS-Protection:         1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy:          strict-origin-when-cross-origin
Permissions-Policy:       geolocation=(), microphone=(), camera=()
```

**Implementation**: `backend/app/core/security.py` → `SecurityHeadersMiddleware`

---

## 3. Input Validation (Defence in Depth)

Two independent validation layers prevent malformed or malicious input:

### Layer 1: Frontend (Zod)
- Validates before API call
- `carbonInputSchema` mirrors backend Pydantic model exactly
- User sees immediate, descriptive error messages
- File: `frontend/src/utils/validators.ts`

### Layer 2: Backend (Pydantic v2)
- Validates all incoming JSON regardless of client
- Strict field types, ge/le bounds, regex patterns
- Returns RFC 7807-compliant `422 Unprocessable Entity` on failure
- File: `backend/app/models/carbon.py`

### device_id Validation
```python
_DEVICE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{8,64}$")
```
Validated on both incoming requests and path parameters.

---

## 4. Rate Limiting

```python
CALCULATE_LIMIT = "30/minute"   # Carbon calculation
INSIGHTS_LIMIT  = "10/minute"   # Gemini AI calls (costly)
ENTRIES_LIMIT   = "20/minute"   # Firestore reads/writes
```

Uses `slowapi` with `get_remote_address` key function. Returns `429 Too Many Requests` with a `Retry-After` header.

---

## 5. Credential Management

| Service | Authentication Method |
|---------|----------------------|
| OpenRouter AI | `OPENROUTER_API_KEY` environment variable |
| Supabase / PostgreSQL | `SUPABASE_DB_URL` environment variable (connection string) |

All credentials are passed exclusively via environment variables.
No API keys, no service account JSON files, no credentials committed to the repository.
See `.env.example` for the full list of required variables.

---

## 6. Database Security (Supabase PostgreSQL)

Row-level security (RLS) can be enabled on the `carbon_entries` table:

```sql
-- Enable RLS
ALTER TABLE carbon_entries ENABLE ROW LEVEL SECURITY;

-- Entries are write-once via the application layer
-- No direct client access to the database is permitted
```

- The `device_id` column never stores real user identifiers
- Analytics tables (`analytics_events`) never store `device_id`
- Application enforces create-only semantics (no UPDATE/DELETE exposed via API)
- Field types and ranges validated by Pydantic v2 before any DB write

---

## 7. Privacy by Design

| Principle | Implementation |
|-----------|---------------|
| Data minimisation | Only lifestyle inputs are processed; no name/email/location |
| Anonymous identifiers | `device_id` is `dev-{timestamp}-{random}` — not linked to any identity |
| Session-scoped identity | device_id stored in `sessionStorage` — cleared on tab close |
| BigQuery anonymisation | `log_event_async()` never receives or logs `device_id` |
| No tracking | No analytics SDK, no cookies, no fingerprinting |

---

## 8. Docker Security

```dockerfile
# Non-root system user
RUN groupadd --system appgroup
RUN useradd --system --gid appgroup --no-create-home appuser
...
USER appuser
```

- Container runs as `appuser` (UID auto-assigned by system)
- No shell, no home directory for the appuser
- `pip install --no-cache-dir` removes pip cache to minimise image size
- `apt-get` cache cleared after curl installation
