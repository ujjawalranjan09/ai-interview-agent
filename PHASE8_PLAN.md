# Phase 8: Scheduling, Search, AI Proctoring & Compliance — Granular Execution Plan (65 Tasks)

## Goal
Interview scheduling with calendar integration, full-text search across the platform, AI-powered proctoring and plagiarism detection, GDPR compliance and data retention, bulk operations, and white-label branding for organizations. This phase completes the platform for enterprise readiness.

## Starting State
- Phase 1-7 complete: full interview flow, ML pipeline, results/reports, copilot, analytics, JD matching, async interviews, admin, testing, security, deployment, WebSocket, coding engine, question banks, candidate portal, webhooks, templates, rubric evaluation, organizations
- No scheduling system (interviews are created ad-hoc)
- No full-text search (users navigate by browsing lists)
- No proctoring (no verification that candidate is who they say)
- No plagiarism detection on code answers
- No GDPR compliance (no consent tracking, no data deletion)
- No bulk operations (one-at-a-time candidate/interview creation)
- No white-label branding (all orgs see same UI)
- No i18n (English only)

---

## INTERVIEW SCHEDULING

### Task 1.1: Create availability model

**File:** `apps/api/app/models/availability.py`

Model `Availability`:
- id: UUID
- user_id: UUID (FK to users — the interviewer)
- day_of_week: Integer (0=Monday, 6=Sunday)
- start_time: Time (e.g. 09:00)
- end_time: Time (e.g. 17:00)
- timezone: String (e.g. "America/New_York")
- is_active: Boolean (default True)
- created_at: DateTime

Model `TimeSlot`:
- id: UUID
- interviewer_id: UUID (FK to users)
- candidate_id: UUID (FK to candidates, nullable)
- interview_id: UUID (FK to interviews, nullable)
- start_time: DateTime (timezone-aware)
- end_time: DateTime (timezone-aware)
- status: Enum (available, booked, cancelled)
- created_at: DateTime

---

### Task 1.2: Create scheduling service

**File:** `apps/api/app/services/scheduling_service.py`

Functions:
- `set_availability(user_id, slots: list[dict], db) -> list[Availability]` — replaces user's availability with new slots
- `get_availability(user_id, db) -> list[Availability]`
- `generate_time_slots(interviewer_id, date_from, date_to, db) -> list[TimeSlot]` — generates available slots based on availability rules, excluding already-booked slots
- `book_slot(slot_id, candidate_id, interview_id, db) -> TimeSlot` — marks slot as booked
- `cancel_slot(slot_id, db) -> TimeSlot` — marks slot as cancelled
- `get_available_slots(interviewer_id, date_from, date_to, db) -> list[TimeSlot]` — returns only available slots for booking
- `get_interviewer_schedule(interviewer_id, date_from, date_to, db) -> list[TimeSlot]` — returns all slots (available + booked)

Slot generation logic:
- For each day in date range, check availability rules for that day_of_week
- Generate 30-minute or 60-minute slots (configurable) within the time window
- Skip slots that overlap with existing bookings
- Skip slots in the past

---

### Task 1.3: Create scheduling API endpoints

**File:** `apps/api/app/api/v1/scheduling.py`

Endpoints:
- `POST /scheduling/availability` — Set availability. Body: {slots: [{day_of_week, start_time, end_time, timezone}]}. Auth required (interviewer/admin).
- `GET /scheduling/availability` — Get own availability. Auth required.
- `GET /scheduling/slots` — Get available slots for an interviewer. Query: interviewer_id, date_from, date_to. Auth required.
- `GET /scheduling/schedule` — Get own schedule (all slots). Query: date_from, date_to. Auth required.
- `POST /scheduling/slots/{slot_id}/book` — Book a slot. Body: {candidate_id, interview_id}. Auth required.
- `POST /scheduling/slots/{slot_id}/cancel` — Cancel a booking. Auth required.

**Schema:** `apps/api/app/schemas/scheduling.py`
- AvailabilityCreate: day_of_week (int), start_time (str), end_time (str), timezone (str)
- AvailabilityResponse: id, user_id, day_of_week, start_time, end_time, timezone, is_active
- TimeSlotResponse: id, interviewer_id, candidate_id, interview_id, start_time, end_time, status
- BookSlotRequest: candidate_id (uuid), interview_id (uuid)

**Router registration:** Add to router.py.
**Migration:** Generate migration for availability and time_slots tables.

---

### Task 1.4: Create scheduling frontend

