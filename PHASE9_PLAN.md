# Phase 9: Internationalization, AI Screening & Integrations — Granular Execution Plan (62 Tasks)

## Goal
Multi-language UI support, AI-powered resume screening and candidate ranking, third-party integrations (Slack, Teams, calendar, ATS), and professional email templates. This phase makes the platform globally usable and connectable to existing hiring workflows.

## Starting State
- Phase 1-8 complete: full interview flow, ML pipeline, results/reports, copilot, analytics, JD matching, async interviews, admin, testing, security, deployment, WebSocket, coding engine, question banks, candidate portal, webhooks, templates, rubric evaluation, organizations, scheduling, search, proctoring, plagiarism, GDPR, bulk ops, white-label
- UI is English-only
- Resume parsing exists but no automated screening/ranking
- No Slack/Teams notifications
- No calendar integration (Google/Outlook)
- No ATS integration (Greenhouse, Lever, Workday)
- Email service exists (SMTP) but no HTML templates

---

## INTERNATIONALIZATION (i18n)

### Task 1.1: Set up next-intl for frontend

**File:** `apps/web/i18n/request.ts`

Configure next-intl:
- Default locale: "en"
- Supported locales: ["en", "es", "fr", "de", "hi", "ja", "zh"]
- Locale detection: cookie → Accept-Language header → default
- Load messages from JSON files per locale

Install: `pnpm add next-intl`

**File:** `apps/web/i18n/routing.ts`

Define routing configuration:
- Locale prefix: "as-needed" (English at root, others prefixed: /es/interviews)
- Default locale: "en"

---

### Task 1.2: Create English message files

**File:** `apps/web/messages/en.json`

English translations organized by feature area:
- common: {loading, error, save, cancel, delete, confirm, search, noResults, back, next}
- auth: {login, register, email, password, fullName, role, forgotPassword}
- sidebar: {dashboard, interviews, candidates, copilot, analytics, schedule, templates, banks, admin, settings}
- interviews: {list, new, detail, live, results, report, replay, coaching, status, score, questions, shareLink}
- candidates: {list, new, detail, import, skills, resume}
- copilot: {suggestions, dismiss, start, active}
- analytics: {overview, trends, skills, history}
- admin: {users, system, health, audit}
- settings: {profile, privacy, branding, webhooks, organization}

Total: ~200 translation keys.

---

### Task 1.3: Create Spanish message file

**File:** `apps/web/messages/es.json`

Spanish translations for all keys in en.json.
Use professional translations (not machine-translated where possible).

---

### Task 1.4: Create French message file

**File:** `apps/web/messages/fr.json`

French translations for all keys.

---

### Task 1.5: Create remaining message files

**Files:** `apps/web/messages/de.json`, `hi.json`, `ja.json`, `zh.json`

German, Hindi, Japanese, Chinese translations.

---

### Task 1.6: Update app layout for i18n

**File:** `apps/web/middleware.ts`

Update middleware to handle locale routing:
- Detect locale from cookie or Accept-Language header
- Redirect to locale-prefixed path if non-default locale
- Pass locale to page props

**File:** `apps/web/app/layout.tsx`

Wrap app in NextIntlClientProvider with messages for detected locale.

**File:** `apps/web/app/[locale]/layout.tsx`

Locale-aware layout that loads correct messages.

---

### Task 1.7: Update components to use translations

**Files to update:** All page and component files

Replace hardcoded strings with `useTranslations` hook:
- `t('common.loading')` instead of "Loading..."
- `t('sidebar.interviews')` instead of "Interviews"
- `t('interviews.new')` instead of "New Interview"

Priority files (highest user-facing impact):
- Sidebar.tsx — navigation labels
- TopBar.tsx — search placeholder, user menu
- login/page.tsx, register/page.tsx — form labels
- interviews/page.tsx — table headers, empty states
- interview detail page — status labels, action buttons
- analytics/page.tsx — metric labels
- admin pages — table headers, filter labels

