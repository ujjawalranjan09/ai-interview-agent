# Phase 7: Real-Time, Advanced ML & Integrations — Granular Execution Plan (68 Tasks)

## Goal
WebSocket real-time updates, coding interview engine, question bank system, candidate portal, webhook integrations, advanced answer evaluation, interview templates, and organization/team support. This phase transforms the platform from a single-user tool into a collaborative, extensible interview platform.

## Starting State
- Phase 1-6 complete: full interview flow, ML pipeline, results/reports/coaching, copilot, analytics, JD matching, async interviews, admin panel, testing, security, deployment
- SSE exists at `/api/v1/events/{interview_id}` for one-way server→client updates
- No WebSocket support
- No coding question execution
- No question bank (questions are generated per-interview)
- No candidate self-service portal
- No webhook/integration system
- No interview templates
- No organization/team model
- Answer evaluation is keyword-based placeholder for async mode

---

## WEBSOCKET REAL-TIME

### Task 1.1: Create WebSocket manager

**File:** `apps/api/app/core/websocket.py`

Create a connection manager class `ConnectionManager`:
- `active_connections: dict[str, list[WebSocket]]` — keyed by channel name (e.g. "interview:{id}", "copilot:{id}")
- `async connect(websocket: WebSocket, channel: str)` — accept connection, add to channel
- `async disconnect(websocket: WebSocket, channel: str)` — remove from channel
- `async broadcast(channel: str, message: dict)` — send JSON to all connections in channel
- `async send_personal(websocket: WebSocket, message: dict)` — send to one connection
- Thread-safe using asyncio locks

---

### Task 1.2: Create WebSocket authentication

**File:** `apps/api/app/core/ws_auth.py`

Function `authenticate_ws(websocket: WebSocket) -> User | None`:
- Extract token from query param: `ws://host/ws/interview/{id}?token=xxx`
- Verify JWT token using existing verify_token from security.py
- Load and return User from DB
- If invalid, close with code 4001 (unauthorized)
- Return None on failure

---

### Task 1.3: Create WebSocket endpoint for interviews

**File:** `apps/api/app/api/v1/ws.py`

WebSocket endpoint `ws /ws/interview/{interview_id}`:
- Authenticate via query param token
- Verify user has access to this interview (interviewer, admin, or candidate)
- Connect to channel "interview:{interview_id}"
- On message from client: parse JSON, handle commands:
  - {"type": "ping"} → respond with {"type": "pong"}
  - {"type": "answer", "question_id": "...", "answer_text": "..."} → process answer, broadcast score update
- Broadcast events to all connected clients:
  - {"type": "question_asked", "data": {question details}}
  - {"type": "answer_submitted", "data": {answer + score}}
  - {"type": "interview_completed", "data": {final score}}
  - {"type": "emotion_update", "data": {emotion data}}
- On disconnect: remove from channel

---

### Task 1.4: Create WebSocket endpoint for copilot

**File:** `apps/api/app/api/v1/ws.py` (add to same file)

WebSocket endpoint `ws /ws/copilot/{interview_id}`:
- Authenticate, verify interviewer/admin role
- Connect to channel "copilot:{interview_id}"
- On message: {"type": "request_suggestions"} → generate suggestions, send back
- Broadcast new suggestions when interview state changes
- Auto-push suggestions every 10 seconds while connected

---

### Task 1.5: Register WebSocket routes

**File:** `apps/api/app/main.py`

Add WebSocket routes:
- `app.websocket("/ws/interview/{interview_id}")(ws_interview_handler)`
- `app.websocket("/ws/copilot/{interview_id}")(ws_copilot_handler)`

---

### Task 1.6: Create frontend WebSocket hook for interviews

**File:** `apps/web/hooks/useInterviewWS.ts`

Hook `useInterviewWS(interviewId: string, token: string)`:
- Connects to `ws://host/ws/interview/{interviewId}?token={token}`
- Returns: { sendMessage, lastMessage, isConnected, disconnect }
- Auto-reconnect on disconnect (exponential backoff: 1s, 2s, 4s, max 30s)
- Parse incoming JSON messages
- On message callback: accepts a handler function

