# Phase 10: Mobile, Accessibility, Performance & Scale — Final Phase (64 Tasks)

## Goal
Progressive Web App for mobile, WCAG 2.1 AA accessibility compliance, performance optimization (caching, CDN, lazy loading), load testing, feature flags, monitoring/alerting, and final production polish. This is the last phase — after this, the platform is enterprise-ready.

## Starting State
- Phase 1-9 complete: full interview flow, ML pipeline, results/reports, copilot, analytics, JD matching, async interviews, admin, testing, security, deployment, WebSocket, coding engine, question banks, candidate portal, webhooks, templates, rubric evaluation, organizations, scheduling, search, proctoring, plagiarism, GDPR, bulk ops, white-label, i18n, AI screening, Slack/Teams/calendar/ATS integrations, email templates
- No PWA support (not installable on mobile)
- No formal accessibility compliance
- No performance optimization beyond basic Next.js defaults
- No load testing
- No feature flags
- No monitoring/alerting beyond health checks
- No offline support

---

## PROGRESSIVE WEB APP (PWA)

### Task 1.1: Configure PWA manifest

**File:** `apps/web/public/manifest.json`

Web app manifest:
- name: "AI Interview Agent"
- short_name: "InterviewAI"
- start_url: "/dashboard"
- display: "standalone"
- background_color: "#ffffff"
- theme_color: "#3b82f6"
- icons: 192x192 and 512x512 PNG icons
- orientation: "any"
- categories: ["business", "productivity"]

**File:** `apps/web/public/icons/`

Generate app icons:
- icon-192.png (192x192)
- icon-512.png (512x512)
- apple-touch-icon.png (180x180)
- favicon.ico (32x32)

---

### Task 1.2: Set up service worker

**File:** `apps/web/next.config.ts`

Configure next-pwa:
- Install: `pnpm add next-pwa`
- Enable PWA in next.config.ts
- Runtime caching strategies:
  - Network-first for API calls (GET requests)
  - Cache-first for static assets (JS, CSS, images)
  - Network-only for mutations (POST, PUT, DELETE)
- Offline fallback page

**File:** `apps/web/public/offline.html`

Offline fallback page:
- "You are offline" message
- "Please check your connection and try again"
- Retry button
- List of features that work offline (view cached interviews, view cached reports)

---

### Task 1.3: Add service worker registration

**File:** `apps/web/app/layout.tsx`

Register service worker:
- Import and register SW in useEffect
- Show "Install App" prompt when beforeinstallprompt event fires
- Track install state

**File:** `apps/web/components/shared/InstallPrompt.tsx`

Install prompt component:
- Shows banner: "Install AI Interview Agent for quick access"
- "Install" button triggers native install prompt
- "Dismiss" button hides for 7 days (localStorage)
- Only shows if not already installed

---

### Task 1.4: Add offline data caching

**File:** `apps/web/lib/offlineCache.ts`

Offline cache utility:
- `cacheInterviews(interviews: Interview[])` — stores in localStorage
- `getCachedInterviews()` — retrieves from localStorage
- `cacheReport(interviewId: string, report: Report)` — stores in localStorage
- `getCachedReport(interviewId: string)` — retrieves from localStorage
- Cache expiry: 24 hours

**File:** `apps/web/hooks/useInterview.ts`

Update useInterviews hook:
- On success: cache results to localStorage
- On network error: fall back to cached data
- Show "Viewing cached data" banner when offline

---

### Task 1.5: Add push notifications

**File:** `apps/api/app/services/push_service.py`

Push notification service:
- `subscribe(user_id: str, subscription: dict, db)` — stores push subscription
- `send_push(user_id: str, title: str, body: str, url: str, db)` — sends push notification
- Uses Web Push Protocol with VAPID keys

**File:** `apps/api/app/models/push_subscription.py`

Model `PushSubscription`:
- id: UUID
- user_id: UUID (FK to users)
- endpoint: String
- p256dh: String
- auth: String
- created_at: DateTime

**File:** `apps/api/app/api/v1/notifications.py`

Endpoints:
- `POST /notifications/subscribe` — Subscribe to push. Auth required.
- `POST /notifications/unsubscribe` — Unsubscribe. Auth required.
- `POST /notifications/test` — Send test notification. Auth required.

**File:** `apps/web/lib/pushNotifications.ts`

Frontend push utilities:
- `requestNotificationPermission()` — requests permission, returns granted boolean
- `subscribeToPush()` — creates push subscription, sends to API
- `unsubscribeFromPush()` — removes subscription