**File:** `apps/web/hooks/useScheduling.ts`
- `useAvailability()` — query, GET /api/v1/scheduling/availability
- `useSetAvailability()` — mutation, POST /api/v1/scheduling/availability
- `useAvailableSlots(interviewerId, dateFrom, dateTo)` — query, GET /api/v1/scheduling/slots
- `useMySchedule(dateFrom, dateTo)` — query, GET /api/v1/scheduling/schedule
- `useBookSlot()` — mutation, POST /api/v1/scheduling/slots/{id}/book
- `useCancelSlot()` — mutation, POST /api/v1/scheduling/slots/{id}/cancel

**File:** `apps/web/app/(dashboard)/scheduling/page.tsx` — Scheduling page with calendar view
**File:** `apps/web/components/scheduling/WeekCalendar.tsx` — Weekly calendar grid showing slots
**File:** `apps/web/components/scheduling/AvailabilityForm.tsx` — Form to set weekly availability
**File:** `apps/web/components/scheduling/SlotPicker.tsx` — Date/time picker for candidates to select a slot
**File:** `apps/web/app/interview/schedule/[token]/page.tsx` — Public page for candidates to pick a time slot (no auth)

**Sidebar update:** Add "Schedule" link. Route: /scheduling. Visible to interviewer and admin.

---

### Task 1.5: Integrate scheduling with interview creation

**File:** `apps/web/app/(dashboard)/interviews/new/page.tsx`

Add option: "Schedule for later" checkbox.
- If checked: show SlotPicker after interview is created
- On slot selection: book the slot and link it to the interview
- Interview status remains "draft" until the scheduled time

**File:** `apps/api/app/services/interview_service.py`

Add function `start_scheduled_interviews(db)`:
- Find all interviews with status "draft" that have a booked time slot starting within the next 5 minutes
- Call start_interview for each
- This function is called by a periodic task (Celery beat or cron)

---

## FULL-TEXT SEARCH

### Task 2.1: Create search service

**File:** `apps/api/app/services/search_service.py`

Functions:
- `search_all(query: str, user: User, db) -> dict` — searches across candidates, interviews, questions, banks
- `search_candidates(query: str, db) -> list[dict]` — full-text search on candidate name, email, skills
- `search_interviews(query: str, db) -> list[dict]` — search on interview status, candidate name
- `search_questions(query: str, db) -> list[dict]` — search on question text
- `search_banks(query: str, db) -> list[dict]` — search on bank title, description

Implementation:
- For PostgreSQL: use `text_col.ilike(f"%{query}%")` for simple search, or `func.to_tsvector` + `func.plainto_tsquery` for full-text search
- For SQLite (tests): use `text_col.contains(query)`
- Rank results by relevance (exact match > partial match)
- Limit to 20 results per category
- Scope results to user's organization if they belong to one

---

### Task 2.2: Create search API endpoint

**File:** `apps/api/app/api/v1/search.py`

Endpoint:
- `GET /search` — Global search. Query: q (string, min 2 chars), type (optional: candidates, interviews, questions, banks). Auth required.
- Returns: {candidates: [...], interviews: [...], questions: [...], banks: [...]} — each with id, title/subtitle, type badge, link

**Schema:** `apps/api/app/schemas/search.py`
- SearchResultItem: id (str), type (str), title (str), subtitle (str), link (str)
- SearchResponse: candidates (list), interviews (list), questions (list), banks (list), total (int)

**Router registration:** Add to router.py.

---

### Task 2.3: Create search frontend

**File:** `apps/web/components/shared/SearchBar.tsx`

Global search bar component:
- Appears in TopBar (top-right area)
- Keyboard shortcut: Ctrl+K or Cmd+K to focus
- Debounced search (300ms delay after typing stops)
- Dropdown shows results grouped by type (Candidates, Interviews, Questions, Banks)
- Each result is a link to the relevant page
- "No results" state
- Loading spinner while searching

**File:** `apps/web/hooks/useSearch.ts`
- `useSearch(query: string, type?: string)` — query, GET /api/v1/search?q=..., enabled when query.length >= 2, staleTime 10 seconds

**File:** `apps/web/components/shared/TopBar.tsx` — Add SearchBar component

---

## AI PROCTORING

### Task 3.1: Create proctoring service

**File:** `apps/api/app/services/proctoring_service.py`

Functions:
- `start_proctoring_session(interview_id, db) -> dict` — initializes proctoring for an interview, returns session config
- `analyze_frame(interview_id, frame_data: bytes, db) -> dict` — analyzes a video frame for proctoring signals
- `get_proctoring_report(interview_id, db) -> dict` — returns proctoring summary