---

### Task 1.7: Create frontend WebSocket hook for copilot

**File:** `apps/web/hooks/useCopilotWS.ts`

Hook `useCopilotWS(interviewId: string, token: string)`:
- Connects to `ws://host/ws/copilot/{interviewId}?token={token}`
- Returns: { suggestions, requestSuggestions, isConnected }
- Auto-pushes suggestions to state when received
- Replaces polling-based useCopilotSuggestions

---

### Task 1.8: Update live interview page to use WebSocket

**File:** `apps/web/app/(dashboard)/interviews/[id]/live/page.tsx`

- Replace SSE-based useInterviewSSE with useInterviewWS
- Send answers via WebSocket instead of REST API
- Show real-time connection status indicator (green dot = connected, red = disconnected)
- Handle reconnection gracefully (show "Reconnecting..." banner)

---

### Task 1.9: Update copilot page to use WebSocket

**File:** `apps/web/app/(dashboard)/copilot/[id]/page.tsx`

- Replace polling-based useCopilotSuggestions with useCopilotWS
- Suggestions appear instantly instead of 5-second poll interval
- Show connection status in sidebar header

---

## CODING INTERVIEW ENGINE

### Task 2.1: Create code execution service

**File:** `apps/api/app/services/code_execution.py`

Service for running candidate code in a sandboxed environment:
- Function `execute_code(language: str, code: str, test_cases: list[dict], timeout: int = 10) -> dict`
- Supported languages: python, javascript, java, cpp
- For Python: use subprocess with timeout, capture stdout/stderr
- For others: use Docker containers with language-specific images (future: use subprocess for now with Python only)
- Return: {passed: int, total: int, results: [{input, expected_output, actual_output, passed, error}], execution_time_ms}
- Security: limit code length to 10000 chars, timeout to 30 seconds, no network access

---

### Task 2.2: Create coding question model

**File:** `apps/api/app/models/coding_question.py`

Model `CodingQuestion`:
- id: UUID
- question_id: UUID (FK to questions, nullable — links coding question to interview question)
- title: String (e.g. "Two Sum", "Reverse Linked List")
- description: Text (problem statement with examples)
- difficulty: Enum (easy, medium, hard)
- language: String (python, javascript, java, cpp)
- starter_code: Text (boilerplate code for candidate)
- solution_code: Text (reference solution, hidden from candidate)
- test_cases: JSON (list of {input, expected_output, is_hidden})
- time_limit_seconds: Integer (default 30)
- memory_limit_mb: Integer (default 256)
- created_at: DateTime

---

### Task 2.3: Create coding question service

**File:** `apps/api/app/services/coding_service.py`

Functions:
- `get_coding_question(question_id: uuid.UUID, db) -> CodingQuestion`
- `submit_code(coding_question_id: uuid.UUID, code: str, language: str, db) -> dict` — runs code against test cases, returns results
- `create_coding_question(data: dict, db) -> CodingQuestion` — creates a new coding question
- `list_coding_questions(difficulty: str, db) -> list[CodingQuestion]` — list by difficulty

---

### Task 2.4: Create coding question API endpoints

**File:** `apps/api/app/api/v1/coding.py`

Endpoints:
- `GET /coding/questions` — List coding questions. Filters: difficulty, language. Auth required.
- `GET /coding/questions/{id}` — Get coding question details (without solution). Auth required.
- `POST /coding/questions` — Create coding question. Admin/interviewer only.
- `POST /coding/questions/{id}/submit` — Submit code for evaluation. Returns test results. Auth required.
- `GET /coding/questions/{id}/submissions` — Get submission history for a question. Auth required.

**Schema:** `apps/api/app/schemas/coding.py`
- CodingQuestionResponse: id, title, description, difficulty, language, starter_code, test_cases (public only), time_limit
- CodeSubmissionRequest: code (str), language (str)
- CodeSubmissionResponse: passed (int), total (int), results (list), execution_time_ms (int), status (str)