---

### Task 1.8: Add language switcher

**File:** `apps/web/components/shared/LanguageSwitcher.tsx`

Dropdown component:
- Shows current locale flag + name
- Dropdown lists all supported locales with flags
- On select: sets locale cookie, reloads page
- Flags: 🇺🇸 English, 🇪🇸 Spanish, 🇫🇷 French, 🇩🇪 German, 🇮🇳 Hindi, 🇯🇵 Japanese, 🇨🇳 Chinese

**File:** `apps/web/components/shared/TopBar.tsx` — Add LanguageSwitcher to top-right area

---

### Task 1.9: Backend i18n for email templates

**File:** `apps/api/app/core/i18n.py`

Backend translation utility:
- `get_translation(key: str, locale: str) -> str` — loads from JSON files
- Supported locales matching frontend
- Translation files: `apps/api/app/locales/en.json`, `es.json`, etc.

Used for: email subject lines, email body text, error messages in API responses (optional).

---

## AI RESUME SCREENING

### Task 2.1: Create screening service

**File:** `apps/api/app/services/screening_service.py`

Functions:
- `screen_candidate(candidate_id: uuid.UUID, job_description: str, db) -> dict` — analyzes candidate resume + skills against JD
- `rank_candidates(job_description: str, candidate_ids: list[uuid], db) -> list[dict]` — ranks multiple candidates by fit score
- `auto_screen_interview(interview_id: uuid.UUID, db) -> dict` — screens candidate automatically when interview is created

Screening logic:
- Extract required skills from JD (reuse jd_service.extract_skills_from_jd)
- Compare against candidate.extracted_skills
- Calculate match_percentage (reuse jd_service.calculate_match)
- Analyze resume text for keyword density
- Compute composite score: skill_match (60%) + experience_years (20%) + education_match (20%) (if available)
- Return: {score, breakdown: {skill_match, experience, education}, strengths: [], gaps: [], recommendation: "strong_fit"/"moderate_fit"/"weak_fit"}

---

### Task 2.2: Create screening model

**File:** `apps/api/app/models/screening_result.py`

Model `ScreeningResult`:
- id: UUID
- candidate_id: UUID (FK to candidates)
- job_description_hash: String (SHA256 of JD text, for caching)
- score: Float (0-100)
- breakdown: JSON ({skill_match, experience, education})
- strengths: JSON (list of strings)
- gaps: JSON (list of strings)
- recommendation: Enum (strong_fit, moderate_fit, weak_fit)
- created_at: DateTime

---

### Task 2.3: Create screening API endpoints

**File:** `apps/api/app/api/v1/screening.py`

Endpoints:
- `POST /screening/candidates/{candidate_id}` — Screen candidate against JD. Body: {job_description: str}. Auth required.
- `POST /screening/rank` — Rank multiple candidates. Body: {job_description: str, candidate_ids: list[uuid]}. Auth required.
- `GET /screening/candidates/{candidate_id}/history` — Get screening history for candidate. Auth required.

**Schema:** `apps/api/app/schemas/screening.py`
- ScreeningRequest: job_description (str, min_length=50)
- ScreeningResponse: candidate_id, score, breakdown, strengths, gaps, recommendation, created_at
- RankRequest: job_description (str), candidate_ids (list[str])
- RankResponse: rankings (list[ScreeningResponse])

**Router registration:** Add to router.py.
**Migration:** Generate migration for screening_results table.

---

### Task 2.4: Create screening frontend

**File:** `apps/web/hooks/useScreening.ts`
- `useScreenCandidate(candidateId)` — mutation, POST /screening/candidates/{id}
- `useRankCandidates()` — mutation, POST /screening/rank
- `useScreeningHistory(candidateId)` — query, GET /screening/candidates/{id}/history

**File:** `apps/web/app/(dashboard)/screening/page.tsx`

