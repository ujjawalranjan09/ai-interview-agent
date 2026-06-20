# Phase 6: Testing, Security & Production Readiness — Granular Execution Plan (70 Tasks)

## Goal
Comprehensive test coverage, security hardening, production infrastructure, error handling, logging, notifications, API docs, and deployment automation. This phase takes the application from "working prototype" to "production-ready SaaS".

## Starting State
- Phase 1-5 complete: auth, candidates, interviews, questions, voice/video ML, results, reports, coaching, replay, copilot, analytics dashboard, JD matching, async interviews, admin panel
- Only 1 test file exists: `apps/api/tests/test_auth.py` (5 tests)
- No frontend tests
- No rate limiting
- No structured logging
- No email notifications
- No CI/CD pipeline
- Docker Compose exists but not tested end-to-end
- No API documentation beyond FastAPI auto-generated
- No audit logging
- No data export

---

## TESTING — BACKEND

### Task 1.1: Create test conftest with database fixtures

**File:** `apps/api/tests/conftest.py`

Update the existing conftest to add:
- A test database engine (SQLite in-memory for speed, or a test PostgreSQL database)
- A session fixture that creates all tables, yields a session, then drops all tables
- Override the `get_db` dependency to use the test session
- A `client` fixture that uses the overridden app with test DB
- A `auth_headers` fixture that registers a user and returns Authorization headers
- A `admin_headers` fixture that registers an admin user and returns Authorization headers
- A `candidate_fixture` fixture that creates a candidate record and returns it
- A `interview_fixture` fixture that creates an interview and returns it

All fixtures should be async (pytest_asyncio). Use `pytest_asyncio.fixture` for async fixtures.

---

### Task 1.2: Create auth endpoint tests

**File:** `apps/api/tests/test_auth.py` (update existing)

Add tests beyond what exists:
- `test_register_validation_error` — register with invalid email, short password, missing fields → 422
- `test_register_all_roles` — register with each role (admin, interviewer, candidate) → 201
- `test_login_wrong_password` — correct email, wrong password → 401
- `test_token_refresh` — register, get tokens, POST /auth/refresh with refresh_token → new tokens
- `test_token_refresh_invalid` — POST /auth/refresh with bad token → 401
- `test_me_after_token_refresh` — register, refresh, use new access_token for /me → 200
- `test_update_profile` — PATCH /auth/me with new name → 200, verify name changed
- `test_update_password` — PATCH /auth/me/password with old and new password → 200, login with new password

---

### Task 1.3: Create candidate endpoint tests

**File:** `apps/api/tests/test_candidates.py`

- `test_create_candidate` — POST /candidates with name, email → 201
- `test_list_candidates` — GET /candidates → 200, returns list
- `test_get_candidate` — GET /candidates/{id} → 200
- `test_get_candidate_not_found` — GET /candidates/{bad_id} → 404
- `test_update_candidate` — PATCH /candidates/{id} → 200
- `test_delete_candidate` — DELETE /candidates/{id} → 204
- `test_candidate_ownership` — interviewer can see all, candidate can only see own

---

### Task 1.4: Create interview endpoint tests

**File:** `apps/api/tests/test_interviews.py`

- `test_create_interview` — POST /interviews with candidate_id → 201
- `test_list_interviews` — GET /interviews → 200
- `test_get_interview` — GET /interviews/{id} → 200
- `test_start_interview` — POST /interviews/{id}/start → 200, status changes to in_progress
- `test_start_interview_wrong_status` — start a completed interview → 409
- `test_close_interview` — POST /interviews/{id}/close → 200, status = completed
- `test_pause_resume_interview` — pause then resume → status cycles correctly
- `test_delete_interview` — DELETE /interviews/{id} → 204

---

### Task 1.5: Create question endpoint tests

**File:** `apps/api/tests/test_questions.py`

- `test_list_questions` — GET /interviews/{id}/questions → 200, returns list
- `test_submit_answer` — POST /questions/{id}/answer with text → 200, answer saved
- `test_submit_answer_already_answered` — answer same question twice → 400
- `test_submit_audio_answer` — POST /questions/{id}/answer with audio blob → 200

---

### Task 1.6: Create copilot endpoint tests

**File:** `apps/api/tests/test_copilot.py`

