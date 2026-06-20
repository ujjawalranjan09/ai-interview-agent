# Phase 5: Advanced Features — Granular Execution Plan (60 Tasks)

## Goal
Copilot mode, analytics dashboard, JD matching with RAG, async interview mode, admin panel.
Each task below is a single, focused unit of work that an agent can execute in isolation.

## Starting State
- Phase 1-4 complete: auth, candidates, interviews, questions, voice/video ML, results, reports, coaching, replay
- Existing models: User (admin/interviewer/candidate roles), Candidate, Interview, Question, EmotionSnapshot, Report, CoachingPlan, CopilotSession
- Existing services: auth, candidate, interview, question, resume, audio, analytics, feedback, report, replay, coaching
- Existing API routers: auth, candidates, interviews, questions, events, reports, coaching, replay
- Existing frontend hooks: useAuth, useInterview, useInterviewSSE, useReport
- Existing frontend pages: login, register, dashboard, interviews list, interview detail, new interview, live interview, results, report, replay, coaching
- Constants already have COPILOT_SUGGESTION_TEMPLATES with 8 suggestion types
- CopilotSession model already exists (interview_id, interviewer_id, suggestions_log JSON, analytics JSON)
- basePath: "/dashboard" in next.config.ts
- All API calls go through apiFetch in lib/api.ts which prepends NEXT_PUBLIC_API_URL

---

## COPILOT MODE

### Task 1.1: Create copilot_service.py — suggestion selection logic

**File:** `apps/api/app/services/copilot_service.py`

Create the file with the suggestion selection function. This is the core logic that decides which suggestion types to generate based on answer score.

Build function `select_suggestion_types(answer_score: float) -> list[str]`:
- If score < 50: return ["rephrase", "encourage"]
- If score 50-79: return ["follow_up", "star_method"]
- If score >= 80: return ["probe_deeper", "strong_area"]
- Always append "gap_fill" to the returned list

This function is pure (no DB, no imports beyond typing). Test it by calling with different scores.

---

### Task 1.2: Create copilot_service.py — template rendering logic

**File:** `apps/api/app/services/copilot_service.py` (same file, add function)

Build function `render_suggestion(suggestion_type: str, context: dict) -> dict`:
- Takes a suggestion type (e.g. "follow_up") and a context dict with keys: topic, skill, concept
- Looks up the template list from COPILOT_SUGGESTION_TEMPLATES[suggestion_type]
- Picks a random template using random.choice
- Fills placeholders {topic}, {skill}, {concept} with values from context (use .format_map with a defaultdict that returns "this topic" for missing keys)
- Returns dict with keys: id (uuid4 hex), type, icon (from templates), color (from templates), text (rendered template), created_at (datetime.utcnow ISO string)

Imports needed: uuid, random, datetime, collections.defaultdict, app.core.constants.COPILOT_SUGGESTION_TEMPLATES

---

### Task 1.3: Create copilot_service.py — session management functions

**File:** `apps/api/app/services/copilot_session.py` (same file, add functions)

Build two functions:

`get_or_create_session(interview_id: uuid.UUID, interviewer_id: uuid.UUID, db: AsyncSession) -> CopilotSession`:
- SELECT from CopilotSession where interview_id matches
- If not found, create new CopilotSession(interview_id=interview_id, interviewer_id=interviewer_id)
- db.add, db.flush, return the session

`log_suggestion(session: CopilotSession, suggestion: dict) -> None`:
- Append suggestion dict to session.suggestions_log (which is a JSON list)
- If suggestions_log is None, initialize to empty list first
- No DB commit here — caller is responsible

Imports needed: uuid, sqlalchemy select, sqlalchemy.ext.asyncio.AsyncSession, app.models.copilot_session.CopilotSession

---

### Task 1.4: Create copilot_service.py — main generate_suggestions function

**File:** `apps/api/app/services/copilot_service.py` (same file, add function)

Build the main orchestrator function `generate_suggestions(interview_id: uuid.UUID, current_question_text: str, answer_text: str, answer_score: float, candidate_skills: list[str], db: AsyncSession) -> list[dict]`:

- Call select_suggestion_types(answer_score) to get types
- For each type, build a context dict:
  - "topic": extract from current_question_text (use first noun phrase or first 5 words)
  - "skill": pick first matching skill from candidate_skills if relevant, else "this area"
  - "concept": extract a key concept from answer_text (first 3 words or "your approach")
- Call render_suggestion(type, context) for each type
- Return the list of suggestion dicts (2-3 suggestions total)

This function ties together Tasks 1.1 and 1.2. No new imports needed.

---

### Task 1.5: Create copilot schema

**File:** `apps/api/app/schemas/copilot.py`

Create Pydantic v2 schemas:
- `CopilotSessionResponse`: id (str), interview_id (str), interviewer_id (str), created_at (str)
- `SuggestionResponse`: id (str), type (str), icon (str), color (str), text (str), created_at (str)
- `SuggestionsResponse`: suggestions (list[SuggestionResponse])
- `DismissRequest`: suggestion_id (str)