AI Screening page:
- Textarea for job description
- Multi-select candidate list (checkboxes)
- "Screen Candidates" button
- Results: ranked list with scores, strengths, gaps, recommendation badges
- Export results as CSV

**File:** `apps/web/components/screening/ScreeningResult.tsx`
- Score gauge (circular progress)
- Strengths (green chips)
- Gaps (red chips)
- Recommendation badge (strong=green, moderate=yellow, weak=red)

**Sidebar update:** Add "AI Screening" link. Route: /screening. Visible to interviewer and admin.

---

### Task 2.5: Integrate screening with interview creation

**File:** `apps/api/app/services/interview_service.py`

In `create_interview`:
- If job_description is provided in config, auto-run screening
- Store screening result link in interview metadata
- Include screening score in interview response

**File:** `apps/web/app/(dashboard)/interviews/new/page.tsx`

Add optional "Job Description" textarea in interview creation form.
If filled: run screening, show fit score before confirming interview creation.

---

## SLACK INTEGRATION

### Task 3.1: Create Slack integration service

**File:** `apps/api/app/services/slack_service.py`

Functions:
- `send_slack_notification(webhook_url: str, message: dict) -> bool` — sends message to Slack via incoming webhook
- `format_interview_completed(interview: Interview, candidate: Candidate) -> dict` — formats Slack message with blocks
- `format_report_ready(interview_id: str, score: float) -> dict`
- `format_daily_summary(interviews: list, stats: dict) -> dict`

Slack message format uses Block Kit:
- Header: "Interview Completed" / "Report Ready"
- Section: candidate name, score, question count
- Action: "View Report" button with link

---

### Task 3.2: Create Slack integration model and endpoints

**File:** `apps/api/app/models/slack_integration.py`

Model `SlackIntegration`:
- id: UUID
- organization_id: UUID (FK to organizations, nullable)
- user_id: UUID (FK to users)
- webhook_url: String (encrypted at rest)
- channel_name: String
- events: JSON (list of event types to notify)
- is_active: Boolean (default True)
- created_at: DateTime

**File:** `apps/api/app/api/v1/integrations.py`

Endpoints:
- `POST /integrations/slack` — Connect Slack webhook. Body: {webhook_url, channel_name, events}. Auth required.
- `GET /integrations/slack` — List Slack integrations. Auth required.
- `DELETE /integrations/slack/{id}` — Remove integration. Auth required.
- `POST /integrations/slack/{id}/test` — Send test message. Auth required.

**Schema:** `apps/api/app/schemas/integration.py`
- SlackConnectRequest: webhook_url (str), channel_name (str), events (list[str])
- SlackIntegrationResponse: id, channel_name, events, is_active, created_at

**Router registration:** Add to router.py.
**Migration:** Generate migration for slack_integrations table.

---

### Task 3.3: Fire Slack notifications from events

**File:** `apps/api/app/services/slack_service.py` (add function)

`notify_slack_integrations(event_type: str, payload: dict, db) -> None`:
- Find all active SlackIntegrations subscribed to event_type
- Send formatted message to each webhook URL
- Fire-and-forget via asyncio.create_task

Add to:
- interview_service.py — close_interview → "interview.completed"
- report generation → "report.generated"
- scheduling → "interview.scheduled" (24h before)

---

### Task 3.4: Create Slack integration frontend

**File:** `apps/web/hooks/useIntegrations.ts`
- `useSlackIntegrations()` — query
- `useConnectSlack()` — mutation
- `useDeleteSlack()` — mutation
- `useTestSlack()` — mutation

**File:** `apps/web/app/(dashboard)/settings/integrations/slack/page.tsx`

Slack integration page:
- Instructions: "Create an Incoming Webhook in Slack, paste the URL below"
- Form: webhook URL input, channel name input, event checkboxes
- Connected integrations list with delete/test buttons
- Status indicator (active/inactive)

---

## MICROSOFT TEAMS INTEGRATION

### Task 4.1: Create Teams integration service