- `test_start_copilot` — POST /interviews/{id}/copilot/start → 200
- `test_start_copilot_unauthorized` — non-interviewer tries → 403
- `test_get_suggestions` — GET /interviews/{id}/copilot/suggestions → 200, returns list
- `test_dismiss_suggestion` — POST /copilot/dismiss/{id} → 200, suggestion marked dismissed

---

### Task 1.7: Create analytics endpoint tests

**File:** `apps/api/tests/test_analytics.py`

- `test_overview` — GET /analytics/overview → 200, returns all fields
- `test_overview_unauthorized` — candidate tries → 403
- `test_candidate_history` — GET /analytics/candidates/{id}/history → 200
- `test_trends` — GET /analytics/trends → 200, returns weekly_scores and skill_distribution

---

### Task 1.8: Create JD matching endpoint tests

**File:** `apps/api/tests/test_jd.py`

- `test_match_jd` — POST /candidates/{id}/jd with JD text → 200, returns match_percentage
- `test_match_jd_too_short` — POST with < 50 chars → 422
- `test_generate_jd_questions` — POST /candidates/{id}/jd/questions → 200, returns questions
- `test_match_jd_ownership` — non-owner candidate cannot analyze → 403

---

### Task 1.9: Create admin endpoint tests

**File:** `apps/api/tests/test_admin.py`

- `test_list_users` — GET /admin/users → 200
- `test_list_users_filter_role` — GET /admin/users?role=admin → filtered list
- `test_update_user_role` — PATCH /admin/users/{id} with role → 200
- `test_update_user_deactivate_self` — admin deactivates self → 400
- `test_admin_non_admin_forbidden` — non-admin tries /admin/users → 403
- `test_system_health` — GET /admin/system/health → 200
- `test_system_stats` — GET /admin/system/stats → 200

---

### Task 1.10: Create async interview (join) endpoint tests

**File:** `apps/api/tests/test_join.py`

- `test_share_interview` — POST /interviews/{id}/share → 200, returns token and URL
- `test_share_reuse_token` — share twice → same token returned
- `test_join_interview` — GET /interviews/join/{token} → 200, returns interview info with first_question
- `test_join_invalid_token` — GET /interviews/join/bad → 404
- `test_join_completed_interview` — join a completed interview → 400
- `test_submit_join_answer` — POST /interviews/join/{token}/answer → 200
- `test_submit_join_answer_wrong_question` — answer a question from different interview → 403

---

### Task 1.11: Create report/coaching/replay endpoint tests

**File:** `apps/api/tests/test_reports.py`

- `test_generate_report` — POST /interviews/{id}/report/generate → 200
- `test_get_report` — GET /interviews/{id}/report → 200
- `test_get_report_not_found` — GET for interview with no report → 404
- `test_generate_coaching` — POST /interviews/{id}/coaching/generate → 200
- `test_get_coaching` — GET /interviews/{id}/coaching → 200
- `test_coaching_force_regenerate` — POST with force=true → 200, new plan
- `test_get_replay` — GET /interviews/{id}/replay → 200
- `test_replay_not_completed` — GET replay for in_progress interview → 400

---

### Task 1.12: Create service unit tests

**File:** `apps/api/tests/test_services.py`

- `test_copilot_select_suggestion_types_low_score` — score 30 → rephrase, encourage, gap_fill
- `test_copilot_select_suggestion_types_mid_score` — score 65 → follow_up, star_method, gap_fill
- `test_copilot_select_suggestion_types_high_score` — score 90 → probe_deeper, strong_area, gap_fill
- `test_copilot_render_suggestion` — render with context → dict with all keys
- `test_jd_extract_skills` — JD with required/preferred sections → correct classification
- `test_jd_extract_skills_no_false_positives` — "your" does not match "r"
- `test_jd_calculate_match` — known skills → correct percentage
- `test_jd_generate_questions` — missing skills → questions generated
- `test_analytics_calculate_performance_metrics` — mock questions → correct metrics
- `test_feedback_generate_feedback` — mock data → feedback dict with all keys

---

### Task 1.13: Run full test suite and fix failures

**Steps:**
1. Run: `cd apps/api && pytest -v --tb=short`
2. Fix any test failures (common: DB isolation issues, missing fixtures, wrong status codes)
3. Run again until all tests pass
4. Run: `cd apps/api && pytest --cov=app --cov-report=term-missing` to see coverage
5. Target: > 60% line coverage for services and API endpoints