**Router registration:** Add to router.py.

---

### Task 2.5: Create coding question seed data

**File:** `apps/api/app/seeds/coding_questions.py`

Script to seed 10 coding questions:
- 3 easy (Two Sum, Reverse String, Valid Palindrome)
- 4 medium (Longest Substring, Group Anagrams, Binary Tree Level Order, Merge Intervals)
- 3 hard (Trapping Rain Water, Median of Two Sorted Arrays, Word Ladder)

Each with: title, description (with examples), starter_code, solution_code, 5 test cases (3 public, 2 hidden).

Run via: `python -m app.seeds.coding_questions`

---

### Task 2.6: Create coding question schema and migration

**File:** `apps/api/app/schemas/coding.py` — schemas as described in 2.4
**Migration:** `alembic revision --autogenerate -m "add_coding_questions_table"`

---

### Task 2.7: Create code editor frontend component

**File:** `apps/web/components/coding/CodeEditor.tsx`

Component using Monaco Editor (VS Code editor):
- Props: language, starterCode, onChange, readOnly
- Install: `pnpm add @monaco-editor/react`
- Dark theme matching the app
- Language selector dropdown (python, javascript, java, cpp)
- Line numbers, syntax highlighting, autocomplete
- "Run" button and "Submit" button

---

### Task 2.8: Create test results component

**File:** `apps/web/components/coding/TestResults.tsx`

Component props: { results: {passed, total, cases: [{input, expected, actual, passed, error}]}, executionTime }

Render:
- Header: "X/Y test cases passed" with color (green if all pass, yellow if partial, red if none)
- Expandable list of test cases
- Each case shows: input, expected output, actual output, pass/fail indicator
- Hidden test cases show only pass/fail (no details)
- Execution time badge

---

### Task 2.9: Create coding question page

**File:** `apps/web/app/(dashboard)/coding/page.tsx`

Coding practice page:
- List of coding questions with difficulty filter tabs (All, Easy, Medium, Hard)
- Each question card: title, difficulty badge, language badge
- Click to open question in split view: problem description left, code editor right
- Run button → shows test results
- Submit button → saves submission, shows results

**File:** `apps/web/hooks/useCoding.ts`
- `useCodingQuestions(filters)` — query, GET /api/v1/coding/questions
- `useCodingQuestion(id)` — query, GET /api/v1/coding/questions/{id}
- `useSubmitCode(questionId)` — mutation, POST /api/v1/coding/questions/{id}/submit

---

### Task 2.10: Add coding questions to interview flow

**File:** `apps/api/app/services/question_service.py`

When generating questions for an interview:
- If interview config includes coding questions (config.coding_count > 0), include coding questions
- Link coding questions to interview questions via CodingQuestion.question_id

**File:** `apps/web/app/(dashboard)/interviews/[id]/live/page.tsx`

When current question is a coding question:
- Show CodeEditor instead of text AnswerInput
- Show TestResults after submission
- Allow multiple submissions (track best score)

---

## QUESTION BANK

### Task 3.1: Create question bank model

**File:** `apps/api/app/models/question_bank.py`

Model `QuestionBank`:
- id: UUID
- title: String (e.g. "Python Developer Questions", "Behavioral Questions")
- description: Text
- created_by: UUID (FK to users)
- is_public: Boolean (default False)
- question_count: Integer (default 0, denormalized)
- created_at: DateTime
- updated_at: DateTime

Model `BankQuestion`:
- id: UUID
- bank_id: UUID (FK to question_bank)
- question_text: Text
- question_type: Enum (technical, behavioral, resume, coding)
- difficulty: Enum (easy, medium, hard, expert)
- expected_answer: Text (nullable, reference answer for scoring)
- tags: JSON (list of skill/topic tags)
- metadata_: JSON (nullable)
- created_at: DateTime

---

### Task 3.2: Create question bank service

**File:** `apps/api/app/services/question_bank_service.py`