Proctoring checks:
- Face detection: verify exactly one face is visible (reuse existing face detection from video emotion)
- Gaze detection: flag if candidate looks away for extended periods (> 5 seconds)
- Multiple faces: flag if more than one face detected
- Tab switch detection: frontend reports when candidate switches tabs (via Page Visibility API)
- Audio anomalies: flag sudden loud noises or extended silence

Each check produces a flag: {type, severity (info/warning/critical), timestamp, description}.

---

### Task 3.2: Create proctoring model

**File:** `apps/api/app/models/proctoring_session.py`

Model `ProctoringSession`:
- id: UUID
- interview_id: UUID (FK to interviews, unique)
- status: Enum (active, completed, reviewed)
- flags: JSON (list of {type, severity, timestamp, description})
- integrity_score: Float (0-100, starts at 100, reduced by flags)
- reviewed_by: UUID (FK to users, nullable)
- reviewed_at: DateTime (nullable)
- created_at: DateTime

---

### Task 3.3: Create proctoring API endpoints

**File:** `apps/api/app/api/v1/proctoring.py`

Endpoints:
- `POST /interviews/{id}/proctoring/start` — Start proctoring session. Auth required (interviewer/admin).
- `POST /interviews/{id}/proctoring/frame` — Upload video frame for analysis. Auth required.
- `POST /interviews/{id}/proctoring/flag` — Report a frontend-detected flag (tab switch, etc.). Auth required.
- `GET /interviews/{id}/proctoring/report` — Get proctoring report. Auth required (interviewer/admin).
- `PATCH /interviews/{id}/proctoring/review` — Mark as reviewed. Auth required (interviewer/admin).

**Schema:** `apps/api/app/schemas/proctoring.py`
- ProctoringFlag: type (str), severity (str), timestamp (str), description (str)
- ProctoringReport: interview_id, status, flags (list), integrity_score, reviewed_by, reviewed_at
- FrameUpload: frame (base64 string)
- FlagReport: type (str), description (str)

**Router registration:** Add to router.py.
**Migration:** Generate migration for proctoring_sessions table.

---

### Task 3.4: Create proctoring frontend

**File:** `apps/web/hooks/useProctoring.ts`
- `useStartProctoring(interviewId)` — mutation
- `useProctoringReport(interviewId)` — query
- `useReportFlag(interviewId)` — mutation

**File:** `apps/web/components/interview/ProctoringIndicator.tsx`
- Shows proctoring status (active/inactive) with colored dot
- Displays integrity score
- Lists recent flags

**File:** `apps/web/app/(dashboard)/interviews/[id]/proctoring/page.tsx`
- Proctoring report page for interviewers
- Shows integrity score gauge
- Timeline of flags with severity color coding
- "Mark as Reviewed" button
- Video frame thumbnails (if frames were captured)

**File:** `apps/web/lib/proctoring.ts`
- Tab visibility detection: listen to `visibilitychange` event, report flag when tab becomes hidden
- Webcam frame capture: take snapshot every 10 seconds during live interview (with candidate consent)
- Send frames to proctoring API

**Update:** `apps/web/app/(dashboard)/interviews/[id]/live/page.tsx`
- Add ProctoringIndicator to the interview UI
- Start tab visibility monitoring when interview starts
- If proctoring is active, capture webcam frames periodically

---

## PLAGIARISM DETECTION

### Task 4.1: Create plagiarism detection service

**File:** `apps/api/app/services/plagiarism_service.py`

Functions:
- `check_code_plagiarism(code: str, language: str, interview_id: uuid.UUID, db) -> dict` — compares submitted code against other submissions for the same coding question
- `check_text_plagiarism(answer: str, question_id: uuid.UUID, db) -> dict` — compares text answers against other answers for the same question

Detection methods:
- Code: normalize whitespace, compare AST similarity (for Python: use `ast.dump`), compute Jaccard similarity on token sets
- Text: compute cosine similarity on TF-IDF vectors (use sklearn if available, else simple word overlap)
- Threshold: > 70% similarity → flag as potential plagiarism

Return: {is_plagiarized: bool, similarity: float, matched_submission_id: str (nullable), details: str}

---

### Task 4.2: Create plagiarism model and endpoints

**File:** `apps/api/app/models/plagiarism_check.py`