**File:** `apps/api/app/services/teams_service.py`

Functions:
- `send_teams_notification(webhook_url: str, card: dict) -> bool` — sends Adaptive Card to Teams webhook
- `format_interview_card(interview, candidate) -> dict` — Teams Adaptive Card format
- `format_report_card(interview_id, score) -> dict`

Teams uses Office 365 Connectors with Incoming Webhooks. Message format is Adaptive Card JSON.

---

### Task 4.2: Create Teams integration model and endpoints

**File:** `apps/api/app/models/teams_integration.py`

Model `TeamsIntegration`:
- id: UUID
- organization_id: UUID (FK to organizations, nullable)
- user_id: UUID (FK to users)
- webhook_url: String (encrypted)
- channel_name: String
- events: JSON
- is_active: Boolean (default True)
- created_at: DateTime

**File:** `apps/api/app/api/v1/integrations.py` (add to existing file)

Endpoints:
- `POST /integrations/teams` — Connect Teams webhook
- `GET /integrations/teams` — List Teams integrations
- `DELETE /integrations/teams/{id}` — Remove integration
- `POST /integrations/teams/{id}/test` — Send test message

**Migration:** Generate migration for teams_integrations table.

---

### Task 4.3: Create Teams integration frontend

**File:** `apps/web/app/(dashboard)/settings/integrations/teams/page.tsx`

Teams integration page — same pattern as Slack.

**File:** `apps/web/app/(dashboard)/settings/integrations/page.tsx`

Integrations hub page:
- Grid of integration cards (Slack, Teams, Google Calendar, Outlook)
- Each card shows: icon, name, status (connected/not), "Connect" button
- Links to individual integration setup pages

---

## CALENDAR INTEGRATION

### Task 5.1: Create calendar service

**File:** `apps/api/app/services/calendar_service.py`

Functions:
- `create_google_calendar_event(credential: dict, slot: TimeSlot, interview: Interview, candidate: Candidate) -> str` — creates Google Calendar event, returns event_id
- `create_outlook_event(credential: dict, slot: TimeSlot, interview: Interview, candidate: Candidate) -> str` — creates Outlook event
- `sync_slot_to_calendar(slot_id: uuid.UUID, db) -> None` — syncs a booked slot to the interviewer's connected calendar
- `generate_ics_file(slot: TimeSlot, interview: Interview, candidate: Candidate) -> bytes` — generates .ics file for download

---

### Task 5.2: Create OAuth flow for Google Calendar

**File:** `apps/api/app/api/v1/auth_google.py`

Endpoints:
- `GET /auth/google/calendar` — Redirect to Google OAuth consent screen
- `GET /auth/google/calendar/callback` — Handle OAuth callback, store refresh token

**File:** `apps/api/app/models/calendar_credential.py`

Model `CalendarCredential`:
- id: UUID
- user_id: UUID (FK to users)
- provider: Enum (google, outlook)
- access_token: String (encrypted)
- refresh_token: String (encrypted)
- expires_at: DateTime
- created_at: DateTime

**Migration:** Generate migration for calendar_credentials table.

---

### Task 5.3: Create Outlook OAuth flow

**File:** `apps/api/app/api/v1/auth_outlook.py`

Endpoints:
- `GET /auth/outlook/calendar` — Redirect to Microsoft OAuth consent screen
- `GET /auth/outlook/calendar/callback` — Handle callback, store tokens

---

### Task 5.4: Integrate calendar sync with scheduling

**File:** `apps/api/app/services/scheduling_service.py`

In `book_slot`:
- After booking, call calendar_service.sync_slot_to_calendar
- Fire-and-forget: don't block booking if calendar sync fails
- Log failures for retry

---

### Task 5.5: Create calendar integration frontend

**File:** `apps/web/app/(dashboard)/settings/integrations/calendar/page.tsx`