All fields use str (not uuid) so they serialize cleanly. Use model_config = ConfigDict(from_attributes=True) on CopilotSessionResponse.

---

### Task 1.6: Create copilot API — start endpoint

**File:** `apps/api/app/api/v1/copilot.py`

Create the router file with just the start endpoint first.

`POST /interviews/{interview_id}/copilot/start`:
- Requires auth via Depends(get_current_user)
- Check user.role in ("interviewer", "admin"), else 403
- Load Interview by interview_id, verify exists (404 if not)
- Call copilot_service.get_or_create_session(interview_id, user.id, db)
- Return CopilotSessionResponse

Router: `router = APIRouter(prefix="/interviews/{interview_id}/copilot", tags=["copilot"])`

---

### Task 1.7: Create copilot API — suggestions endpoint

**File:** `apps/api/app/api/v1/copilot.py` (add to same file)

`GET /interviews/{interview_id}/copilot/suggestions`:
- Requires auth, role check (interviewer or admin)
- Load Interview, verify exists
- Load latest Question for this interview (ORDER BY order_index DESC LIMIT 1)
- Load Candidate skills via interview.candidate_id → Candidate.skills
- Call copilot_service.generate_suggestions(interview_id, question.question_text, question.candidate_answer_text or "", question.answer_score or 0, candidate.skills or [], db)
- Return SuggestionsResponse

---

### Task 1.8: Create copilot API — dismiss endpoint

**File:** `apps/api/app/api/v1/copilot.py` (add to same file)

`POST /interviews/{interview_id}/copilot/dismiss/{suggestion_id}`:
- Requires auth, role check
- Load CopilotSession for this interview_id
- Find the suggestion with matching id in suggestions_log list
- Set suggestion["dismissed"] = True
- db.flush
- Return {"status": "dismissed"}

---

### Task 1.9: Register copilot router

**File:** `apps/api/app/api/v1/router.py`

Add: `from app.api.v1.copilot import router as copilot_router`
Add: `api_router.include_router(copilot_router)`

---

### Task 1.10: Create useCopilot hook

**File:** `apps/web/hooks/useCopilot.ts`

Create three hooks:
- `useStartCopilot(interviewId: string)` — useMutation, POST to `/api/v1/interviews/${interviewId}/copilot/start`
- `useCopilotSuggestions(interviewId: string, enabled: boolean)` — useQuery, GET to `/api/v1/interviews/${interviewId}/copilot/suggestions`, refetchInterval: 5000 when enabled, retry: false
- `useDismissSuggestion(interviewId: string)` — useMutation, POST to `/api/v1/interviews/${interviewId}/copilot/dismiss/${suggestionId}`, invalidates suggestions query on success

All use apiFetch from "@/lib/api".

---

### Task 1.11: Create SuggestionCard component

**File:** `apps/web/components/copilot/SuggestionCard.tsx`

Component props: { id, type, icon, color, text, onDismiss: (id: string) => void }

Render:
- A div with border, rounded corners, padding
- Background color: light version of the color prop (use color + "20" for hex opacity, or use CSS color-mix)
- Left side: icon (emoji text, large), type badge (small pill with type name)
- Center: suggestion text
- Right side: dismiss X button
- All in a flex row

---

### Task 1.12: Create CopilotSidebar component

**File:** `apps/web/components/copilot/CopilotSidebar.tsx`

Component props: { suggestions: Suggestion[], onDismiss: (id: string) => void }

Where Suggestion = { id: string, type: string, icon: string, color: string, text: string }

Render:
- Header: "AI Suggestions" with a bot emoji
- Scrollable list of SuggestionCard components
- Filter out suggestions where dismissed === true
- Show "No suggestions yet" empty state when list is empty
- Max height with overflow-y-auto

---

### Task 1.13: Create copilot setup page

**File:** `apps/web/app/(dashboard)/copilot/page.tsx`

Page that lets interviewer select an in_progress interview to start copilot mode.

- Fetch interviews list via useInterviews() hook (already exists)
- Filter to only show in_progress interviews
- Dropdown/select to pick one
- "Start Copilot Session" button
- On click: call useStartCopilot.mutateAsync(selectedId)
- On success: router.push(`/copilot/${selectedId}`)
- Show loading state on button while mutation is pending
- Show "No active interviews" empty state if none in_progress

Add "use client" directive at top.

---

### Task 1.14: Create active copilot page

**File:** `apps/web/app/(dashboard)/copilot/[id]/page.tsx`

Two-column layout for active copilot session.

Left column (wider):
- Fetch interview data via useInterview(id)
- Show current question text and candidate's answer (from latest question)
- Show answer score as a colored number
- Show LiveScoreCard component (reuse from existing components/interview/LiveScoreCard.tsx)

Right column (sidebar):
- CopilotSidebar component
- Fed by useCopilotSuggestions(id, true)
- onDismiss calls useDismissSuggestion(id).mutateAsync(suggestionId)

Top: breadcrumb "Copilot > Interview {id}"
Show loading state while data loads.

Add "use client" directive.

---

### Task 1.15: Add Copilot to Sidebar navigation

**File:** `apps/web/components/shared/Sidebar.tsx`