Model `PlagiarismCheck`:
- id: UUID
- submission_type: Enum (code, text)
- submission_id: UUID (FK to question or coding_question)
- matched_submission_id: UUID (nullable)
- similarity: Float
- is_plagiarized: Boolean
- details: JSON
- created_at: DateTime

**File:** `apps/api/app/api/v1/plagiarism.py`

Endpoints:
- `GET /plagiarism/checks` — List plagiarism checks. Filters: interview_id, is_plagiarized. Auth required (interviewer/admin).
- `GET /plagiarism/checks/{id}` — Get check details. Auth required.

**Router registration:** Add to router.py.
**Migration:** Generate migration for plagiarism_checks table.

---

### Task 4.3: Integrate plagiarism into answer flow

**File:** `apps/api/app/api/v1/questions.py`

After evaluating an answer:
- Call plagiarism_service.check_text_plagiarism asynchronously
- If flagged, create PlagiarismCheck record

**File:** `apps/api/app/api/v1/coding.py`

After code submission:
- Call plagiarism_service.check_code_plagiarism asynchronously
- If flagged, create PlagiarismCheck record

---

### Task 4.4: Create plagiarism frontend

**File:** `apps/web/hooks/usePlagiarism.ts`
- `usePlagiarismChecks(filters)` — query, GET /api/v1/plagiarism/checks

**File:** `apps/web/app/(dashboard)/plagiarism/page.tsx` — Plagiarism dashboard
- Table of flagged submissions
- Similarity score column
- Link to compare side-by-side

**File:** `apps/web/components/plagiarism/PlagiarismBadge.tsx`
- Badge component: green (clean), yellow (suspicious > 50%), red (likely plagiarized > 70%)
- Shows similarity percentage

**Update:** `apps/web/app/(dashboard)/interviews/[id]/results/page.tsx`
- Show PlagiarismBadge next to answers that were checked

---

## GDPR COMPLIANCE

### Task 5.1: Create consent model

**File:** `apps/api/app/models/consent.py`

Model `Consent`:
- id: UUID
- user_id: UUID (FK to users, nullable — for anonymous candidates)
- candidate_id: UUID (FK to candidates, nullable)
- consent_type: Enum (data_processing, video_recording, audio_recording, analytics, marketing)
- granted: Boolean
- ip_address: String (nullable)
- user_agent: String (nullable)
- created_at: DateTime

---

### Task 5.2: Create consent service

**File:** `apps/api/app/services/consent_service.py`

Functions:
- `record_consent(user_id, candidate_id, consent_type, granted, ip_address, user_agent, db) -> Consent`
- `get_consents(user_id, db) -> list[Consent]`
- `has_consent(user_id, consent_type, db) -> bool` — checks latest consent for type
- `withdraw_consent(user_id, consent_type, db) -> Consent` — records withdrawal

---

### Task 5.3: Create data export service (GDPR right to portability)

**File:** `apps/api/app/services/gdpr_service.py`

Functions:
- `export_user_data(user_id, db) -> dict` — exports all data associated with a user: profile, candidates, interviews, answers, reports, coaching plans, emotion data
- `delete_user_data(user_id, db) -> bool` — anonymizes or deletes all user data: replaces PII with "[REDACTED]", deletes audio/video files from S3, keeps aggregated analytics

Deletion strategy:
- User record: anonymize email, name → "[Deleted User]"
- Candidates: anonymize name, email, delete resume from S3
- Interviews: keep record (for analytics) but anonymize candidate info
- Questions: keep answers (for aggregate stats) but anonymize
- Audio/Video: delete from S3
- Reports: delete
- Coaching plans: delete
- Emotion snapshots: delete

---

### Task 5.4: Create GDPR API endpoints

**File:** `apps/api/app/api/v1/gdpr.py`

Endpoints:
- `POST /gdpr/consent` — Record consent. Body: {consent_type, granted}. Auth required (or candidate token).
- `GET /gdpr/consent` — Get own consents. Auth required.
- `POST /gdpr/consent/withdraw` — Withdraw consent. Body: {consent_type}. Auth required.
- `GET /gdpr/export` — Export own data. Auth required. Returns JSON download.
- `POST /gdpr/delete` — Request data deletion. Auth required. Returns confirmation.
- `GET /gdpr/deletion-status` — Check deletion request status. Auth required.

**Schema:** `apps/api/app/schemas/gdpr.py`
- ConsentRequest: consent_type (str), granted (bool)
- ConsentResponse: id, consent_type, granted, created_at
- DataExportResponse: profile, candidates, interviews, reports (all as JSON)
- DeletionRequestResponse: status (str), estimated_completion (str)