---

## TESTING — FRONTEND

### Task 2.1: Set up Vitest for frontend

**File:** `apps/web/vitest.config.ts`

Create Vitest configuration:
- Environment: jsdom
- Setup file: `apps/web/tests/setup.ts`
- Include: `**/*.test.ts`, `**/*.test.tsx`
- Path aliases matching tsconfig

**File:** `apps/web/tests/setup.ts`

Setup file:
- Import `@testing-library/jest-dom` for DOM matchers
- Mock `next/navigation` (useRouter, useParams, usePathname)
- Mock `@/lib/api` (apiFetch)

Install dependencies: `cd apps/web && pnpm add -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom`

Add to package.json scripts: `"test": "vitest run", "test:watch": "vitest"`

---

### Task 2.2: Create auth hook tests

**File:** `apps/web/hooks/__tests__/useAuth.test.ts`

- `test_login_sets_tokens` — mock apiFetch, call login, verify sessionStorage updated
- `test_logout_clears_tokens` — call logout, verify sessionStorage cleared
- `test_me_fetches_user` — mock apiFetch, verify user data returned

---

### Task 2.3: Create API utility tests

**File:** `apps/web/lib/__tests__/api.test.ts`

- `test_apiFetch_sends_auth_header` — mock fetch, verify Authorization header set
- `test_apiFetch_refreshes_on_401` — mock 401 then 200, verify token refreshed
- `test_apiFetch_throws_on_error` — mock 500, verify ApiError thrown
- `test_apiFetch_sends_json_body` — call with json option, verify Content-Type and body

---

### Task 2.4: Run frontend tests

**Steps:**
1. Run: `cd apps/web && pnpm test`
2. Fix any failures
3. Verify all tests pass

---

## SECURITY

### Task 3.1: Add rate limiting to API

**File:** `apps/api/app/core/rate_limit.py`

Create rate limiter:
- Use Redis-based rate limiting (already have Redis)
- Function `rate_limit(key: str, limit: int, window: int)` that returns True if allowed, False if exceeded
- Track by IP address for public endpoints, by user ID for authenticated endpoints
- Limits: 100 requests/minute for authenticated, 20 requests/minute for public (join endpoint), 5 requests/minute for auth endpoints (login/register)

**File:** `apps/api/app/api/v1/auth.py` — Add rate limit to login/register (5/min by IP)
**File:** `apps/api/app/api/v1/interviews.py` — Add rate limit to join endpoints (20/min by IP)

---

### Task 3.2: Add CORS configuration

**File:** `apps/api/app/main.py`

Verify CORS middleware is configured:
- Allow origins from CORS_ORIGINS setting
- Allow methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
- Allow headers: Authorization, Content-Type
- Allow credentials: true
- Max age: 600 (10 minutes preflight cache)

---

### Task 3.3: Add input validation and sanitization

**File:** `apps/api/app/core/validation.py`

Create validators:
- `sanitize_string(value: str) -> str` — strip HTML tags, trim whitespace, limit length to 10000 chars
- `validate_uuid(value: str) -> uuid.UUID` — parse and validate UUID format
- `validate_email(value: str) -> str` — normalize email (lowercase, strip)

Apply sanitization to:
- All string fields in Pydantic schemas that accept user input (jd_text, answer_text, question_text, full_name)
- Use `@field_validator` in Pydantic models

---

### Task 3.4: Add security headers middleware

**File:** `apps/api/app/core/security_headers.py`

Create middleware that adds:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- Content-Security-Policy: default-src 'self'

Register in `apps/api/app/main.py`.

---

### Task 3.5: Add request ID tracking

**File:** `apps/api/app/core/request_id.py`

Create middleware:
- Generate a UUID for each request
- Add to request state: `request.state.request_id`
- Include in response headers: X-Request-ID
- Include in log context for tracing

---

## ERROR HANDLING

### Task 4.1: Create global exception handler

**File:** `apps/api/app/core/error_handler.py`

Create handlers:
- `http_exception_handler` — returns JSON with status, detail, request_id
- `validation_exception_handler` — returns JSON with field-level errors
- `generic_exception_handler` — logs the error, returns 500 with generic message (never leaks stack traces)

Register in `apps/api/app/main.py` via `app.add_exception_handler`.

---

### Task 4.2: Create frontend error boundary

**File:** `apps/web/components/shared/ErrorBoundary.tsx`