Add a new nav item:
- Label: "Copilot"
- Icon: use a robot emoji "🤖" or the existing bot icon if available
- Route: /copilot
- Visibility: only when user.role is "interviewer" or "admin" (check authStore or useAuth)

Place it after "Interviews" in the nav list.

---

## ANALYTICS DASHBOARD

### Task 2.1: Create analytics schema

**File:** `apps/api/app/schemas/analytics.py`

Create Pydantic v2 schemas:
- `OverviewResponse`: total_interviews (int), completed_interviews (int), average_score (float), total_candidates (int), interviews_this_week (int), top_skills (list[dict]) — each dict has skill (str) and count (int)
- `CandidateHistoryItem`: interview_id (str), date (str), score (float), status (str), question_count (int)
- `CandidateHistoryResponse`: items (list[CandidateHistoryItem])
- `TrendResponse`: weekly_scores (list[dict]) — each dict has week_start (str), average_score (float), interview_count (int). Also skill_distribution (list[dict]) — each dict has skill (str), count (int)

---

### Task 2.2: Create analytics API — overview endpoint

**File:** `apps/api/app/api/v1/analytics.py`

Create router with the overview endpoint first.

`GET /analytics/overview`:
- Requires auth (admin or interviewer role)
- Query 1: SELECT count(*) FROM interviews → total_interviews
- Query 2: SELECT count(*) FROM interviews WHERE status = 'completed' → completed_interviews
- Query 3: SELECT avg(total_score) FROM interviews WHERE status = 'completed' AND total_score IS NOT NULL → average_score (round to 1 decimal)
- Query 4: SELECT count(*) FROM candidates → total_candidates
- Query 5: SELECT count(*) FROM interviews WHERE created_at >= now() - interval '7 days' → interviews_this_week
- Query 6: SELECT skills FROM candidates WHERE skills IS NOT NULL → flatten all skill lists, count occurrences, sort desc, take top 10
- Return OverviewResponse

Router: `router = APIRouter(prefix="/analytics", tags=["analytics"])`

Imports: uuid, typing Annotated, fastapi APIRouter/Depends/HTTPException, sqlalchemy select/func, sqlalchemy.ext.asyncio AsyncSession, app.core.database get_db, app.api.deps get_current_user, app.models.user User, app.models.interview Interview, app.models.candidate Candidate

---

### Task 2.3: Create analytics API — candidate history endpoint

**File:** `apps/api/app/api/v1/analytics.py` (add to same file)

`GET /analytics/candidates/{candidate_id}/history`:
- Requires auth
- Load candidate by id, verify exists (404 if not)
- Ownership check: user is admin, or user is the candidate (candidate.user_id == user.id), or user is an interviewer
- SELECT from Interview WHERE candidate_id = candidate_id ORDER BY created_at DESC LIMIT 50
- Map each to CandidateHistoryItem: interview_id=str(id), date=created_at.isoformat(), score=total_score or 0, status=status, question_count=question_count
- Return CandidateHistoryResponse

---

### Task 2.4: Create analytics API — trends endpoint

**File:** `apps/api/app/api/v1/analytics.py` (add to same file)

`GET /analytics/trends`:
- Requires auth (admin or interviewer)
- Weekly scores: query interviews created in last 12 weeks, group by week (use date_trunc('week', created_at)), compute avg(total_score) and count per week
- Skill distribution: same as top_skills in overview but top 15 instead of 10
- Return TrendResponse

Note: date_trunc is PostgreSQL-specific. If using SQLite in tests, fall back to strftime. For production PostgreSQL, use date_trunc.

---

### Task 2.5: Register analytics router

**File:** `apps/api/app/api/v1/router.py`

Add: `from app.api.v1.analytics import router as analytics_router`
Add: `api_router.include_router(analytics_router)`

---

### Task 2.6: Create useAnalytics hook

**File:** `apps/web/hooks/useAnalytics.ts`

Create three hooks:
- `useAnalyticsOverview()` — useQuery, GET /api/v1/analytics/overview, staleTime 60 seconds
- `useCandidateHistory(candidateId: string)` — useQuery, GET /api/v1/analytics/candidates/${candidateId}/history, enabled only when candidateId is non-empty
- `useAnalyticsTrends()` — useQuery, GET /api/v1/analytics/trends, staleTime 60 seconds

All use apiFetch.

---

### Task 2.7: Create MetricCard component

**File:** `apps/web/components/analytics/MetricCard.tsx`

Component props: { value: number, label: string, icon: string, decimals?: number }

Render:
- Card component from ui/card
- Large animated number that counts up from 0 to value over 1 second
- Use useEffect + requestAnimationFrame with easing
- Label below the number in muted text
- Icon (emoji) in the top-right corner
- Format number with Intl.NumberFormat

Add "use client" directive.

---

### Task 2.8: Create SkillsBarChart component

**File:** `apps/web/components/analytics/SkillsBarChart.tsx`

Component props: { data: { skill: string, count: number }[] }