Functions:
- `create_bank(title, description, user_id, is_public, db) -> QuestionBank`
- `get_bank(bank_id, db) -> QuestionBank`
- `list_banks(user_id, db) -> list[QuestionBank]` — user's own + public banks
- `add_question_to_bank(bank_id, question_data, db) -> BankQuestion`
- `remove_question_from_bank(bank_id, question_id, db) -> bool`
- `get_bank_questions(bank_id, filters, db) -> list[BankQuestion]` — filter by type, difficulty, tags
- `import_questions_from_interview(bank_id, interview_id, db) -> int` — copy questions from an interview into a bank
- `generate_interview_from_bank(bank_id, count, difficulty, types, db) -> list[dict]` — pick random questions from bank matching filters

---

### Task 3.3: Create question bank API endpoints

**File:** `apps/api/app/api/v1/banks.py`

Endpoints:
- `POST /banks` — Create bank. Auth required.
- `GET /banks` — List banks (own + public). Auth required.
- `GET /banks/{id}` — Get bank details. Auth required.
- `DELETE /banks/{id}` — Delete bank (owner only). Auth required.
- `POST /banks/{id}/questions` — Add question to bank. Auth required.
- `GET /banks/{id}/questions` — List bank questions. Filters: type, difficulty. Auth required.
- `DELETE /banks/{id}/questions/{question_id}` — Remove question. Auth required.
- `POST /banks/{id}/generate` — Generate interview from bank. Body: {count, difficulty, types}. Auth required.
- `POST /banks/{id}/import/{interview_id}` — Import questions from interview. Auth required.

**Schema:** `apps/api/app/schemas/bank.py`
- BankCreate: title (str), description (str), is_public (bool)
- BankResponse: id, title, description, created_by, is_public, question_count, created_at
- BankQuestionCreate: question_text, question_type, difficulty, expected_answer, tags
- BankQuestionResponse: id, bank_id, question_text, question_type, difficulty, expected_answer, tags, created_at
- GenerateFromBankRequest: count (int), difficulty (str, optional), types (list[str], optional)

**Router registration:** Add to router.py.
**Migration:** Generate migration for question_bank and bank_questions tables.

---

### Task 3.4: Create question bank frontend

**File:** `apps/web/hooks/useBanks.ts`
- `useBanks()` — query, GET /api/v1/banks
- `useBank(id)` — query, GET /api/v1/banks/{id}
- `useCreateBank()` — mutation, POST /api/v1/banks
- `useBankQuestions(bankId, filters)` — query, GET /api/v1/banks/{id}/questions
- `useAddBankQuestion(bankId)` — mutation, POST /api/v1/banks/{id}/questions
- `useGenerateFromBank(bankId)` — mutation, POST /api/v1/banks/{id}/generate

**File:** `apps/web/app/(dashboard)/banks/page.tsx` — Question bank list page
**File:** `apps/web/app/(dashboard)/banks/[id]/page.tsx` — Bank detail with question list
**File:** `apps/web/components/banks/BankCard.tsx` — Bank card with title, count, visibility badge
**File:** `apps/web/components/banks/BankQuestionForm.tsx` — Form to add question to bank

**Sidebar update:** Add "Question Banks" link. Route: /banks. Visible to interviewer and admin.

---

## CANDIDATE PORTAL

### Task 4.1: Create candidate profile service

**File:** `apps/api/app/services/candidate_portal.py`

Functions:
- `get_candidate_dashboard(candidate_id, db) -> dict` — returns: upcoming_interviews, completed_interviews, average_score, recent_reports
- `get_candidate_interviews(candidate_id, filters, db) -> list[Interview]` — candidate's own interviews
- `get_candidate_reports(candidate_id, db) -> list[Report]` — candidate's own reports

---

### Task 4.2: Create candidate portal API endpoints

**File:** `apps/api/app/api/v1/portal.py`