**File:** `apps/web/app/(dashboard)/settings/notifications/page.tsx`

Notification settings:
- Toggle: "Push notifications" (requests permission)
- Toggle: "Email notifications" (uses existing settings)
- Test notification button

**Migration:** Generate migration for push_subscriptions table.

---

### Task 1.6: Optimize mobile interview flow

**File:** `apps/web/app/interview/join/[token]/page.tsx`

Mobile optimizations:
- Full-width layout (no max-width constraint on small screens)
- Larger touch targets (min 44px) for buttons
- Swipe gestures for navigating between questions
- Auto-scroll to answer textarea when question appears
- Prevent zoom on input focus (font-size: 16px minimum)
- Safe area insets for notch devices

**File:** `apps/web/app/(dashboard)/interviews/[id]/live/page.tsx`

Mobile live interview:
- Stack layout instead of side-by-side on mobile
- Bottom sheet for copilot suggestions instead of sidebar
- Floating action button for key actions (submit answer, end interview)

---

## ACCESSIBILITY (WCAG 2.1 AA)

### Task 2.1: Add skip navigation link

**File:** `apps/web/components/shared/SkipNav.tsx`

Component:
- Visually hidden link "Skip to main content"
- Becomes visible on focus (Tab key)
- Links to #main-content anchor

**File:** `apps/web/app/(dashboard)/layout.tsx` — Add SkipNav before Sidebar
**File:** `apps/web/app/layout.tsx` — Add id="main-content" to main content area

---

### Task 2.2: Add ARIA labels to interactive elements

**Files to update:** All components with buttons, links, forms

Add aria-label or aria-labelledby to:
- Sidebar.tsx — nav role="navigation", aria-label="Main navigation"
- TopBar.tsx — search input aria-label="Search"
- All icon-only buttons — aria-label describing action
- StatusBadge.tsx — aria-label with full status text
- All form inputs — associated label elements (not just placeholder)
- Modal/dialog components — role="dialog", aria-modal="true"
- Toast notifications — role="alert", aria-live="polite"

---

### Task 2.3: Ensure keyboard navigation works

**Files to update:** All interactive components

Verify and fix:
- All interactive elements are focusable (button, a, input, select, textarea, or tabindex=0)
- Focus order follows visual order (left-to-right, top-to-bottom)
- Focus is visible (outline or ring style on focus-visible)
- Escape closes modals/dropdowns
- Tab traps in modals (focus stays within modal while open)
- Arrow keys navigate within lists/menus (role="menu", role="listbox")

Specific fixes:
- Dropdown menus: arrow key navigation, Enter to select
- Tabs (chart tabs, filter tabs): arrow key navigation between tabs
- Table rows: Enter to navigate to detail
- Sidebar: arrow key navigation between nav items

---

### Task 2.4: Add color contrast compliance

**Files to update:** Tailwind config, component files

Audit and fix:
- Text on backgrounds must have 4.5:1 contrast ratio (AA)
- Large text (18px+) must have 3:1 ratio
- Interactive elements must have 3:1 against adjacent colors
- Focus indicators must have 3:1 against background

Common fixes:
- `text-muted-foreground` on white — verify contrast (may need darker shade)
- Disabled buttons — ensure still perceivable
- Error text on white — verify red shade has enough contrast
- Link colors on various backgrounds

---

### Task 2.5: Add screen reader support

**Files to update:** Key components

Add:
- `aria-live="polite"` regions for dynamic content (suggestions appearing, score updates)
- `aria-busy="true"` during loading states
- `aria-expanded` on collapsible sections (question breakdown)
- `aria-selected` on selected tabs
- `aria-current="page"` on active sidebar link
- `role="status"` for loading spinners
- `role="alert"` for error messages
- Descriptive alt text for any images/charts (or aria-label on the container)

---

### Task 2.6: Add form accessibility

**Files to update:** All form components

Ensure:
- Every input has an associated `<label>` (not just placeholder)
- Error messages are linked via `aria-describedby`
- Required fields have `aria-required="true"`
- Invalid fields have `aria-invalid="true"`
- Form submission errors are announced via `aria-live`

---

### Task 2.7: Add accessibility testing

**File:** `apps/web/tests/accessibility.test.ts`

Automated accessibility tests:
- Install: `pnpm add -D @axe-core/react jest-axe`
- Test each major page for axe violations
- Test keyboard navigation paths
- Test screen reader announcements (via testing-library)

---

## PERFORMANCE OPTIMIZATION