**Router registration:** Add to router.py.
**Migration:** Generate migration for consents table.

---

### Task 5.5: Add consent collection to frontend

**File:** `apps/web/components/shared/ConsentBanner.tsx`

Cookie/consent banner:
- Shows on first visit (check localStorage)
- Options: "Accept All", "Reject Optional", "Customize"
- Required: data_processing (always on)
- Optional: analytics, marketing
- Stores consent via POST /gdpr/consent

**File:** `apps/web/app/(dashboard)/settings/privacy/page.tsx`

Privacy settings page:
- View current consents
- Toggle optional consents
- "Export My Data" button → downloads JSON
- "Delete My Account" button → confirmation dialog → POST /gdpr/delete

**File:** `apps/web/app/interview/join/[token]/page.tsx`

Before starting interview:
- Show consent checkboxes: "I consent to video recording", "I consent to audio recording"
- Must accept data_processing to proceed
- Record consent via API before starting

---

## BULK OPERATIONS

### Task 6.1: Create bulk import service

**File:** `apps/api/app/services/bulk_service.py`

Functions:
- `import_candidates_csv(file_bytes: bytes, db) -> dict` — parses CSV, creates candidates
  - Expected columns: name, email, skills (comma-separated)
  - Returns: {created: int, skipped: int, errors: [{row, reason}]}
  - Skip rows with duplicate emails
- `create_bulk_interviews(candidate_ids: list[uuid], config: dict, db) -> list[Interview]` — creates interviews for multiple candidates at once
  - Uses same config for all (difficulty, question_count, template)
  - Returns list of created interviews

---

### Task 6.2: Create bulk API endpoints

**File:** `apps/api/app/api/v1/bulk.py`

Endpoints:
- `POST /bulk/import/candidates` — Upload CSV file. Auth required (admin/interviewer). Uses `UploadFile` from FastAPI.
- `POST /bulk/create/interviews` — Create interviews for multiple candidates. Body: {candidate_ids: list[uuid], config: dict}. Auth required.

**Schema:** `apps/api/app/schemas/bulk.py`
- BulkImportResponse: created (int), skipped (int), errors (list[dict])
- BulkInterviewRequest: candidate_ids (list[str]), template_id (uuid, optional), difficulty (int, optional), question_count (int, optional)
- BulkInterviewResponse: created (int), interviews (list[dict])

**Router registration:** Add to router.py.

---

### Task 6.3: Create bulk operations frontend

**File:** `apps/web/hooks/useBulk.ts`
- `useImportCandidates()` — mutation, POST /bulk/import/candidates (FormData with file)
- `useBulkCreateInterviews()` — mutation, POST /bulk/create/interviews

**File:** `apps/web/app/(dashboard)/candidates/import/page.tsx`

Candidate import page:
- File upload area (drag & drop or click)
- CSV template download link
- Preview table showing first 10 rows
- "Import" button
- Results: created/skipped/errors summary

**File:** `apps/web/app/(dashboard)/interviews/bulk/page.tsx`

Bulk interview creation page:
- Multi-select candidate list (checkboxes)
- Option: "Use Template" or manual config
- "Create Interviews" button
- Results: number created

**Sidebar update:** Add "Import Candidates" and "Bulk Create" under Tools section.

---

## WHITE-LABEL BRANDING

### Task 7.1: Add branding fields to organization model

**File:** `apps/api/app/models/organization.py`

Add fields:
- primary_color: String (hex color, default "#3b82f6")
- secondary_color: String (hex color, default "#1e40af")
- logo_url: String (nullable, uploaded to S3)
- favicon_url: String (nullable)
- custom_domain: String (nullable, unique)
- email_from_name: String (nullable)
- email_from_address: String (nullable)

---

### Task 7.2: Create branding service

**File:** `apps/api/app/services/branding_service.py`

Functions:
- `get_branding(org_id, db) -> dict` — returns branding config for org
- `update_branding(org_id, data, db) -> Organization`
- `upload_logo(org_id, file_bytes, content_type, db) -> str` — uploads to S3, returns URL
- `get_branding_css(org_id, db) -> str` — generates CSS custom properties for branding colors

---

### Task 7.3: Create branding API endpoints

**File:** `apps/api/app/api/v1/branding.py`

Endpoints:
- `GET /organizations/{id}/branding` — Get branding. Members only.
- `PATCH /organizations/{id}/branding` — Update branding. Admin only.
- `POST /organizations/{id}/branding/logo` — Upload logo. Admin only. Uses UploadFile.
- `GET /branding/{org_slug}/css` — Public endpoint returning CSS for custom branding (for embedding).