React error boundary component:
- Catches rendering errors
- Shows user-friendly error page with "Try Again" button
- Logs error to console (future: send to error tracking service)
- Wraps the main content area in layout files

**File:** `apps/web/app/(dashboard)/layout.tsx` — Wrap children in ErrorBoundary
**File:** `apps/web/app/interview/join/[token]/layout.tsx` — Wrap children in ErrorBoundary

---

### Task 4.3: Create frontend toast error handler

**File:** `apps/web/lib/errorHandler.ts`

Utility function `handleApiError(error: unknown)`:
- If ApiError: show toast with error.message
- If network error: show "Network error. Please check your connection."
- If unknown: show "Something went wrong. Please try again."

Apply to all mutation `onError` callbacks in hooks:
- `useInterview.ts` — all mutations
- `useReport.ts` — all mutations
- `useCopilot.ts` — all mutations
- `useAdmin.ts` — all mutations

---

## LOGGING & MONITORING

### Task 5.1: Add structured logging

**File:** `apps/api/app/core/logging_config.py`

Configure Python logging:
- Use JSON formatter for structured logs
- Fields: timestamp, level, message, request_id, user_id, endpoint, duration_ms
- Log levels: DEBUG for development, INFO for production
- Configure via LOG_LEVEL environment variable

**File:** `apps/api/app/main.py` — Apply logging config on startup

---

### Task 5.2: Add request logging middleware

**File:** `apps/api/app/core/request_logger.py`

Middleware that logs:
- Request: method, path, query_params, user_id, request_id
- Response: status_code, duration_ms
- Errors: exception type, message, request_id

Skip logging for health check endpoint to reduce noise.

---

### Task 5.3: Enhance health check endpoint

**File:** `apps/api/app/main.py`

Update `/health` endpoint to return:
- status: "healthy" or "degraded"
- version: from app version constant
- uptime: seconds since startup
- checks: {database: "ok"/"error", redis: "ok"/"error", storage: "ok"/"error"}

Each check runs a quick ping (SELECT 1, redis.ping, minio bucket list).

---

## NOTIFICATIONS

### Task 6.1: Create email service

**File:** `apps/api/app/services/email_service.py`

Create email sending service:
- Uses SMTP (configurable via EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_SMTP_USER, EMAIL_SMTP_PASSWORD settings)
- Function `send_email(to: str, subject: str, html_body: str)` — sends email via SMTP
- Function `send_interview_completion_email(candidate_email: str, candidate_name: str, interview_id: str, score: float)` — sends notification when interview is completed
- Function `send_share_link_email(candidate_email: str, candidate_name: str, share_url: str, interviewer_name: str)` — sends share link to candidate
- HTML templates stored as strings in the service (keep simple, no template engine needed)

Add email settings to `apps/api/app/core/config.py`.

---

### Task 6.2: Add email notifications to interview flow

**File:** `apps/api/app/services/interview_service.py`