Render:
- Horizontal bar chart using recharts BarChart with layout="vertical"
- YAxis: skill names (dataKey="skill"), width 120
- XAxis: count (dataKey="count")
- Single Bar with gradient fill
- ResponsiveContainer width="100%" height={400}
- Show "No data" empty state if data is empty

Add "use client" directive.

---

### Task 2.9: Create analytics page

**File:** `apps/web/app/(dashboard)/analytics/page.tsx`

Page layout:
- Title: "Analytics Dashboard"
- Top row (grid 4 columns): 4 MetricCard components showing total_interviews, completed_interviews, average_score, total_candidates from useAnalyticsOverview
- Middle row: Card with "Score Trends" title, LineChart showing weekly_scores from useAnalyticsTrends (use existing ScoreLineChart or build inline with recharts)
- Bottom row: Card with "Top Skills" title, SkillsBarChart with skill_distribution from useAnalyticsTrends
- Below that: Card with "Candidate History" title, dropdown to select a candidate (fetch candidates list or use a search input), when selected show CandidateHistory table

Add "use client" directive. Show loading skeleton while data loads.

---

### Task 2.10: Add Analytics to Sidebar navigation

**File:** `apps/web/components/shared/Sidebar.tsx`

Add nav item:
- Label: "Analytics"
- Icon: chart emoji "📊"
- Route: /analytics
- Visibility: admin and interviewer roles

Place after Copilot in nav list.

---

## JD MATCHING

### Task 3.1: Create jd_service.py — skill extraction

**File:** `apps/api/app/services/jd_service.py`

Create the file with skill extraction function.

`extract_skills_from_jd(jd_text: str) -> dict`:
- Import ALL_SKILLS from app.core.constants
- Normalize jd_text to lowercase
- For each skill in ALL_SKILLS, check if skill name appears in jd_text (case-insensitive substring match)
- To determine required vs preferred: scan for sections/keywords
  - If "required" or "must have" or "essential" appears within 200 chars before the skill mention → required
  - If "preferred" or "nice to have" or "bonus" or "plus" appears within 200 chars before → preferred
  - Default to required if no qualifier found
- Return {"required_skills": [...], "preferred_skills": [...]}

Imports: re, app.core.constants.ALL_SKILLS

---

### Task 3.2: Create jd_service.py — match calculation

**File:** `apps/api/app/services/jd_service.py` (add function)

`calculate_match(candidate_skills: list[str], jd_skills: dict) -> dict`:
- Normalize candidate_skills to lowercase
- matched_required = [s for s in jd_skills["required_skills"] if s in candidate_skills]
- missing_required = [s for s in jd_skills["required_skills"] if s not in candidate_skills]
- matched_preferred = [s for s in jd_skills["preferred_skills"] if s in candidate_skills]
- missing_preferred = [s for s in jd_skills["preferred_skills"] if s not in candidate_skills]
- total_required = len(jd_skills["required_skills"])
- match_percentage = (len(matched_required) / total_required * 100) if total_required > 0 else 100.0
- Return all lists + match_percentage rounded to 1 decimal

No new imports needed.

---

### Task 3.3: Create jd_service.py — question generation

**File:** `apps/api/app/services/jd_service.py` (add function)

`generate_jd_questions(missing_skills: list[str], count: int = 5) -> list[dict]`:
- Import TECHNICAL_QUESTION_TEMPLATES from constants
- Pick templates from the "medium" difficulty level
- For each missing skill (up to count), pick a template, fill {skill} with the skill name
- Return list of {"question_text": rendered, "question_type": "technical", "difficulty": "medium", "target_skill": skill}
- If missing_skills is empty, return empty list

Imports: random, app.core.constants.TECHNICAL_QUESTION_TEMPLATES

---

### Task 3.4: Create jd schema

**File:** `apps/api/app/schemas/jd.py`

Create Pydantic v2 schemas:
- `JDUploadRequest`: jd_text (str, min_length=50)
- `JDMatchResponse`: match_percentage (float), matched_required (list[str]), missing_required (list[str]), matched_preferred (list[str]), missing_preferred (list[str])
- `JDQuestionRequest`: jd_text (str, min_length=50), count (int, default=5, ge=1, le=20)
- `JDQuestionItem`: question_text (str), question_type (str), difficulty (str), target_skill (str)
- `JDQuestionResponse`: questions (list[JDQuestionItem])

---

### Task 3.5: Create jd API — match endpoint

**File:** `apps/api/app/api/v1/jd.py`

Create router with match endpoint.

`POST /candidates/{candidate_id}/jd`:
- Requires auth
- Load Candidate by candidate_id, verify exists (404)
- Ownership check: user is admin, or user is the candidate (candidate.user_id == user.id), or user is interviewer
- Parse body as JDUploadRequest
- Call jd_service.extract_skills_from_jd(request.jd_text)
- Call jd_service.calculate_match(candidate.skills or [], extracted_skills)
- Return JDMatchResponse

Router: `router = APIRouter(prefix="/candidates/{candidate_id}/jd", tags=["jd-matching"])`

---

### Task 3.6: Create jd API — questions endpoint

**File:** `apps/api/app/api/v1/jd.py` (add to same file)