Endpoints (all require auth, candidate role):
- `GET /portal/dashboard` — Returns dashboard summary
- `GET /portal/interviews` — List candidate's interviews. Filters: status.
- `GET /portal/interviews/{id}` — Get interview detail (own only)
- `GET /portal/reports` — List candidate's reports
- `GET /portal/reports/{id}` — Get report detail (own only)
- `GET /portal/coaching` — List candidate's coaching plans

Ownership enforced: candidate can only access their own data.

**Schema:** `apps/api/app/schemas/portal.py`
- DashboardResponse: upcoming (list), completed_count (int), average_score (float), recent_reports (list)
- PortalInterviewResponse: id, status, score, question_count, created_at

**Router registration:** Add to router.py.

---

### Task 4.3: Create candidate portal frontend

**File:** `apps/web/hooks/usePortal.ts`
- `usePortalDashboard()` — query, GET /api/v1/portal/dashboard
- `usePortalInterviews(filters)` — query, GET /api/v1/portal/interviews
- `usePortalReports()` — query, GET /api/v1/portal/reports

**File:** `apps/web/app/(portal)/layout.tsx` — Portal layout (simplified sidebar, candidate-focused)
**File:** `apps/web/app/(portal)/dashboard/page.tsx` — Candidate dashboard
**File:** `apps/web/app/(portal)/interviews/page.tsx` — Candidate's interviews
**File:** `apps/web/app/(portal)/reports/page.tsx` — Candidate's reports
**File:** `apps/web/app/(portal)/profile/page.tsx` — Candidate profile (edit name, view skills)

**Sidebar for portal:**
- Dashboard
- My Interviews
- My Reports
- Profile

**Middleware update:** Add /portal to protected routes. Candidates are redirected to /portal after login (instead of /dashboard).

---

## WEBHOOKS & INTEGRATIONS

### Task 5.1: Create webhook model

**File:** `apps/api/app/models/webhook.py`

Model `Webhook`:
- id: UUID
- user_id: UUID (FK to users, the webhook owner)
- url: String (target URL)
- events: JSON (list of event types to subscribe to, e.g. ["interview.completed", "report.generated"])
- secret: String (signing secret for HMAC verification)
- is_active: Boolean (default True)
- last_triggered_at: DateTime (nullable)
- failure_count: Integer (default 0)
- created_at: DateTime

---

### Task 5.2: Create webhook service

**File:** `apps/api/app/services/webhook_service.py`

Functions:
- `create_webhook(user_id, url, events, db) -> Webhook`
- `list_webhooks(user_id, db) -> list[Webhook]`
- `delete_webhook(webhook_id, user_id, db) -> bool`
- `trigger_webhooks(event_type: str, payload: dict, db) -> None` — find all active webhooks subscribed to event_type, send HTTP POST to each URL with signed payload
- `verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool` — HMAC-SHA256 verification

Signing: compute HMAC-SHA256 of JSON payload using webhook.secret, include in X-Webhook-Signature header.

Retry logic: if delivery fails (non-2xx), retry 3 times with exponential backoff (1s, 5s, 30s). After 3 failures, increment failure_count. After 10 consecutive failures, deactivate webhook.

---

### Task 5.3: Create webhook API endpoints

**File:** `apps/api/app/api/v1/webhooks.py`

Endpoints:
- `POST /webhooks` — Create webhook. Auth required.
- `GET /webhooks` — List webhooks. Auth required.
- `DELETE /webhooks/{id}` — Delete webhook. Auth required.
- `POST /webhooks/{id}/test` — Send test payload to webhook URL. Auth required.

**Schema:** `apps/api/app/schemas/webhook.py`
- WebhookCreate: url (str), events (list[str])
- WebhookResponse: id, url, events, is_active, last_triggered_at, failure_count, created_at
- WebhookTestResponse: status_code (int), response_body (str)

**Router registration:** Add to router.py.
**Migration:** Generate migration for webhooks table.

---

### Task 5.4: Fire webhooks from key events