Calendar integration page:
- "Connect Google Calendar" button → redirects to OAuth
- "Connect Outlook Calendar" button → redirects to OAuth
- Connected calendars list with disconnect button
- Toggle: "Auto-sync new bookings" (default: on)

**File:** `apps/web/components/scheduling/SlotPicker.tsx`

Add .ics download link after booking:
- "Add to Google Calendar" link
- "Add to Outlook" link
- "Download .ics" link

---

## ATS INTEGRATION

### Task 6.1: Create ATS integration abstraction

**File:** `apps/api/app/services/ats/base.py`

Abstract base class `ATSIntegration`:
- `push_candidate(candidate: Candidate) -> str` — pushes candidate to ATS, returns external ID
- `push_interview(interview: Interview, external_candidate_id: str) -> str` — pushes interview result
- `pull_candidates() -> list[dict]` — pulls candidates from ATS
- `sync_status(external_id: str) -> dict` — checks status in ATS

---

### Task 6.2: Create Greenhouse integration

**File:** `apps/api/app/services/ats/greenhouse.py`

Class `GreenhouseIntegration(ATSIntegration)`:
- Uses Greenhouse Harvest API (REST, API key auth)
- Push candidate as "candidate" entity
- Push interview score as "scorecard"
- Map our fields to Greenhouse fields

Config: API key, board token

---

### Task 6.3: Create Lever integration

**File:** `apps/api/app/services/ats/lever.py`

Class `LeverIntegration(ATSIntegration)`:
- Uses Lever API (REST, API key auth)
- Push candidate as "candidate" entity
- Push interview as "posting" application

Config: API key

---

### Task 6.4: Create ATS integration model and endpoints

**File:** `apps/api/app/models/ats_integration.py`

Model `ATSIntegration`:
- id: UUID
- organization_id: UUID (FK to organizations)
- provider: Enum (greenhouse, lever, workday)
- config: JSON (encrypted — API keys, board tokens)
- sync_direction: Enum (push, pull, bidirectional)
- is_active: Boolean (default True)
- last_sync_at: DateTime (nullable)
- created_at: DateTime

**File:** `apps/api/app/api/v1/integrations.py` (add to existing file)

Endpoints:
- `POST /integrations/ats` — Connect ATS. Body: {provider, config}. Auth required (admin).
- `GET /integrations/ats` — List ATS integrations. Auth required.
- `DELETE /integrations/ats/{id}` — Remove. Auth required (admin).
- `POST /integrations/ats/{id}/sync` — Trigger manual sync. Auth required (admin).
- `POST /integrations/ats/{id}/push/{interview_id}` — Push specific interview to ATS. Auth required.

**Migration:** Generate migration for ats_integrations table.

---

### Task 6.5: Create ATS integration frontend

**File:** `apps/web/app/(dashboard)/settings/integrations/ats/page.tsx`

ATS integration page:
- Provider selector (Greenhouse, Lever, Workday)
- Config form (API key, board token)
- "Test Connection" button
- "Sync Now" button
- Sync history log

---

## EMAIL TEMPLATES

### Task 7.1: Create email template engine

**File:** `apps/api/app/services/email_templates.py`

HTML email template system:
- Base template: professional layout with header, content area, footer
- Variables: {{candidate_name}}, {{interview_date}}, {{score}}, {{company_name}}, {{action_url}}
- Templates stored as Python strings (no external template files needed)

Templates to create:
- `interview_invitation` — sent when share link is created
- `interview_reminder` — sent 24h before scheduled interview
- `interview_completed` — sent to interviewer when interview completes
- `report_ready` — sent to candidate when report is generated
- `coaching_ready` — sent to candidate when coaching plan is ready
- `welcome` — sent after registration
- `password_reset` — sent when password is requested (future)

Each template has: subject, html_body, text_body (fallback).

---

### Task 7.2: Update email service to use templates

**File:** `apps/api/app/services/email_service.py`