`POST /candidates/{candidate_id}/jd/questions`:
- Requires auth
- Same ownership check as match endpoint
- Parse body as JDQuestionRequest
- Call jd_service.extract_skills_from_jd(request.jd_text)
- Call jd_service.calculate_match(candidate.skills or [], extracted_skills)
- Call jd_service.generate_jd_questions(match_result["missing_required"], request.count)
- Return JDQuestionResponse

---

### Task 3.7: Register jd router

**File:** `apps/api/app/api/v1/router.py`

Add: `from app.api.v1.jd import router as jd_router`
Add: `api_router.include_router(jd_router)`

---

### Task 3.8: Create useJD hook

**File:** `apps/web/hooks/useJD.ts`

Create two hooks:
- `useJdMatch(candidateId: string)` — useMutation, POST /api/v1/candidates/${candidateId}/jd
- `useJdQuestions(candidateId: string)` — useMutation, POST /api/v1/candidates/${candidateId}/jd/questions

Both use apiFetch. On success, no query invalidation needed (stateless analysis).

---

### Task 3.9: Create MatchResults component

**File:** `apps/web/components/jd/MatchResults.tsx`

Component props: { matchPercentage, matchedRequired, missingRequired, matchedPreferred, missingPreferred }

Render:
- Large circular progress indicator showing matchPercentage (reuse ScoreOverview SVG pattern)
- Color: green if >= 80, yellow if >= 60, red if < 60
- Below: 2x2 grid of chip lists:
  - "Required Skills Met" — green chips for each matchedRequired
  - "Required Skills Missing" — red chips for each missingRequired
  - "Preferred Skills Met" — green chips for each matchedPreferred
  - "Preferred Skills Missing" — orange chips for each missingPreferred
- Each chip is a small rounded pill with the skill name

Add "use client" directive.

---

### Task 3.10: Create GeneratedQuestions component

**File:** `apps/web/components/jd/GeneratedQuestions.tsx`

Component props: { questions: { question_text, question_type, difficulty, target_skill }[] }

Render:
- List of cards, each card has:
  - Header row: question_type badge, difficulty badge, target_skill chip
  - Body: question_text
- "No questions generated" empty state
- Each card has a "Copy" button that copies question_text to clipboard

Add "use client" directive.

---

### Task 3.11: Create JD match page

**File:** `apps/web/app/(dashboard)/tools/jd/page.tsx`

Page layout:
- Title: "Job Description Match"
- Textarea for pasting JD text (min 50 chars, show char count)
- Row of two buttons: "Analyze Match" and "Generate Questions"
- Analyze Match calls useJdMatch, shows MatchResults below
- Generate Questions calls useJdQuestions, shows GeneratedQuestions below
- Show loading spinners on buttons while mutations are pending
- Show error toast if mutation fails

For candidate_id: use a text input where user can paste a candidate ID, OR if the user is a candidate, use their own candidate record. For simplicity, start with a candidate ID input field.

Add "use client" directive.

---

### Task 3.12: Add JD Match to Sidebar navigation

**File:** `apps/web/components/shared/Sidebar.tsx`

Add a "Tools" section header in the sidebar (below the main nav).
Add nav item under Tools:
- Label: "JD Match"
- Icon: magnifying glass emoji "🔍"
- Route: /tools/jd
- Visibility: admin and interviewer roles

---

## ASYNC INTERVIEW MODE

### Task 4.1: Add share_token to Interview model

**File:** `apps/api/app/models/interview.py`

Add field to Interview class:
- `share_token: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)`

Import String from sqlalchemy if not already imported.

---

### Task 4.2: Create async interview schema

**File:** `apps/api/app/schemas/interview.py` (add to existing file)

Add new schemas:
- `ShareResponse`: share_token (str), share_url (str)
- `JoinInterviewResponse`: id (str), candidate_name (str), question_count (int), difficulty_level (str), status (str)
- `JoinAnswerRequest`: question_id (str), answer_text (str)
- `JoinAnswerResponse`: next_question (dict or None), score (float or None), completed (bool)

---

### Task 4.3: Create interview_service.py — share token functions

**File:** `apps/api/app/services/interview_service.py` (add to existing file)

Add two functions:

`generate_share_token(interview_id: uuid.UUID, db: AsyncSession) -> str`:
- Import secrets
- Load Interview by id
- Generate token: secrets.token_urlsafe(32)
- Set interview.share_token = token
- db.flush
- Return token

`get_interview_by_token(token: str, db: AsyncSession) -> Interview | None`:
- SELECT from Interview WHERE share_token = token
- Return interview or None

Imports: secrets, uuid, sqlalchemy select, app.models.interview.Interview

---

### Task 4.4: Create async interview API — share endpoint

**File:** `apps/api/app/api/v1/interviews.py` (add to existing file)