Add webhook triggers to:
- `interview_service.py` — `close_interview`: fire "interview.completed" event with {interview_id, candidate_id, score, status}
- `report_service.py` — after report generation: fire "report.generated" event with {interview_id, report_id}
- `coaching_service.py` — after coaching generation: fire "coaching.generated" event with {interview_id, coaching_plan_id}
- `interview_service.py` — `generate_share_token`: fire "interview.shared" event with {interview_id, share_url}

Pattern: after main operation commits, call `asyncio.create_task(webhook_service.trigger_webhooks(...))` to fire webhooks asynchronously.

---

### Task 5.5: Create webhook management frontend

**File:** `apps/web/hooks/useWebhooks.ts`
- `useWebhooks()` — query, GET /api/v1/webhooks
- `useCreateWebhook()` — mutation, POST /api/v1/webhooks
- `useDeleteWebhook()` — mutation, DELETE /api/v1/webhooks/{id}
- `useTestWebhook()` — mutation, POST /api/v1/webhooks/{id}/test

**File:** `apps/web/app/(dashboard)/settings/webhooks/page.tsx` — Webhook management page
**File:** `apps/web/components/settings/WebhookForm.tsx` — Form to create webhook (URL, event checkboxes)
**File:** `apps/web/components/settings/WebhookList.tsx` — List of webhooks with delete/test buttons

---

## INTERVIEW TEMPLATES

### Task 6.1: Create interview template model

**File:** `apps/api/app/models/interview_template.py`

Model `InterviewTemplate`:
- id: UUID
- name: String (e.g. "Senior Python Developer", "Entry Level Behavioral")
- description: Text
- created_by: UUID (FK to users)
- config: JSON — stores: difficulty_level, question_count, question_types (with proportions), coding_count, time_limit_minutes, tags
- is_public: Boolean (default False)
- usage_count: Integer (default 0)
- created_at: DateTime
- updated_at: DateTime

---

### Task 6.2: Create interview template service

**File:** `apps/api/app/services/template_service.py`

Functions:
- `create_template(data, user_id, db) -> InterviewTemplate`
- `list_templates(user_id, db) -> list[InterviewTemplate]` — own + public
- `get_template(template_id, db) -> InterviewTemplate`
- `delete_template(template_id, user_id, db) -> bool`
- `create_interview_from_template(template_id, candidate_id, db) -> Interview` — creates interview using template config, increments usage_count

---

### Task 6.3: Create interview template API endpoints

**File:** `apps/api/app/api/v1/templates.py`

Endpoints:
- `POST /templates` — Create template. Auth required.
- `GET /templates` — List templates. Auth required.
- `GET /templates/{id}` — Get template. Auth required.
- `DELETE /templates/{id}` — Delete template. Owner only.
- `POST /templates/{id}/create-interview` — Create interview from template. Body: {candidate_id}. Auth required.

**Schema:** `apps/api/app/schemas/template.py`
- TemplateCreate: name, description, config (dict), is_public (bool)
- TemplateResponse: id, name, description, created_by, config, is_public, usage_count, created_at
- CreateFromTemplateRequest: candidate_id (uuid)

**Router registration:** Add to router.py.

---

### Task 6.4: Create template frontend

**File:** `apps/web/hooks/useTemplates.ts`
- `useTemplates()` — query
- `useCreateTemplate()` — mutation
- `useCreateFromTemplate()` — mutation

**File:** `apps/web/app/(dashboard)/templates/page.tsx` — Template list with "Use Template" button
**File:** `apps/web/components/templates/TemplateCard.tsx` — Template card with config summary
**File:** `apps/web/components/templates/TemplateForm.tsx` — Create/edit template form

**Update:** `apps/web/app/(dashboard)/interviews/new/page.tsx` — Add "Start from Template" option that shows template picker before creating interview.

**Sidebar update:** Add "Templates" link. Route: /templates. Visible to interviewer and admin.

---

## ADVANCED ANSWER EVALUATION

### Task 7.1: Create rubric-based evaluation service

**File:** `apps/api/app/services/rubric_evaluator.py`