**Schema:** `apps/api/app/schemas/branding.py`
- BrandingUpdate: primary_color (str), secondary_color (str), email_from_name (str), email_from_address (str)
- BrandingResponse: primary_color, secondary_color, logo_url, favicon_url, custom_domain, email_from_name

**Router registration:** Add to router.py.

---

### Task 7.4: Apply branding to frontend

**File:** `apps/web/lib/branding.ts`

Utility:
- `getBrandingColors()` — reads org branding from context or API, returns CSS variables
- Applies to document root via `document.documentElement.style.setProperty`

**File:** `apps/web/components/providers.tsx`

Add BrandingProvider:
- Fetches branding for user's organization on mount
- Sets CSS custom properties: --primary, --secondary
- All Tailwind `bg-primary`, `text-primary` etc. automatically use branded colors

**File:** `apps/web/app/(dashboard)/settings/branding/page.tsx`

Branding settings page for org admins:
- Color pickers for primary/secondary colors
- Logo upload with preview
- Preview panel showing how the branded UI looks
- Save button

---

## VERIFICATION

### Task 8.1: Scheduling test

**Steps:**
1. Set availability for an interviewer (Mon-Fri 9-17)
2. Generate time slots for next week → verify correct count
3. Book a slot → verify status changes to booked
4. Try to book same slot → verify 409
5. Cancel booking → verify status changes to cancelled

---

### Task 8.2: Search test

**Steps:**
1. Create candidates with known names/skills
2. GET /search?q=python → verify candidates with python in skills appear
3. GET /search?q=interview&type=interviews → verify filtered results
4. GET /search?q=ab → verify 400 (min 2 chars)

---

### Task 8.3: Proctoring test

**Steps:**
1. Start proctoring session for an interview
2. Report a "tab_switch" flag → verify flag recorded
3. Get proctoring report → verify flag appears, integrity_score < 100
4. Mark as reviewed → verify reviewed_by set

---

### Task 8.4: Plagiarism test

**Steps:**
1. Submit two identical text answers for the same question
2. Verify plagiarism check created with high similarity
3. Submit unique answer → verify no plagiarism flag

---

### Task 8.5: GDPR test

**Steps:**
1. Record consent for data_processing
2. GET /gdpr/consent → verify consent recorded
3. Withdraw consent → verify new record with granted=false
4. Export data → verify JSON contains user's interviews
5. Request deletion → verify user data anonymized

---

### Task 8.6: Bulk operations test

**Steps:**
1. Upload CSV with 5 candidates → verify 5 created
2. Upload same CSV → verify duplicates skipped
3. Bulk create interviews for 3 candidates → verify 3 interviews created

---

### Task 8.7: Branding test

**Steps:**
1. Update organization branding colors
2. GET /branding/{slug}/css → verify CSS contains custom colors
3. Upload logo → verify URL returned

---

### Task 8.8: Build and import verification

**Steps:**
1. `cd apps/api && python -c "from app.api.v1.router import api_router; print('OK')"`
2. `cd apps/web && npx next build` — verify no errors
3. `cd apps/api && pytest -v --tb=short` — verify all tests pass

---

## FILE SUMMARY

| Area | New Files | Modified Files |
|------|-----------|----------------|
| Scheduling | 6 files + 1 migration | 2 existing files |
| Full-text search | 3 files | 1 existing file |
| AI Proctoring | 4 files + 1 migration | 2 existing files |
| Plagiarism | 3 files + 1 migration | 2 existing files |
| GDPR | 5 files + 1 migration | 2 existing files |
| Bulk operations | 3 files | 2 existing files |
| White-label | 4 files | 2 existing files |
| Frontend components | 14 files | 5 existing files |
| **Total** | **~46 new** | **~18 modified** |

Estimated implementation time: 10-12 hours.

---

## Execution Order

1. Task 2.1-2.3 (Search) — simplest, no new models
2. Task 5.1-5.5 (GDPR) — foundational for compliance
3. Task 1.1-1.5 (Scheduling) — new models + service + frontend
4. Task 6.1-6.3 (Bulk operations) — no new models
5. Task 3.1-3.4 (Proctoring) — depends on existing video infrastructure
6. Task 4.1-4.4 (Plagiarism) — depends on coding + question endpoints
7. Task 7.1-7.4 (White-label) — depends on organizations from Phase 7
8. Task 8.1-8.8 (Verification) — after everything