`POST /interviews/{interview_id}/share`:
- Requires auth, role check (interviewer or admin)
- Load Interview by id, verify exists (404)
- If interview.share_token already exists, return existing token (don't regenerate)
- Call interview_service.generate_share_token(interview_id, db)
- Construct share_url = f"{settings.APP_URL}/interview/join/{token}" (need APP_URL in config, or use a hardcoded dev URL for now)
- Return ShareResponse

Note: Need to add APP_URL to config.py settings. Default to "http://localhost:3000" for dev.

---

### Task 4.5: Create async interview API — join endpoint

**File:** `apps/api/app/api/v1/interviews.py` (add to same file)

`GET /interviews/join/{token}`:
- NO AUTH (public endpoint)
- Call interview_service.get_interview_by_token(token, db)
- If not found: 404
- If interview.status not in ("ready", "in_progress"): 400 with message "Interview is not available"
- Load candidate name via interview.candidate_id → Candidate.name
- Count questions: SELECT count(*) FROM questions WHERE interview_id = interview.id
- Return JoinInterviewResponse

---

### Task 4.6: Create async interview API — answer endpoint

**File:** `apps/api/app/api/v1/interviews.py` (add to same file)

`POST /interviews/join/{token}/answer`:
- NO AUTH (public endpoint)
- Call interview_service.get_interview_by_token(token, db)
- If not found: 404
- Parse body as JoinAnswerRequest
- Load Question by question_id, verify it belongs to this interview (403 if not)
- If question.candidate_answer_text is already set: 400 "Already answered"
- Set question.candidate_answer_text = request.answer_text
- Evaluate answer: call existing answer_evaluator or set a placeholder score
- Set question.answer_score = evaluated score
- Check if there are more unanswered questions: SELECT from Question WHERE interview_id = interview.id AND candidate_answer_text IS NULL ORDER BY order_index LIMIT 1
- If next question exists: return JoinAnswerResponse(next_question={id, question_text, question_type, difficulty, order_index}, score=score, completed=False)
- If no more questions: return JoinAnswerResponse(next_question=None, score=score, completed=True)

For answer evaluation, import and call the existing answer evaluator from app.ml.evaluation.answer_evaluator if available, else use a simple keyword-match placeholder.

---

### Task 4.7: Generate alembic migration for share_token

**Steps:**
1. Run: `cd apps/api && alembic revision --autogenerate -m "add_share_token_to_interviews"`
2. Review the generated migration file — it should only add a share_token VARCHAR(64) column to interviews table
3. Verify the migration has upgrade() and downgrade() functions
4. Apply: `alembic upgrade head`
5. Verify: `python -c "from app.models.interview import Interview; print(hasattr(Interview, 'share_token'))"`

---

### Task 4.8: Create join page layout

**File:** `apps/web/app/interview/join/[token]/layout.tsx`

Minimal layout for public interview pages:
- No sidebar, no TopBar
- Just a centered container with max-width
- Header with app logo/name at top
- Wrap children in QueryClientProvider and ThemeProvider (import from components/providers)
- Background: neutral color

This layout does NOT use the (dashboard) route group layout. It's a standalone layout.

---

### Task 4.9: Create join page

**File:** `apps/web/app/interview/join/[token]/page.tsx`

Public interview page (no auth required):

States:
1. Loading: show spinner while fetching interview info
2. Welcome: show candidate name, question count, difficulty, "Begin Interview" button
3. Active: show one question at a time with textarea for answer, "Submit Answer" button
4. Complete: show thank you message

On mount: fetch GET /api/v1/interviews/join/{token} (use raw fetch, not apiFetch, since no auth needed)

On "Begin Interview": set state to active, show first question

On "Submit Answer": POST /api/v1/interviews/join/{token}/answer with {question_id, answer_text}
- If response has next_question: show next question
- If response has completed=true: show complete state
- Show score feedback after each answer (small toast or inline)

Add "use client" directive. This page must NOT use any auth-dependent hooks.

---

### Task 4.10: Update new interview page with share link option

**File:** `apps/web/app/(dashboard)/interviews/new/page.tsx`

After interview creation, add:
- A checkbox "Generate shareable link for candidate"
- If checked, after interview is created, call POST /api/v1/interviews/{id}/share
- Show the share URL in a copyable input field with a "Copy" button
- Show a note: "Share this link with the candidate. They can answer questions without logging in."

---

## ADMIN PANEL

### Task 5.1: Create admin schema

**File:** `apps/api/app/schemas/admin.py`

Create Pydantic v2 schemas:
- `UserListItem`: id (str), email (str), full_name (str), role (str), is_active (bool), created_at (str)
- `UserListResponse`: items (list[UserListItem]), total (int), page (int), per_page (int)
- `UserUpdateRequest`: role (str or None, optional), is_active (bool or None, optional)
- `SystemHealthResponse`: status (str), database (str), timestamp (str)
- `SystemStatsResponse`: total_users (int), total_interviews (int), total_candidates (int), active_sessions (int)

---

### Task 5.2: Create admin API — list users endpoint

**File:** `apps/api/app/api/v1/admin.py`

Create router with list users endpoint.

`GET /admin/users`:
- Requires auth + admin role (check user.role == "admin", else 403)
- Query params: role (optional filter), is_active (optional filter), page (default 1), per_page (default 20)
- Build query: SELECT from User
  - If role filter: WHERE user.role = role
  - If is_active filter: WHERE user.is_active = is_active
  - ORDER BY created_at DESC
  - LIMIT per_page OFFSET (page-1)*per_page
- Also get total count with same filters
- Return UserListResponse

Router: `router = APIRouter(prefix="/admin", tags=["admin"])`

---

### Task 5.3: Create admin API — update user endpoint

**File:** `apps/api/app/api/v1/admin.py` (add to same file)

`PATCH /admin/users/{user_id}`:
- Requires auth + admin role
- Load User by user_id, verify exists (404)
- If user_id == current user's id and request tries to change is_active to false: 400 "Cannot deactivate yourself"
- If request.role is provided: validate it's one of "admin", "interviewer", "candidate"
- Update user fields that are provided
- db.flush
- Return updated user as UserListItem

---

### Task 5.4: Create admin API — health endpoint

**File:** `apps/api/app/api/v1/admin.py` (add to same file)

`GET /admin/system/health`:
- Requires auth + admin role
- Try: execute "SELECT 1" via db.execute(text("SELECT 1"))
- If success: database = "connected"
- If fail: database = "error"
- Return SystemHealthResponse with status="healthy" if DB ok, timestamp=now().isoformat()

---

### Task 5.5: Create admin API — stats endpoint

**File:** `apps/api/app/api/v1/admin.py` (add to same file)

`GET /admin/system/stats`:
- Requires auth + admin role
- Query 1: count(*) from users → total_users
- Query 2: count(*) from interviews → total_interviews
- Query 3: count(*) from candidates → total_candidates
- Query 4: count(*) from interviews WHERE status = 'in_progress' → active_sessions
- Return SystemStatsResponse

---

### Task 5.6: Register admin router

**File:** `apps/api/app/api/v1/router.py`

Add: `from app.api.v1.admin import router as admin_router`
Add: `api_router.include_router(admin_router)`

---

### Task 5.7: Create useAdmin hook

**File:** `apps/web/hooks/useAdmin.ts`

Create four hooks:
- `useAdminUsers(filters: {role?: string, page?: number})` — useQuery, GET /api/v1/admin/users with query params, keepPreviousData true
- `useUpdateUser()` — useMutation, PATCH /api/v1/admin/users/${userId}, invalidates admin-users query on success
- `useSystemHealth()` — useQuery, GET /api/v1/admin/system/health, refetchInterval 30000
- `useSystemStats()` — useQuery, GET /api/v1/admin/system/stats, staleTime 30000

All use apiFetch.

---

### Task 5.8: Create UserTable component

**File:** `apps/web/components/admin/UserTable.tsx`

Component props: { users: UserListItem[], onUpdateRole: (userId: string, role: string) => void, onToggleActive: (userId: string, isActive: boolean) => void }

Render:
- Table with columns: Name, Email, Role, Status, Actions
- Role column: select dropdown with options admin/interviewer/candidate, onChange calls onUpdateRole
- Status column: toggle switch (green if active, red if inactive), onChange calls onToggleActive
- Actions column: currently empty (future: delete, impersonate)
- Row highlight on hover
- Show "No users found" if empty

Add "use client" directive.

---

### Task 5.9: Create admin users page

**File:** `apps/web/app/(dashboard)/admin/users/page.tsx`

Page layout:
- Title: "User Management"
- Role filter tabs: All, Admin, Interviewer, Candidate (click to filter)
- UserTable component fed by useAdminUsers
- Pagination: Previous / Page X / Next buttons
- Show loading skeleton while data loads
- Inline confirmation: before deactivating, show a confirm dialog (use window.confirm for simplicity)

Handle role update: call useUpdateUser.mutateAsync({userId, role})
Handle active toggle: call useUpdateUser.mutateAsync({userId, is_active})

Add "use client" directive.

---

### Task 5.10: Create admin system page

**File:** `apps/web/app/(dashboard)/admin/system/page.tsx`

Page layout:
- Title: "System Health"
- Health card: green/red circle indicator, "Database: connected/error", "Last checked: timestamp"
- Stats grid (4 cards): total users, total interviews, total candidates, active sessions
- Auto-refreshes every 30 seconds (via useSystemHealth and useSystemStats refetchInterval)
- Show loading while data loads

Add "use client" directive.

---

### Task 5.11: Add Admin section to Sidebar

**File:** `apps/web/components/shared/Sidebar.tsx`

Add an "Admin" section header at the bottom of the sidebar (only visible when user.role === "admin").
Add two nav items under Admin:
- Label: "Users", Icon: people emoji "👥", Route: /admin/users
- Label: "System", Icon: gear emoji "⚙️", Route: /admin/system

---

## VERIFICATION

### Task 6.1: Backend import check

**Steps:**
1. Run: `cd apps/api && python -c "from app.services.copilot_service import generate_suggestions; print('copilot_service OK')"`
2. Run: `cd apps/api && python -c "from app.services.jd_service import extract_skills_from_jd; print('jd_service OK')"`
3. Run: `cd apps/api && python -c "from app.api.v1.router import api_router; print('router OK')"`
4. Verify no import errors on any of these

---

### Task 6.2: Frontend build check

**Steps:**
1. Run: `cd apps/web && npx next build`
2. Verify "Compiled successfully" in output
3. Verify all new routes appear: /copilot, /copilot/[id], /analytics, /tools/jd, /admin/users, /admin/system, /interview/join/[token]
4. Verify no TypeScript errors
5. Verify /interview/join/[token] is NOT prefixed with /dashboard

---

### Task 6.3: Database migration check

**Steps:**
1. Run: `cd apps/api && python -c "from app.models.interview import Interview; print(hasattr(Interview, 'share_token'))"`
2. Verify prints "True"
3. Run: `cd apps/api && alembic history` — verify the migration appears
4. Run: `cd apps/api && alembic current` — verify head is applied

---

### Task 6.4: Copilot end-to-end verification

**Steps:**
1. Start backend server
2. Login as interviewer
3. Create an interview with status "in_progress"
4. POST /api/v1/interviews/{id}/copilot/start — verify 200 with session data
5. POST a question answer to populate data
6. GET /api/v1/interviews/{id}/copilot/suggestions — verify returns list of suggestions with correct keys (id, type, icon, color, text, created_at)
7. POST /api/v1/interviews/{id}/copilot/dismiss/{suggestion_id} — verify 200

---

### Task 6.5: Analytics end-to-end verification

**Steps:**
1. Ensure at least one completed interview exists in DB
2. GET /api/v1/analytics/overview — verify returns all fields with correct types
3. GET /api/v1/analytics/candidates/{id}/history — verify returns list of history items
4. GET /api/v1/analytics/trends — verify returns weekly_scores and skill_distribution lists

---

### Task 6.6: JD matching end-to-end verification

**Steps:**
1. Ensure at least one candidate with skills exists
2. POST /api/v1/candidates/{id}/jd with a sample JD text (at least 50 chars) — verify returns match_percentage and skill lists
3. POST /api/v1/candidates/{id}/jd/questions — verify returns list of question dicts

---

### Task 6.7: Async interview end-to-end verification

**Steps:**
1. Create an interview with status "ready"
2. POST /api/v1/interviews/{id}/share — verify returns share_token and share_url
3. GET /api/v1/interviews/join/{token} (no auth) — verify returns interview details
4. GET /api/v1/interviews/join/invalid_token — verify 404
5. POST /api/v1/interviews/join/{token}/answer with a question_id and answer_text — verify returns next_question or completed

---

### Task 6.8: Admin end-to-end verification

**Steps:**
1. Login as admin
2. GET /api/v1/admin/users — verify returns user list with pagination
3. PATCH /api/v1/admin/users/{id} with role="candidate" — verify role changed
4. PATCH /api/v1/admin/users/{self_id} with is_active=false — verify 400 error
5. GET /api/v1/admin/system/health — verify returns status and database fields
6. GET /api/v1/admin/system/stats — verify returns all count fields
7. Login as non-admin, try GET /api/v1/admin/users — verify 403

---

## FILE SUMMARY

| Task | New Files | Modified Files |
|------|-----------|----------------|
| 1.1-1.4 Copilot service | 1 | 0 |
| 1.5 Copilot schema | 1 | 0 |
| 1.6-1.8 Copilot API | 1 | 0 |
| 1.9 Register router | 0 | 1 |
| 1.10 Copilot hook | 1 | 0 |
| 1.11-1.12 Copilot components | 2 | 0 |
| 1.13-1.14 Copilot pages | 2 | 0 |
| 1.15 Copilot sidebar | 0 | 1 |
| 2.1 Analytics schema | 1 | 0 |
| 2.2-2.4 Analytics API | 1 | 0 |
| 2.5 Register router | 0 | 1 |
| 2.6 Analytics hook | 1 | 0 |
| 2.7-2.8 Analytics components | 2 | 0 |
| 2.9 Analytics page | 1 | 0 |
| 2.10 Analytics sidebar | 0 | 1 |
| 3.1-3.3 JD service | 1 | 0 |
| 3.4 JD schema | 1 | 0 |
| 3.5-3.6 JD API | 1 | 0 |
| 3.7 Register router | 0 | 1 |
| 3.8 JD hook | 1 | 0 |
| 3.9-3.10 JD components | 2 | 0 |
| 3.11 JD page | 1 | 0 |
| 3.12 JD sidebar | 0 | 1 |
| 4.1 Interview model | 0 | 1 |
| 4.2 Interview schema | 0 | 1 |
| 4.3 Interview service | 0 | 1 |
| 4.4-4.6 Interview API | 0 | 1 |
| 4.7 Migration | 1 | 0 |
| 4.8-4.9 Join pages | 2 | 0 |
| 4.10 New interview update | 0 | 1 |
| 5.1 Admin schema | 1 | 0 |
| 5.2-5.5 Admin API | 1 | 0 |
| 5.6 Register router | 0 | 1 |
| 5.7 Admin hook | 1 | 0 |
| 5.8 Admin components | 1 | 0 |
| 5.9-5.10 Admin pages | 2 | 0 |
| 5.11 Admin sidebar | 0 | 1 |
| **Total** | **~28 new** | **~11 modified** |