Enhanced answer evaluation using rubrics:
- Function `evaluate_with_rubric(answer: str, question: dict, rubric: dict) -> dict`
- Rubric structure: {criteria: [{name, weight, description, keywords, max_score}]}
- Score each criterion separately, compute weighted average
- Return: {total_score, criteria_scores: [{name, score, max, feedback}], overall_feedback}
- Fallback: if no rubric, use existing keyword-based scoring

---

### Task 7.2: Create rubric model and seed data

**File:** `apps/api/app/models/rubric.py`

Model `Rubric`:
- id: UUID
- name: String (e.g. "Technical Depth", "Communication Skills")
- description: Text
- criteria: JSON (list of {name, weight, description, keywords, max_score})
- created_by: UUID (FK to users)
- created_at: DateTime

**File:** `apps/api/app/seeds/rubrics.py`

Seed 3 default rubrics:
- "Technical Depth" — criteria: accuracy (40%), depth (30%), examples (20%), clarity (10%)
- "Behavioral Response" — criteria: situation (25%), task (25%), action (25%), result (25%)
- "Communication" — criteria: clarity (30%), structure (25%), conciseness (25%), vocabulary (20%)

---

### Task 7.3: Integrate rubric evaluation into answer flow

**File:** `apps/api/app/services/question_service.py`

When evaluating answers:
- If question has an associated rubric, use rubric_evaluator
- Store criteria_scores in question.metadata_ JSON field
- Include criteria_scores in the response

**File:** `apps/api/app/api/v1/questions.py`

Update answer submission response to include criteria_scores when available.

---

### Task 7.4: Show rubric scores in frontend

**File:** `apps/web/components/interview/RubricScores.tsx`

Component props: { criteriaScores: {name, score, max, feedback}[] }

Render:
- Horizontal bar for each criterion
- Score / Max displayed
- Color coded (green if score/max > 0.8, yellow if > 0.5, red otherwise)
- Feedback text below each bar

**File:** `apps/web/app/(dashboard)/interviews/[id]/live/page.tsx` — Show RubricScores after answer submission when available
**File:** `apps/web/app/(dashboard)/interviews/[id]/results/page.tsx` — Show RubricScores in question breakdown

---

## ORGANIZATION / TEAM SUPPORT

### Task 8.1: Create organization model

**File:** `apps/api/app/models/organization.py`

Model `Organization`:
- id: UUID
- name: String
- slug: String (unique, URL-friendly)
- logo_url: String (nullable)
- settings: JSON (default branding, default interview config)
- created_at: DateTime

Add to User model:
- organization_id: UUID (nullable, FK to organizations)

---

### Task 8.2: Create organization service

**File:** `apps/api/app/services/org_service.py`

Functions:
- `create_organization(name, slug, creator_id, db) -> Organization` — creates org, sets creator's organization_id
- `get_organization(org_id, db) -> Organization`
- `list_organization_members(org_id, db) -> list[User]`
- `add_member(org_id, user_id, db) -> bool` — sets user's organization_id
- `remove_member(org_id, user_id, db) -> bool` — sets user's organization_id to None
- `update_organization(org_id, data, db) -> Organization`

---

### Task 8.3: Create organization API endpoints

**File:** `apps/api/app/api/v1/organizations.py`

Endpoints:
- `POST /organizations` — Create org. Auth required.
- `GET /organizations/{id}` — Get org. Members only.
- `PATCH /organizations/{id}` — Update org. Admin only.
- `GET /organizations/{id}/members` — List members. Members only.
- `POST /organizations/{id}/members/{user_id}` — Add member. Admin only.
- `DELETE /organizations/{id}/members/{user_id}` — Remove member. Admin only.

**Schema:** `apps/api/app/schemas/organization.py`
- OrgCreate: name (str), slug (str)
- OrgResponse: id, name, slug, logo_url, settings, created_at
- OrgMemberResponse: id, email, full_name, role, joined_at

**Router registration:** Add to router.py.
**Migration:** Add organizations table and organization_id column to users.

---

### Task 8.4: Add organization context to existing queries