Update existing functions:
- `send_interview_invitation_email(to, candidate_name, share_url, interviewer_name, locale)` — uses template
- `send_interview_reminder_email(to, candidate_name, interview_date, locale)` — uses template
- `send_report_ready_email(to, candidate_name, report_url, score, locale)` — uses template

Add locale parameter for i18n support in email subject/body.

---

### Task 7.3: Add email preview endpoint (dev only)

**File:** `apps/api/app/api/v1/dev.py`

Development-only endpoints (disabled in production):
- `GET /dev/email-preview/{template_name}` — renders email template with sample data, returns HTML
- Only accessible when ENVIRONMENT=development

---

### Task 7.4: Create email template preview in admin

**File:** `apps/web/app/(dashboard)/admin/emails/page.tsx`

Email template preview page (admin only):
- Dropdown to select template
- Preview rendered HTML in an iframe
- "Send Test Email" button → sends to admin's email

**Sidebar update:** Add "Email Templates" under Admin section.

---

## VERIFICATION

### Task 8.1: i18n test

**Steps:**
1. Set locale cookie to "es"
2. Navigate to /es/dashboard → verify Spanish labels
3. Switch to "fr" via LanguageSwitcher → verify French labels
4. Switch back to "en" → verify English labels
5. Verify all pages render without missing translation errors

---

### Task 8.2: Screening test

**Steps:**
1. Create candidate with known skills
2. POST /screening/candidates/{id} with JD → verify score and breakdown
3. POST /screening/rank with 3 candidates → verify ranked order
4. Verify caching: same JD + candidate → same result without recompute

---

### Task 8.3: Slack integration test

**Steps:**
1. Connect Slack webhook
2. POST test message → verify Slack receives message
3. Complete an interview → verify notification sent
4. Delete integration → verify no more notifications

---

### Task 8.4: Calendar integration test

**Steps:**
1. Connect Google Calendar (OAuth flow)
2. Book a slot → verify calendar event created
3. Cancel booking → verify calendar event deleted
4. Download .ics file → verify valid ICS format

---

### Task 8.5: ATS integration test

**Steps:**
1. Connect Greenhouse with test API key
2. Push interview result → verify Greenhouse receives scorecard
3. Pull candidates → verify candidates synced

---

### Task 8.6: Email template test

**Steps:**
1. Preview each template via admin page → verify HTML renders correctly
2. Send test email → verify received with correct formatting
3. Verify locale-specific templates render in correct language

---

### Task 8.7: Build and import verification

**Steps:**
1. `cd apps/api && python -c "from app.api.v1.router import api_router; print('OK')"`
2. `cd apps/web && npx next build` — verify no errors
3. `cd apps/api && pytest -v --tb=short` — verify all tests pass

---

## FILE SUMMARY

| Area | New Files | Modified Files |
|------|-----------|----------------|
| i18n | 10 files (7 messages + 3 config) | 15+ component files |
| AI Screening | 3 files + 1 migration | 2 existing files |
| Slack | 3 files + 1 migration | 2 existing files |
| Teams | 2 files + 1 migration | 1 existing file |
| Calendar | 4 files + 1 migration | 2 existing files |
| ATS | 5 files + 1 migration | 1 existing file |
| Email templates | 2 files | 2 existing files |
| Frontend | 10 files | 5 existing files |
| **Total** | **~42 new** | **~28 modified** |

Estimated implementation time: 10-12 hours.

---

## Execution Order

1. Tasks 1.1-1.9 (i18n) — foundational, affects all UI
2. Tasks 7.1-7.4 (Email templates) — no dependencies
3. Tasks 2.1-2.5 (AI Screening) — reuses existing JD service
4. Tasks 3.1-3.4 (Slack) — standalone
5. Tasks 4.1-4.3 (Teams) — same pattern as Slack
6. Tasks 5.1-5.5 (Calendar) — OAuth complexity
7. Tasks 6.1-6.5 (ATS) — most external dependencies
8. Tasks 8.1-8.7 (Verification) — after everything