### Task 3.1: Add Next.js image optimization

**Files to update:** All components using `<img>` tags

Replace with Next.js `<Image>` component:
- Automatic WebP/AVIF conversion
- Lazy loading by default
- Responsive srcset
- Blur placeholder while loading

Specific files:
- Logo images in Sidebar, TopBar
- Candidate avatars (if added)
- Report charts (if exported as images)

---

### Task 3.2: Add code splitting and lazy loading

**File:** `apps/web/app/(dashboard)/interviews/[id]/results/page.tsx`

Lazy load heavy components:
- Chart components (recharts) — load only when Charts tab is visible
- Monaco editor (coding page) — load only when coding question is active
- PDF viewer (report page) — load only when user clicks download

Pattern: `const Chart = dynamic(() => import('@/components/charts/ScoreBarChart'), { loading: () => <ChartSkeleton /> })`

---

### Task 3.3: Add API response caching headers

**File:** `apps/api/app/main.py`

Add Cache-Control middleware:
- GET /analytics/* → Cache-Control: max-age=60 (1 minute)
- GET /candidates → Cache-Control: max-age=30
- GET /interviews → Cache-Control: max-age=10
- GET /admin/system/* → Cache-Control: max-age=30
- POST/PUT/PATCH/DELETE → Cache-Control: no-store
- Add ETag support for GET endpoints

---

### Task 3.4: Add database query optimization

**File:** `apps/api/app/services/analytics_service.py`

Optimize overview endpoint:
- Combine 6 queries into 2 using CTEs or subqueries
- Add database indexes for common filter columns

**File:** `apps/api/app/services/search_service.py`

Optimize search:
- Add GIN indexes on JSON columns (extracted_skills, tags) for faster search
- Use database-level full-text search (PostgreSQL tsvector) instead of ILIKE

**Migration:** Add indexes:
- `candidates_extracted_skills_gin` on candidates.extracted_skills
- `questions_text_search` on questions.question_text (tsvector)
- `interviews_status_created` on interviews(status, created_at)

---

### Task 3.5: Add Redis caching for hot paths

**File:** `apps/api/app/core/cache.py`

Expand caching:
- Cache user sessions (auth/me endpoint) — 5 minutes
- Cache candidate details — 2 minutes
- Cache question bank contents — 5 minutes
- Cache organization branding — 10 minutes
- Cache invalidation on write operations

---

### Task 3.6: Add frontend bundle analysis

**File:** `apps/web/package.json`

Add script: `"analyze": "ANALYZE=true next build"`

Install: `pnpm add -D @next/bundle-analyzer`

**File:** `apps/web/next.config.ts`

Add bundle analyzer plugin (conditional on ANALYZE env var).

Run and identify:
- Largest chunks (recharts, monaco, etc.)
- Duplicate dependencies
- Unused code that can be tree-shaken

---

### Task 3.7: Add compression and minification

**File:** `apps/web/next.config.ts`

Enable:
- gzip/brotli compression (Next.js does this by default in production)
- Verify static assets are compressed
- Add `compress: true` to next.config.ts if not default

**File:** `apps/api/app/main.py`

Add gzip middleware:
- `from fastapi.middleware.gzip import GZipMiddleware`
- `app.add_middleware(GZipMiddleware, minimum_size=1000)`

---

## LOAD TESTING

### Task 4.1: Create load test scenarios

**File:** `tests/load/locustfile.py`

Locust load test scenarios:
- `InterviewFlow` — full interview lifecycle (register → create → start → answer → close)
- `ConcurrentUsers` — 100 concurrent users browsing interviews
- `AnalyticsLoad` — concurrent analytics queries
- `SearchLoad` — concurrent search queries
- `WebSocketLoad` — concurrent WebSocket connections

Install: `pip install locust`

---

### Task 4.2: Create load test configuration

**File:** `tests/load/config.py`

Configuration:
- Target URL (env variable)
- User credentials for test accounts
- Think time between requests (1-5 seconds)
- Ramp-up period (30 seconds to reach target users)

---

### Task 4.3: Run load tests and document results

**Steps:**
1. Start infrastructure (Docker Compose)
2. Run: `cd tests/load && locust -f locustfile.py --headless -u 50 -r 10 -t 60s --host http://localhost:8000`
3. Record: requests/second, p50/p95/p99 latency, error rate
4. Identify bottlenecks (slow queries, memory usage, CPU)
5. Fix top 3 bottlenecks
6. Re-run to verify improvement

**File:** `tests/load/RESULTS.md` — Document load test results and improvements

---

### Task 4.4: Add connection pooling

**File:** `apps/api/app/core/database.py`

Optimize SQLAlchemy connection pool:
- pool_size: 20 (default 5)
- max_overflow: 10
- pool_timeout: 30
- pool_recycle: 1800 (recycle connections every 30 minutes)
- pool_pre_ping: True (verify connection before use)

---

## FEATURE FLAGS

### Task 5.1: Create feature flag service

**File:** `apps/api/app/services/feature_flags.py`

Simple feature flag system:
- `is_enabled(flag_name: str, user_id: uuid = None, org_id: uuid = None) -> bool`
- Flags stored in database (not just env vars, so they can be toggled at runtime)
- Support: global flags, per-organization flags, per-user flags
- Cache flags in Redis with 60-second TTL

---

### Task 5.2: Create feature flag model

**File:** `apps/api/app/models/feature_flag.py`

Model `FeatureFlag`:
- id: UUID
- name: String (unique, e.g. "coding_questions", "proctoring", "ai_screening")
- description: String
- is_enabled: Boolean (global toggle)
- enabled_for_orgs: JSON (list of org IDs, nullable — for org-specific rollout)
- enabled_for_users: JSON (list of user IDs, nullable — for user-specific rollout)
- created_at: DateTime
- updated_at: DateTime

---

### Task 5.3: Create feature flag API and admin UI

**File:** `apps/api/app/api/v1/feature_flags.py`

Endpoints:
- `GET /feature-flags` — List all flags. Admin only.
- `PATCH /feature-flags/{name}` — Toggle flag. Admin only.
- `GET /feature-flags/check/{name}` — Check if flag is enabled for current user. Auth required.

**File:** `apps/web/app/(dashboard)/admin/feature-flags/page.tsx`

Feature flags admin page:
- Table: flag name, description, global toggle, org list, user list
- Toggle switches for each flag
- Search/filter by flag name

**File:** `apps/web/hooks/useFeatureFlags.ts`
- `useFeatureFlags()` — query, GET /api/v1/feature-flags
- `useIsFeatureEnabled(flagName)` — query, GET /api/v1/feature-flags/check/{name}
- `useToggleFeatureFlag()` — mutation, PATCH /api/v1/feature-flags/{name}

**Migration:** Generate migration for feature_flags table.

---

### Task 5.4: Apply feature flags to existing features

Wrap behind feature flags:
- Coding questions: flag "coding_questions"
- Proctoring: flag "proctoring"
- AI screening: flag "ai_screening"
- Plagiarism detection: flag "plagiarism_detection"
- Push notifications: flag "push_notifications"
- Slack/Teams integrations: flag "team_integrations"
- ATS integrations: flag "ats_integrations"
- White-label branding: flag "white_label"

Pattern in frontend:
```
const { data: codingEnabled } = useIsFeatureEnabled("coding_questions");
if (codingEnabled) { /* show coding UI */ }
```

Pattern in backend:
```
if not is_enabled("proctoring", user_id=user.id): raise HTTPException(404)
```

---

## MONITORING & ALERTING

### Task 6.1: Add Prometheus metrics

**File:** `apps/api/app/core/metrics.py`

Prometheus metrics:
- `http_requests_total` (counter) — labels: method, path, status
- `http_request_duration_seconds` (histogram) — labels: method, path
- `active_websocket_connections` (gauge)
- `database_query_duration_seconds` (histogram)
- `celery_task_duration_seconds` (histogram) — labels: task_name
- `feature_flag_checks_total` (counter) — labels: flag_name, result

Install: `pip add prometheus-client`

**File:** `apps/api/app/main.py`

Add Prometheus middleware:
- Track request count, duration, status codes
- Expose /metrics endpoint for scraping

---

### Task 6.2: Add structured logging with correlation IDs

**File:** `apps/api/app/core/logging_config.py`

Enhance logging:
- Add correlation_id to all log entries (from request.state.request_id)
- Add user_id to authenticated request logs
- Add duration_ms to response logs
- Log levels: DEBUG for DB queries, INFO for requests, WARNING for retries, ERROR for failures

---

### Task 6.3: Add Sentry error tracking

**File:** `apps/api/app/main.py`

Configure Sentry:
- Install: `pip install sentry-sdk[fastapi]`
- `sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.ENVIRONMENT, traces_sample_rate=0.1)`
- Auto-capture unhandled exceptions
- Capture performance traces for slow endpoints

**File:** `apps/web/next.config.ts`

Configure Sentry for frontend:
- Install: `pnpm add @sentry/nextjs`
- Capture client-side errors
- Capture performance traces
- Source maps upload for stack traces

Add SENTRY_DSN to config (backend) and NEXT_PUBLIC_SENTRY_DSN (frontend).

---

### Task 6.4: Add uptime monitoring endpoint

**File:** `apps/api/app/api/v1/monitoring.py`

Endpoints:
- `GET /monitoring/health` — Detailed health check (same as admin/system/health but public, no auth)
- `GET /monitoring/ready` — Readiness probe (checks DB + Redis connectivity)
- `GET /monitoring/live` — Liveness probe (returns 200 if process is running)

These endpoints are for Kubernetes/load balancer health checks.

---

### Task 6.5: Create monitoring dashboard page

**File:** `apps/web/app/(dashboard)/admin/monitoring/page.tsx`

Monitoring dashboard (admin only):
- System health status (green/yellow/red)
- Request rate chart (last 1 hour)
- Error rate chart (last 1 hour)
- Response time percentiles (p50, p95, p99)
- Active WebSocket connections
- Database connection pool stats
- Redis memory usage
- Auto-refreshes every 30 seconds

---

## FINAL POLISH

### Task 7.1: Add favicon and meta tags

**File:** `apps/web/app/layout.tsx`

Update metadata:
- title: "AI Interview Agent"
- description: "AI-powered interview platform for technical hiring"
- openGraph: title, description, image
- twitter: card, title, description
- icons: favicon, apple-touch-icon

**File:** `apps/web/public/` — Ensure favicon.ico, apple-touch-icon.png, og-image.png exist

---

### Task 7.2: Add error pages

**File:** `apps/web/app/not-found.tsx`

Custom 404 page:
- "Page not found" message
- "Go to Dashboard" button
- Search bar

**File:** `apps/web/app/error.tsx`

Custom error page:
- "Something went wrong" message
- "Try Again" button
- "Go to Dashboard" link
- Error ID for support reference

**File:** `apps/web/app/(dashboard)/error.tsx`

Dashboard-specific error boundary:
- Same as above but within dashboard layout
- Preserves sidebar navigation

---

### Task 7.3: Add loading skeletons

**File:** `apps/web/components/shared/Skeleton.tsx`

Reusable skeleton components:
- `SkeletonCard` — card-shaped skeleton
- `SkeletonTable` — table with skeleton rows
- `SkeletonChart` — chart-shaped skeleton
- `SkeletonText` — text line skeleton (configurable width)

Apply to all pages that show loading states (replace "Loading..." text with skeletons).

---

### Task 7.4: Add keyboard shortcuts

**File:** `apps/web/lib/keyboardShortcuts.ts`

Global keyboard shortcuts:
- `Ctrl+K` / `Cmd+K` — Open search (already in Task 2.3 Phase 8)
- `Ctrl+N` / `Cmd+N` — New interview
- `Ctrl+/` / `Cmd+/` — Show keyboard shortcuts help
- `Escape` — Close modal/dropdown

**File:** `apps/web/components/shared/KeyboardShortcutsHelp.tsx`

Modal showing all available keyboard shortcuts:
- Triggered by Ctrl+/
- Grouped by context (Global, Interview, Navigation)
- Key + description for each shortcut

---

### Task 7.5: Add session timeout handling

**File:** `apps/web/lib/sessionTimeout.ts`

Session timeout utility:
- Track last activity timestamp
- Warning at 25 minutes of inactivity: "Your session will expire in 5 minutes"
- Auto-logout at 30 minutes of inactivity
- Reset timer on any user activity (mouse, keyboard, touch)

**File:** `apps/web/components/shared/SessionTimeoutWarning.tsx`

Warning modal:
- Countdown timer (5:00, 4:59, ...)
- "Stay Logged In" button → resets timer
- "Logout" button → immediate logout

---

### Task 7.6: Add dark mode improvements

**File:** `apps/web/app/layout.tsx`

Verify dark mode works across all new components:
- All Phase 7-9 components have dark: variants
- Charts use accessible colors in both themes
- Email templates look good in both themes (if rendered in-app)
- Code editor (Monaco) uses correct theme

**File:** `apps/web/components/ui/sonner.tsx`

Verify toast notifications look good in dark mode.

---

### Task 7.7: Add print-friendly styles

**File:** `apps/web/app/globals.css`

Add print media query:
- Hide sidebar, topbar, navigation
- Show full-width content
- Ensure charts render in print
- Page breaks between major sections
- White background regardless of theme

---

## VERIFICATION

### Task 8.1: PWA test

**Steps:**
1. Build production: `cd apps/web && pnpm build && pnpm start`
2. Open in Chrome → verify "Install" prompt appears
3. Install PWA → verify opens in standalone mode
4. Go offline → verify cached pages load
5. Verify push notifications work (subscribe, send test)

---

### Task 8.2: Accessibility test

**Steps:**
1. Run axe-core automated tests: `cd apps/web && pnpm test`
2. Manual keyboard navigation: Tab through all pages, verify focus order
3. Screen reader test: Use NVDA/VoiceOver, verify all content announced
4. Color contrast: Use browser DevTools audit, verify AA compliance
5. Verify skip nav link works

---

### Task 8.3: Performance test

**Steps:**
1. Run Lighthouse on key pages: Dashboard, Interview Detail, Analytics
2. Target: Performance score > 90, Accessibility > 95, Best Practices > 90
3. Verify First Contentful Paint < 1.5s
4. Verify Largest Contentful Paint < 2.5s
5. Verify Cumulative Layout Shift < 0.1
6. Run bundle analyzer → verify no unexpectedly large chunks

---

### Task 8.4: Load test

**Steps:**
1. Run Locust with 50 concurrent users for 60 seconds
2. Verify: p95 latency < 500ms, error rate < 1%
3. Verify: WebSocket connections stable under load
4. Verify: Database connections don't exhaust pool
5. Document results in tests/load/RESULTS.md

---

### Task 8.5: Feature flag test

**Steps:**
1. Disable "coding_questions" flag via admin UI
2. Verify coding question UI hidden from frontend
3. Verify coding API returns 404
4. Re-enable flag → verify features return
5. Test per-org flag: enable for one org only

---

### Task 8.6: Offline test

**Steps:**
1. Load dashboard with data → go offline
2. Verify cached interviews list visible
3. Verify "You are offline" banner appears
4. Try to create interview → verify appropriate error
5. Go online → verify auto-refresh

---

### Task 8.7: Final build verification

**Steps:**
1. `cd apps/api && pytest -v --tb=short` — all tests pass
2. `cd apps/web && pnpm test` — all tests pass
3. `cd apps/web && npx next build` — no errors
4. `docker compose -f infra/docker-compose.yml build` — all images build
5. `docker compose -f infra/docker-compose.yml up -d` — all services start
6. Full E2E smoke test: register → create interview → answer → report
7. Verify all 10 phases' features work end-to-end

---

## FILE SUMMARY

| Area | New Files | Modified Files |
|------|-----------|----------------|
| PWA | 6 files | 3 existing files |
| Accessibility | 3 files | 15+ existing files |
| Performance | 2 files | 8 existing files |
| Load testing | 3 files | 0 |
| Feature flags | 4 files + 1 migration | 3 existing files |
| Monitoring | 3 files | 2 existing files |
| Final polish | 8 files | 5 existing files |
| **Total** | **~32 new** | **~35 modified** |

Estimated implementation time: 8-10 hours.

---

## Execution Order

1. Tasks 3.1-3.7 (Performance) — foundational, improves everything
2. Tasks 2.1-2.7 (Accessibility) — affects all components
3. Tasks 1.1-1.6 (PWA) — depends on performance optimizations
4. Tasks 5.1-5.4 (Feature flags) — standalone
5. Tasks 6.1-6.5 (Monitoring) — standalone
6. Tasks 4.1-4.4 (Load testing) — after performance fixes
7. Tasks 7.1-7.7 (Final polish) — last, everything else is stable
8. Tasks 8.1-8.7 (Verification) — final validation

---

## PLATFORM COMPLETE

After Phase 10, the AI Interview Agent platform includes:

**Core:** Auth, candidates, interviews, questions, voice/video ML, results, reports, coaching, replay
**Advanced:** Copilot, analytics, JD matching, async interviews, admin, WebSocket, coding engine, question banks, candidate portal, webhooks, templates, rubric evaluation, organizations
**Enterprise:** Scheduling, search, proctoring, plagiarism, GDPR, bulk ops, white-label, i18n (7 languages), AI screening, Slack/Teams/calendar/ATS integrations, email templates
**Production:** Testing (backend + frontend), security hardening, deployment (Docker + CI/CD), PWA, accessibility, performance optimization, load testing, feature flags, monitoring/alerting

**Total across all phases: ~10 phases, ~650 tasks, ~280 new files, ~180 modified files.**