**File:** `apps/api/app/api/v1/interviews.py`

When listing interviews:
- If user has organization_id, filter to interviews where candidate's organization matches
- Admin sees all org interviews, interviewer sees their own + org interviews

**File:** `apps/api/app/api/v1/analytics.py`

When fetching analytics:
- Scope to organization if user belongs to one

---

### Task 8.5: Create organization settings page

**File:** `apps/web/app/(dashboard)/settings/organization/page.tsx`

Page for org admins:
- Edit org name, logo
- Member management (list, add, remove)
- Default interview settings

**File:** `apps/web/hooks/useOrg.ts`
- `useOrganization(id)` — query
- `useOrgMembers(id)` — query
- `useUpdateOrganization()` — mutation
- `useAddMember()` — mutation
- `useRemoveMember()` — mutation

---

## VERIFICATION

### Task 9.1: WebSocket end-to-end test

**Steps:**
1. Start backend server
2. Connect to ws://localhost:8000/ws/interview/{id}?token=xxx using websocat or Python script
3. Send {"type": "ping"} → verify {"type": "pong"} received
4. Submit answer via REST → verify WebSocket receives answer_submitted event
5. Disconnect → verify clean removal from channel

---

### Task 9.2: Coding execution test

**Steps:**
1. Create a coding question via API
2. Submit correct Python code → verify all test cases pass
3. Submit incorrect code → verify failures reported
4. Submit code with infinite loop → verify timeout
5. Verify solution_code is not exposed in GET response

---

### Task 9.3: Question bank test

**Steps:**
1. Create a bank, add 10 questions
2. List banks → verify appears
3. Generate interview from bank → verify correct count
4. Import questions from existing interview → verify copied

---

### Task 9.4: Candidate portal test

**Steps:**
1. Login as candidate
2. GET /portal/dashboard → verify returns own data
3. GET /portal/interviews → verify only own interviews
4. Login as different candidate → verify cannot see first candidate's data

---

### Task 9.5: Webhook test

**Steps:**
1. Create webhook pointing to httpbin.org/post
2. Complete an interview → verify webhook fired
3. Check webhook signature verification
4. Test webhook with unreachable URL → verify failure_count increments

---

### Task 9.6: Template test

**Steps:**
1. Create template with specific config
2. Create interview from template → verify config matches
3. Verify usage_count incremented

---

### Task 9.7: Build and import verification

**Steps:**
1. `cd apps/api && python -c "from app.api.v1.router import api_router; print('OK')"`
2. `cd apps/web && npx next build` — verify no errors
3. `cd apps/api && pytest -v --tb=short` — verify all tests pass

---

## FILE SUMMARY

| Area | New Files | Modified Files |
|------|-----------|----------------|
| WebSocket | 4 files | 2 existing files |
| Coding engine | 6 files + 1 seed | 2 existing files |
| Question bank | 4 files + 1 migration | 2 existing files |
| Candidate portal | 5 files | 1 middleware |
| Webhooks | 4 files + 1 migration | 4 existing files |
| Templates | 4 files | 2 existing files |
| Rubric evaluation | 3 files + 1 seed | 3 existing files |
| Organizations | 4 files + 1 migration | 3 existing files |
| Frontend components | 12 files | 4 existing files |
| **Total** | **~47 new** | **~23 modified** |

Estimated implementation time: 10-12 hours.

---

## Execution Order

1. Task 1.1-1.9 (WebSocket) — foundation for real-time
2. Task 7.1-7.4 (Rubric evaluation) — improves answer quality
3. Task 3.1-3.4 (Question bank) — reusable question management
4. Task 6.1-6.4 (Templates) — depends on question bank
5. Task 2.1-2.10 (Coding engine) — standalone, can parallel with 3-6
6. Task 4.1-4.3 (Candidate portal) — standalone
7. Task 5.1-5.5 (Webhooks) — standalone
8. Task 8.1-8.5 (Organizations) — last, most cross-cutting
9. Task 9.1-9.7 (Verification) — after everything