In `close_interview` function, after setting status to "completed":
- Call `email_service.send_interview_completion_email` asynchronously (don't block the response)
- Use `asyncio.create_task` to fire and forget
- Wrap in try/except to prevent email failures from breaking interview close

**File:** `apps/api/app/api/v1/interviews.py`

In `share_interview` endpoint, after generating share URL:
- If candidate has an email, call `email_service.send_share_link_email` asynchronously
- Same fire-and-forget pattern

---

### Task 6.3: Add frontend notification preferences

**File:** `apps/web/app/(dashboard)/settings/page.tsx`

Settings page with:
- Toggle: "Email me when interview completes" (default: on)
- Toggle: "Email me when coaching plan is ready" (default: on)
- Save button

This is a placeholder — actual persistence requires a UserSettings model or a JSON field on User. For now, store in localStorage.

---

## AUDIT LOGGING

### Task 7.1: Create audit log model

**File:** `apps/api/app/models/audit_log.py`

Model `AuditLog`:
- id: UUID (primary key)
- user_id: UUID (nullable, FK to users)
- action: String (e.g. "user.login", "interview.create", "interview.share", "admin.update_user")
- resource_type: String (e.g. "user", "interview", "candidate")
- resource_id: String (nullable)
- details: JSON (nullable, extra context)
- ip_address: String (nullable)
- created_at: DateTime

---

### Task 7.2: Create audit log service

**File:** `apps/api/app/services/audit_service.py`

Function `log_action(user_id, action, resource_type, resource_id, details, ip_address)`:
- Creates AuditLog record
- Does NOT commit — caller is responsible for commit (can be batched with the main operation)
- Non-blocking: if audit log fails, log a warning but don't break the main flow

---

### Task 7.3: Add audit logging to key endpoints

Add audit calls to:
- `auth.py` — login, register, password change
- `interviews.py` — create, start, close, share, delete
- `admin.py` — update user, list users
- `copilot.py` — start session
- `jd.py` — match, generate questions

Pattern: after the main operation succeeds, call `audit_service.log_action(...)`.

---

### Task 7.4: Create audit log API and page

**File:** `apps/api/app/api/v1/audit.py`

Endpoint:
- `GET /audit/logs` — Requires admin. Returns paginated audit logs. Filters: action, user_id, resource_type, date_from, date_to. Default: last 100 entries.

**File:** `apps/web/hooks/useAudit.ts` — hook for fetching audit logs
**File:** `apps/web/app/(dashboard)/admin/audit/page.tsx` — audit log viewer page
**File:** `apps/web/components/admin/AuditTable.tsx` — table component

**Sidebar update:** Add "Audit Log" link under Admin section.

---

### Task 7.5: Generate alembic migration for audit_logs

**Steps:**
1. Run: `cd apps/api && alembic revision --autogenerate -m "add_audit_logs_table"`
2. Review migration
3. Apply: `alembic upgrade head`

---

## API DOCUMENTATION

### Task 8.1: Add OpenAPI metadata

**File:** `apps/api/app/main.py`

Update FastAPI app initialization:
- title: "AI Interview Agent API"
- description: "Backend API for AI-powered interview platform"
- version: "1.0.0"
- contact: support email
- license_info: MIT or appropriate

---

### Task 8.2: Add endpoint documentation

Add docstrings and `summary`/`description` to all endpoint functions:
- `auth.py` — all 6 endpoints
- `candidates.py` — all CRUD endpoints
- `interviews.py` — all endpoints including share/join
- `questions.py` — answer submission
- `copilot.py` — start, suggestions, dismiss
- `analytics.py` — overview, history, trends
- `jd.py` — match, questions
- `admin.py` — users, health, stats
- `reports.py` — generate, get, download
- `coaching.py` — generate, get
- `replay.py` — get

Each docstring should be 1-2 sentences describing what the endpoint does.

---

### Task 8.3: Add response examples to schemas

**Files:** All schema files in `apps/api/app/schemas/`

Add `model_config` with `json_schema_extra` to key response schemas:
- `InterviewResponse` — example with typical values
- `JDMatchResponse` — example with match data
- `OverviewResponse` — example with analytics data
- `CopilotSessionResponse` — example with session data

---

## PERFORMANCE

### Task 9.1: Add database query optimization

**File:** `apps/api/app/services/interview_service.py`

- In `list_interviews`: add `selectinload` for candidate relationship if needed
- In `get_interview`: add eager loading for related questions count
- Add database indexes: check if `questions.interview_id`, `candidates.user_id`, `interviews.candidate_id` have indexes (they do from FK, verify)

**File:** `apps/api/app/api/v1/analytics.py`

- The overview endpoint makes 6 separate queries. Combine into fewer queries where possible using subqueries or CTEs.

---

### Task 9.2: Add response caching

**File:** `apps/api/app/core/cache.py`

Create Redis cache utility:
- `cache_get(key: str)` → cached value or None
- `cache_set(key: str, value: Any, ttl: int)` → set with TTL
- `cache_delete(key: str)` → delete
- Uses Redis connection from REDIS_URL setting

Apply to:
- Analytics overview (cache 60 seconds)
- Analytics trends (cache 60 seconds)
- System stats (cache 30 seconds)

---

### Task 9.3: Add pagination to list endpoints

Verify pagination works correctly on:
- GET /candidates — already has pagination
- GET /interviews — already has pagination
- GET /admin/users — already has pagination
- GET /audit/logs — needs pagination (from Task 7.4)

Add `Link` header to paginated responses with next/prev URLs (optional enhancement).

---

## DEPLOYMENT

### Task 10.1: Create production Dockerfile for API

**File:** `infra/docker/Dockerfile.api`

Multi-stage build:
- Stage 1: Install dependencies (python:3.12-slim, pip install)
- Stage 2: Copy app code, set PYTHONPATH, expose 8000
- CMD: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
- Health check: curl http://localhost:8000/health

---

### Task 10.2: Create production Dockerfile for Web

**File:** `infra/docker/Dockerfile.web`

Multi-stage build:
- Stage 1: Install dependencies (node:20-alpine, pnpm install)
- Stage 2: Build (pnpm build)
- Stage 3: Run (node:20-alpine, copy .next/standalone, copy public, copy static)
- CMD: node server.js
- Health check: curl http://localhost:3000

---

### Task 10.3: Create production Dockerfile for Worker

**File:** `infra/docker/Dockerfile.worker`

- Based on Python 3.12-slim
- Install API dependencies (shared with API)
- CMD: celery -A app.tasks worker --loglevel=info --concurrency=2
- Health check: celery inspect ping

---

### Task 10.4: Create production docker-compose

**File:** `infra/docker-compose.prod.yml`

Override file for production:
- Remove volume mounts (no live code reload)
- Add restart: unless-stopped to all services
- Add resource limits (memory, CPU)
- Use environment variables instead of .env files
- Add nginx reverse proxy service (optional)

---

### Task 10.5: Create environment configuration files

**File:** `.env.example` — Update with all required variables:
- DATABASE_URL
- REDIS_URL
- MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY
- JWT_SECRET_KEY
- OPENAI_API_KEY (optional)
- EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_SMTP_USER, EMAIL_SMTP_PASSWORD (optional)
- CORS_ORIGINS
- LOG_LEVEL
- NEXT_PUBLIC_API_URL
- NEXT_PUBLIC_APP_URL

**File:** `.env.production` — Template with placeholder values for production

---

### Task 10.6: Create CI/CD pipeline

**File:** `.github/workflows/ci.yml`

GitHub Actions workflow:
- Trigger: push to main, pull requests
- Jobs:
  1. `lint` — Run ruff check on API, eslint on web
  2. `test-api` — Run pytest with test database
  3. `test-web` — Run vitest
  4. `build` — Build Docker images (don't push)
- Use PostgreSQL service container for API tests
- Use Redis service container for API tests

---

### Task 10.7: Create deployment documentation

**File:** `DEPLOYMENT.md`

Document:
- Prerequisites (Docker, Docker Compose, domain name)
- Environment variable setup
- Database migration steps
- Docker Compose commands for production
- SSL/TLS setup with nginx/caddy
- Backup strategy for PostgreSQL
- Monitoring recommendations

---

## ACCESSIBILITY & UX

### Task 11.1: Add keyboard navigation to sidebar

**File:** `apps/web/components/shared/Sidebar.tsx`

- Add tabIndex={0} to all nav links
- Add onKeyDown handler for Enter/Space to activate links
- Add aria-label to each nav item
- Add role="navigation" to the nav element
- Add aria-current="page" to active link

---

### Task 11.2: Add loading states to all pages

Verify all pages have proper loading states:
- Dashboard — skeleton or spinner
- Interviews list — skeleton rows
- Interview detail — skeleton cards
- Live interview — spinner
- Results — skeleton charts
- Copilot — skeleton sidebar
- Analytics — skeleton metric cards
- Admin pages — skeleton tables

Use the existing `text-muted-foreground` pattern or add a Spinner component.

---

### Task 11.3: Add empty states to all pages

Verify all list pages have empty states:
- Interviews: "No interviews yet. Create your first interview."
- Candidates: "No candidates yet. Add a candidate."
- Copilot suggestions: "No suggestions yet."
- Analytics history: "No history for this candidate."
- Admin users: "No users found."
- Audit logs: "No audit entries."

Use the existing EmptyState component where applicable.

---

### Task 11.4: Add responsive design to dashboard

**File:** `apps/web/app/(dashboard)/layout.tsx`

- Make sidebar collapsible on mobile (hamburger menu)
- Use Tailwind responsive breakpoints: sidebar hidden on md:, shown on lg:
- Add mobile header with menu toggle button
- Main content takes full width on mobile

---

## DATA EXPORT

### Task 12.1: Create CSV export service

**File:** `apps/api/app/services/export_service.py`

Functions:
- `export_candidates_csv(db) -> bytes` — all candidates as CSV
- `export_interviews_csv(db, filters) -> bytes` — interviews with optional status/date filters
- `export_audit_logs_csv(db, filters) -> bytes` — audit logs with filters

Uses Python csv module with io.StringIO.

---

### Task 12.2: Create export API endpoints

**File:** `apps/api/app/api/v1/export.py`

Endpoints:
- `GET /export/candidates` — Requires admin/interviewer. Returns CSV file
- `GET /export/interviews` — Requires admin/interviewer. Query params: status, date_from, date_to. Returns CSV file

Set response headers: Content-Type: text/csv, Content-Disposition: attachment; filename=candidates_export.csv

Register router in router.py.

---

### Task 12.3: Add export buttons to frontend

**File:** `apps/web/app/(dashboard)/admin/users/page.tsx` — Add "Export CSV" button that opens /api/v1/export/candidates in new tab
**File:** `apps/web/app/(dashboard)/interviews/page.tsx` — Add "Export CSV" button

---

## VERIFICATION

### Task 13.1: Backend test suite passes

**Steps:**
1. Run: `cd apps/api && pytest -v --tb=short`
2. Verify all tests pass (target: 50+ tests)
3. Run: `cd apps/api && pytest --cov=app --cov-report=term-missing`
4. Verify coverage > 60%

---

### Task 13.2: Frontend test suite passes

**Steps:**
1. Run: `cd apps/web && pnpm test`
2. Verify all tests pass (target: 15+ tests)

---

### Task 13.3: Frontend build passes

**Steps:**
1. Run: `cd apps/web && npx next build`
2. Verify no TypeScript errors
3. Verify all routes present

---

### Task 13.4: Backend imports all pass

**Steps:**
1. Run: `cd apps/api && python -c "from app.api.v1.router import api_router; print('OK')"`
2. Run: `cd apps/api && python -c "from app.models.audit_log import AuditLog; print('OK')"`
3. Verify no import errors

---

### Task 13.5: Docker build passes

**Steps:**
1. Run: `docker compose -f infra/docker-compose.yml build`
2. Verify all images build successfully
3. Run: `docker compose -f infra/docker-compose.yml up -d`
4. Wait for health checks to pass
5. Verify API responds at http://localhost:8000/health
6. Verify Web responds at http://localhost:3000

---

### Task 13.6: End-to-end smoke test

**Steps:**
1. Register a user via API
2. Login and get tokens
3. Create a candidate
4. Create an interview
5. Start the interview
6. Submit an answer
7. Close the interview
8. Generate a report
9. Verify all steps return expected status codes

---

## FILE SUMMARY

| Area | New Files | Modified Files |
|------|-----------|----------------|
| Backend tests | 10 test files | 1 conftest |
| Frontend tests | 3 test files | 1 package.json, 1 vitest config |
| Security | 4 files | 2 existing files |
| Error handling | 3 files | 5 existing files |
| Logging | 3 files | 1 existing file |
| Notifications | 1 file | 2 existing files |
| Audit logging | 4 files + 1 migration | 6 endpoint files, 1 sidebar |
| API docs | 0 | 10+ endpoint files |
| Performance | 2 files | 3 existing files |
| Deployment | 5 files | 2 existing files |
| Accessibility | 0 | 4 existing files |
| Data export | 3 files | 2 existing files, 1 sidebar |
| **Total** | **~38 new** | **~35 modified** |

Estimated implementation time: 8-10 hours.

---

## Execution Order

1. Tasks 1.1-1.13 (Backend tests) — foundation, no dependencies
2. Tasks 2.1-2.4 (Frontend tests) — can parallel with backend tests
3. Tasks 3.1-3.5 (Security) — no test dependencies
4. Tasks 4.1-4.3 (Error handling) — no dependencies
5. Tasks 5.1-5.3 (Logging) — no dependencies
6. Tasks 7.1-7.5 (Audit logging) — model + migration first, then service, then endpoints
7. Tasks 6.1-6.3 (Notifications) — depends on email config
8. Tasks 8.1-8.3 (API docs) — can be done anytime
9. Tasks 9.1-9.3 (Performance) — after tests pass
10. Tasks 10.1-10.7 (Deployment) — after all code is stable
11. Tasks 11.1-11.4 (Accessibility) — can be done anytime
12. Tasks 12.1-12.3 (Data export) — after audit logging
13. Tasks 13.1-13.6 (Verification) — last, after everything
