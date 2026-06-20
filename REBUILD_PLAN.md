# AI Interview Agent — Professional Rebuild Plan

## 1. Current State Assessment

### 1.1 Architecture Summary
The existing project is a monolithic Python application with:
- **Frontend**: Streamlit (server-rendered Python widgets, no real SPA capability)
- **Backend**: In-process Python modules (no API layer — everything runs inside Streamlit's event loop)
- **Database**: MongoDB via pymongo (direct driver calls, no ORM, no migrations)
- **ML/NLP**: sentence-transformers, spaCy, OpenAI Whisper, librosa, DeepFace
- **Report Generation**: FPDF2 (PDF), Plotly (charts saved as HTML/JSON)
- **Deployment**: Docker + docker-compose (single container with MongoDB sidecar)

### 1.2 Current Feature Set
- Resume PDF parsing with section segmentation and skill extraction (spaCy NER + taxonomy matching)
- Adaptive question generation (template-based fallback + OpenAI API)
- Adaptive difficulty management (rolling average of last 3 scores)
- Speech-to-text via Whisper, text-to-speech via gTTS/pyttsx3
- Facial emotion detection (DeepFace — currently commented out in requirements)
- Voice emotion analysis (librosa pitch/speed/pause features)
- Multimodal confidence scoring (4-signal weighted fusion)
- Answer evaluation (semantic similarity via sentence-transformers + keyword + concept coverage)
- Follow-up question generation (LLM or template-based)
- 7 Plotly chart types for performance visualization
- PDF report generation with FPDF2
- Interview replay with emotion timeline
- Copilot mode (real-time AI suggestions for human interviewer)
- Coaching plan generator (personalized improvement roadmap with resources)
- RAG chain for job-description-matched questions (ChromaDB + OpenAI)
- Interview pacing system (sentiment-driven flow adjustments)
- D-ID avatar integration (talking-head video generation)
- NetworkX skill graph with community detection

### 1.3 Critical Problems

**Architecture**
- No API layer — frontend and backend are tightly coupled inside Streamlit's execution model
- No real-time communication — Streamlit reruns the entire script on every interaction; no WebSocket/SSE support
- Session state is in-memory Python dicts — lost on restart, not shareable across processes
- No authentication or authorization system
- No async support — all ML inference blocks the UI thread
- No proper error handling boundaries — a crash in any module kills the whole page

**Database**
- MongoDB with raw pymongo — no schema validation, no migrations, no connection pooling beyond basic config
- Data models are Python dataclasses with manual to_dict/from_dict — no serialization layer
- No indexes defined — queries will degrade at scale

**Frontend**
- Streamlit limits UI to basic form widgets — cannot build custom layouts, animations, or interactive components
- No responsive design — Streamlit's layout is fixed-width columns
- No component reusability — each page re-implements similar patterns
- Camera integration is limited to st.camera_input (single snapshot, not live video)
- No proper loading states, skeleton screens, or optimistic updates

**ML Pipeline**
- DeepFace is commented out in requirements.txt — facial emotion detection is broken
- Whisper runs synchronously on the main thread — blocks UI for 10-30 seconds per audio clip
- No model caching strategy beyond simple global variables
- No fallback when ML models fail to load

**Testing**
- Only 5 test files, all unittest-based — no integration tests, no API tests, no frontend tests
- No CI pipeline beyond a basic GitHub Actions workflow
- No test fixtures or mocking infrastructure

**Deployment**
- Single-container Docker setup — no separation of concerns
- No environment management (dev/staging/production)
- No health checks beyond Streamlit's built-in endpoint
- No logging aggregation or monitoring

---

## 2. Target Architecture

### 2.1 High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  Next.js 15 (App Router) + React 19 + TypeScript + Tailwind │
│  + shadcn/ui + Framer Motion + TanStack Query               │
│  Port 3000                                                  │
├─────────────────────────────────────────────────────────────┤
│                      API GATEWAY                             │
│  FastAPI (async) + Pydantic v2 + WebSocket support          │
│  Port 8000                                                  │
├──────────┬──────────┬───────────┬───────────┬───────────────┤
│ Auth     │Interview │ ML        │ Report    │ Analytics     │
│ Service  │ Service  │ Service   │ Service   │ Service       │
│ (JWT)    │(orchest.)│(inference)│(generate) │(metrics)      │
├──────────┴──────────┴───────────┴───────────┴───────────────┤
│                     DATA LAYER                               │
│  PostgreSQL 16 (primary) + Redis 7 (cache/sessions/queues)  │
│  + MinIO/S3 (file storage: resumes, audio, reports)         │
├─────────────────────────────────────────────────────────────┤
│                   ML INFRASTRUCTURE                          │
│  Whisper (faster-whisper) + sentence-transformers            │
│  spaCy + librosa + OpenCV + optional DeepFace               │
│  Celery + Redis (async task queue for heavy inference)      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 New Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend Framework** | Next.js 15 (App Router) | SSR/SSG, server components, API routes, file-based routing |
| **UI Library** | React 19 | Concurrent features, use() hook, server components |
| **Styling** | Tailwind CSS v4 + shadcn/ui | Utility-first, accessible components, dark mode built-in |
| **Animations** | Framer Motion | Smooth page transitions, micro-interactions |
| **State/Data** | TanStack Query v5 | Server state caching, optimistic updates, real-time sync |
| **Forms** | React Hook Form + Zod | Type-safe validation, minimal re-renders |
| **Charts** | Recharts (shadcn integration) | Lightweight, composable, responsive |
| **Video/WebRTC** | LiveKit or Daily.js | Real-time video/audio with recording |
| **Backend Framework** | FastAPI (async) | Auto OpenAPI docs, WebSocket, dependency injection |
| **ORM** | SQLAlchemy 2.0 (async) + Alembic | Async support, migrations, relationship mapping |
| **Validation** | Pydantic v2 | Fast serialization, strict typing |
| **Primary DB** | PostgreSQL 16 | ACID, JSON support, full-text search, pgvector for embeddings |
| **Cache/Queue** | Redis 7 | Session cache, Celery broker, rate limiting |
| **Task Queue** | Celery 5 + Redis broker | Async ML inference, report generation |
| **File Storage** | MinIO (S3-compatible) | Resume uploads, audio recordings, PDF reports |
| **Auth** | JWT + bcrypt + refresh tokens | Stateless auth, role-based access (admin/interviewer/candidate) |
| **Speech-to-Text** | faster-whisper | 4x faster than openai-whisper, same accuracy |
| **Embeddings** | sentence-transformers + pgvector | Semantic search stored in PostgreSQL |
| **Container** | Docker Compose (multi-service) | Separate containers for API, frontend, worker, DB, Redis |

### 2.3 Project Structure (New)

```
ai-interview-agent/
├── apps/
│   ├── web/                          # Next.js frontend
│   │   ├── app/
│   │   │   ├── (auth)/               # Auth pages (login/register)
│   │   │   ├── (dashboard)/          # Dashboard pages
│   │   │   │   ├── interview/        # Interview flow pages
│   │   │   │   ├── results/          # Results & analytics
│   │   │   │   ├── coaching/         # Coaching plans
│   │   │   │   ├── copilot/          # Copilot mode
│   │   │   │   ├── admin/            # Admin panel
│   │   │   │   └── layout.tsx        # Dashboard layout with sidebar
│   │   │   ├── api/                  # Next.js API routes (BFF proxy)
│   │   │   ├── layout.tsx            # Root layout
│   │   │   └── page.tsx              # Landing page
│   │   ├── components/
│   │   │   ├── ui/                   # shadcn/ui components
│   │   │   ├── interview/            # Interview-specific components
│   │   │   ├── charts/               # Chart components
│   │   │   └── shared/               # Shared components
│   │   ├── hooks/                    # Custom React hooks
│   │   ├── lib/                      # Utilities, API client
│   │   ├── stores/                   # Zustand stores (client state)
│   │   └── styles/                   # Global styles
│   │
│   └── api/                          # FastAPI backend
│       ├── app/
│       │   ├── api/
│       │   │   ├── v1/
│       │   │   │   ├── auth.py       # Auth endpoints
│       │   │   │   ├── interviews.py # Interview CRUD + flow
│       │   │   │   ├── candidates.py # Candidate management
│       │   │   │   ├── questions.py  # Question generation
│       │   │   │   ├── reports.py    # Report generation/download
│       │   │   │   ├── coaching.py   # Coaching plans
│       │   │   │   ├── analytics.py  # Analytics endpoints
│       │   │   │   └── ws.py         # WebSocket endpoints
│       │   │   └── deps.py           # Shared dependencies
│       │   ├── core/
│       │   │   ├── config.py         # Pydantic settings
│       │   │   ├── security.py       # JWT, password hashing
│       │   │   └── database.py       # Async SQLAlchemy engine
│       │   ├── models/               # SQLAlchemy ORM models
│       │   ├── schemas/              # Pydantic request/response schemas
│       │   ├── services/             # Business logic layer
│       │   │   ├── interview_service.py
│       │   │   ├── evaluation_service.py
│       │   │   ├── ml_service.py     # ML inference orchestrator
│       │   │   ├── report_service.py
│       │   │   └── coaching_service.py
│       │   ├── ml/                   # ML modules (migrated from current modules/)
│       │   │   ├── resume/
│       │   │   ├── questions/
│       │   │   ├── evaluation/
│       │   │   ├── voice/
│       │   │   ├── video/
│       │   │   └── embeddings/
│       │   ├── tasks/                # Celery tasks
│       │   │   ├── transcription.py
│       │   │   ├── emotion_analysis.py
│       │   │   └── report_generation.py
│       │   └── main.py               # FastAPI app factory
│       ├── alembic/                  # Database migrations
│       ├── tests/
│       └── pyproject.toml
│
├── packages/
│   └── shared/                       # Shared types/schemas (optional Python package)
│
├── infra/
│   ├── docker/
│   │   ├── Dockerfile.web
│   │   ├── Dockerfile.api
│   │   └── Dockerfile.worker
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   └── nginx.conf
│
├── scripts/
│   ├── seed.py                       # Database seeding
│   └── download_models.py            # Pre-download ML models
│
├── .env.example
├── .gitignore
├── Makefile
└── README.md
```

---

## 3. Database Schema (PostgreSQL)

### 3.1 Core Tables

**users** — Authentication and role management
- id (UUID, PK)
- email (unique, indexed)
- password_hash
- full_name
- role (enum: admin, interviewer, candidate)
- avatar_url
- is_active (boolean)
- created_at, updated_at

**candidates** — Candidate profiles (linked to user account or standalone)
- id (UUID, PK)
- user_id (UUID, FK → users, nullable — for walk-in candidates)
- name, email
- resume_s3_key (file stored in MinIO/S3)
- extracted_skills (JSONB array)
- extracted_projects (JSONB array)
- skill_graph (JSONB — NetworkX graph data)
- metadata (JSONB — extensible field)
- created_at, updated_at

**interviews** — Interview sessions
- id (UUID, PK)
- candidate_id (UUID, FK → candidates)
- interviewer_id (UUID, FK → users, nullable — for copilot mode)
- status (enum: draft, ready, in_progress, paused, completed, cancelled)
- difficulty_level (integer 1-4)
- question_count (integer)
- questions_answered (integer, default 0)
- total_score (float, default 0)
- start_time, end_time
- config (JSONB — interview-specific settings)
- created_at, updated_at

**questions** — Individual interview questions
- id (UUID, PK)
- interview_id (UUID, FK → interviews, indexed)
- question_text (text)
- question_type (enum: resume, technical, behavioral, coding)
- difficulty (enum: easy, medium, hard, expert)
- order_index (integer)
- candidate_answer_text (text)
- answer_audio_s3_key (string)
- answer_score (float)
- semantic_score, keyword_score, concept_score (float)
- follow_up_of (UUID, FK → questions.id, nullable — for follow-up chain)
- metadata (JSONB)
- created_at

**emotion_snapshots** — Time-series emotion data
- id (UUID, PK)
- interview_id (UUID, FK → interviews, indexed)
- question_id (UUID, FK → questions, nullable)
- timestamp (timestamptz)
- facial_emotion (string)
- facial_confidence (float)
- voice_emotion (string)
- voice_pitch, speaking_speed (float)
- hesitation_detected (boolean)
- combined_confidence (float)
- raw_data (JSONB)

**reports** — Generated interview reports
- id (UUID, PK)
- interview_id (UUID, FK → interviews, unique)
- pdf_s3_key (string)
- strengths, weaknesses, suggestions (JSONB arrays)
- overall_assessment (text)
- chart_data (JSONB — cached chart configurations)
- generated_at

**coaching_plans** — Personalized improvement plans
- id (UUID, PK)
- interview_id (UUID, FK → interviews)
- candidate_id (UUID, FK → candidates)
- overall_score (float)
- strong_topics, weak_topics (JSONB)
- one_week_plan, one_month_plan, three_month_plan (text)
- coaching_advice (text)
- resources (JSONB)
- generated_at

**copilot_sessions** — Copilot mode sessions
- id (UUID, PK)
- interview_id (UUID, FK → interviews)
- interviewer_id (UUID, FK → users)
- suggestions_log (JSONB — array of suggestion events)
- analytics (JSONB)
- created_at

### 3.2 Indexes
- users: email (unique), role
- interviews: candidate_id, status, created_at
- questions: interview_id + order_index (composite)
- emotion_snapshots: interview_id + timestamp (composite)
- reports: interview_id (unique)

### 3.3 Key Changes from Current
- MongoDB → PostgreSQL (ACID, relational integrity, JSONB for flexible fields)
- UUID primary keys instead of ObjectId
- Proper foreign key relationships with cascade rules
- JSONB for flexible/nested data (skills, graphs, metadata)
- Alembic for version-controlled schema migrations

---

## 4. API Design (FastAPI)

### 4.1 Auth Endpoints
- POST /api/v1/auth/register — Create account
- POST /api/v1/auth/login — Login, returns JWT access + refresh tokens
- POST /api/v1/auth/refresh — Refresh access token
- GET /api/v1/auth/me — Get current user profile
- PUT /api/v1/auth/me — Update profile

### 4.2 Interview Endpoints
- POST /api/v1/interviews — Create new interview session
- GET /api/v1/interviews — List interviews (with filters: status, candidate, date range)
- GET /api/v1/interviews/{id} — Get interview detail
- PATCH /api/v1/interviews/{id} — Update interview (settings, status)
- POST /api/v1/interviews/{id}/start — Start interview flow
- POST /api/v1/interviews/{id}/pause — Pause interview
- POST /api/v1/interviews/{id}/resume — Resume interview
- POST /api/v1/interviews/{id}/close — Close interview, trigger report generation
- DELETE /api/v1/interviews/{id} — Soft-delete interview

### 4.3 Question Endpoints
- GET /api/v1/interviews/{id}/questions — Get all questions for interview
- POST /api/v1/interviews/{id}/questions/generate — Generate questions (async via Celery)
- POST /api/v1/questions/{id}/answer — Submit answer (text or audio upload)
- POST /api/v1/questions/{id}/followup — Request/generate follow-up
- GET /api/v1/questions/{id}/evaluation — Get evaluation for answered question

### 4.4 Candidate Endpoints
- POST /api/v1/candidates — Create candidate
- GET /api/v1/candidates — List candidates (search, filter)
- GET /api/v1/candidates/{id} — Get candidate detail with interview history
- POST /api/v1/candidates/upload-resume — Upload resume PDF (returns extracted data)
- PUT /api/v1/candidates/{id} — Update candidate info

### 4.5 Report Endpoints
- GET /api/v1/interviews/{id}/report — Get report data
- GET /api/v1/interviews/{id}/report/pdf — Download PDF report
- POST /api/v1/interviews/{id}/report/regenerate — Regenerate report

### 4.6 Coaching Endpoints
- GET /api/v1/interviews/{id}/coaching — Get coaching plan
- POST /api/v1/interviews/{id}/coaching/generate — Generate coaching plan
- GET /api/v1/coaching/{id}/download — Download coaching plan as text/PDF

### 4.7 Analytics Endpoints
- GET /api/v1/analytics/overview — Dashboard overview (total interviews, avg scores, trends)
- GET /api/v1/analytics/candidates/{id}/history — Candidate performance over time
- GET /api/v1/analytics/interviews/{id}/charts — Get chart data for an interview
- GET /api/v1/analytics/skills — Skill distribution across candidates

### 4.8 WebSocket Endpoints
- WS /api/v1/ws/interview/{id} — Real-time interview updates (state changes, new questions, scores)
- WS /api/v1/ws/copilot/{id} — Real-time copilot suggestions for human interviewer

### 4.9 Admin Endpoints
- GET /api/v1/admin/users — List all users
- PATCH /api/v1/admin/users/{id} — Update user role/status
- GET /api/v1/admin/system/health — System health check
- GET /api/v1/admin/system/stats — Usage statistics

---

## 5. Frontend Rebuild (Next.js 15 + shadcn/ui)

### 5.1 Page Structure

**Public Pages**
- `/` — Landing page (marketing, features, CTA)
- `/login` — Login form
- `/register` — Registration form
- `/interview/join/{token}` — Public interview link for candidates (no account required)

**Dashboard Pages (authenticated)**
- `/dashboard` — Overview dashboard (recent interviews, quick stats, activity feed)
- `/dashboard/interviews` — Interview list with filters and search
- `/dashboard/interviews/new` — Create new interview (configure settings, upload JD)
- `/dashboard/interviews/{id}` — Interview detail (status, questions, scores)
- `/dashboard/interviews/{id}/live` — Live interview session (the main interview flow)
- `/dashboard/interviews/{id}/results` — Results page (charts, feedback, question breakdown)
- `/dashboard/interviews/{id}/replay` — Interview replay with emotion timeline
- `/dashboard/interviews/{id}/report` — Report view + download
- `/dashboard/interviews/{id}/coaching` — Coaching plan
- `/dashboard/copilot` — Copilot mode setup
- `/dashboard/copilot/{id}` — Active copilot session
- `/dashboard/candidates` — Candidate management list
- `/dashboard/candidates/{id}` — Candidate profile with history
- `/dashboard/analytics` — Global analytics dashboard
- `/dashboard/settings` — User settings, API keys, preferences
- `/admin/users` — User management (admin only)
- `/admin/system` — System health and config (admin only)

### 5.2 Key UI Components

**Interview Flow (the core experience)**
- `InterviewLobby` — Pre-interview screen with instructions, mic/camera check, and settings
- `QuestionCard` — Animated question display with type badge, difficulty indicator, and TTS button
- `AnswerInput` — Dual-mode answer input (text typing + voice recording with waveform visualization)
- `VideoFeed` — WebRTC-based live camera feed with face detection overlay
- `LiveScoreCard` — Real-time score display that animates on update
- `FollowUpPrompt` — Follow-up question overlay with accept/skip actions
- `InterviewProgress` — Stepper/progress bar showing question count and overall progress
- `InterviewComplete` — Celebration screen with quick stats and next steps

**Results & Analytics**
- `ScoreOverview` — Large animated score gauge with grade badge
- `PerformanceCharts` — Tabbed chart view (bar, line, area, radar, pie, step, grouped)
- `EmotionTimeline` — Interactive timeline with emotion markers and playback
- `QuestionBreakdown` — Expandable question cards with scores and answer text
- `FeedbackPanel` — Strengths/weaknesses/suggestions in card layout
- `ScoreComparison` — Compare current interview with past interviews

**Copilot Mode**
- `CopilotSidebar` — Real-time suggestion feed with type icons and action buttons
- `LiveScoreboard` — Rolling score tracker with trend indicator
- `TopicCoverage` — Visual grid showing which topics are covered vs. gaps
- `QuickActions` — One-click buttons for common interviewer actions

**Coaching**
- `CoachingOverview` — Strength/weakness summary with progress bars
- `StudyTimeline` — 1-week / 1-month / 3-month roadmap tabs
- `TopicCard` — Individual topic breakdown with resources and exercises
- `ResourceGrid` — Filterable resource list grouped by type

**Shared**
- `DataTable` — Sortable, filterable table with pagination (for candidates, interviews)
- `MetricCard` — Animated counter with icon and optional delta
- `StatusBadge` — Color-coded status indicators
- `FileUpload` — Drag-and-drop file upload with progress bar
- `EmptyState` — Illustrated empty state with CTA
- `ErrorBoundary` — Graceful error handling with retry

### 5.3 Design System

**Theme**: Dark-first with light mode toggle. Color palette based on shadcn/ui's zinc/slate base with accent colors:
- Primary: Indigo (#6366f1)
- Success: Emerald (#10b981)
- Warning: Amber (#f59e0b)
- Error: Red (#ef4444)
- Info: Sky (#0ea5e9)

**Typography**: Inter (body) + JetBrains Mono (code/metrics)

**Animations**: Framer Motion for page transitions, score count-ups, card entrances, and progress animations. Subtle and purposeful — not decorative.

**Responsive**: Mobile-first design. Interview flow works on tablets. Admin dashboard optimized for desktop.

### 5.4 State Management
- **Server State**: TanStack Query for all API data (candidates, interviews, reports). Auto-refetch, optimistic updates, cache invalidation.
- **Client State**: Zustand for interview session state (current question, answers, scores). Persisted to sessionStorage for page refresh resilience.
- **Real-time**: Native WebSocket integration via TanStack Query's queryClient.setQueryData for live interview updates.

---

## 6. New Features to Add

### 6.1 Authentication & Multi-Tenancy
- Email + password registration with email verification
- JWT-based authentication with refresh token rotation
- Role-based access: Admin (manage users/system), Interviewer (create/conduct interviews), Candidate (take interviews)
- Interviewer can create shareable interview links (candidates don't need accounts)
- Admin dashboard for user management and system configuration

### 6.2 Job Description Matching
- Upload or paste a job description alongside the resume
- RAG pipeline extracts requirements and maps them to candidate skills
- Questions are generated to specifically test job-relevant skills
- Gap analysis: which job requirements the candidate hasn't demonstrated

### 6.3 Coding Interview Mode
- In-browser code editor (Monaco Editor — same as VS Code)
- Support for Python, JavaScript, Java, C++
- Syntax highlighting, autocomplete, error detection
- Code execution sandbox (optional — via Judge0 API or Docker sandbox)
- Code quality scoring (correctness + complexity + style)

### 6.4 Async/Recorded Interviews
- Candidate records answers on their own time (no live interviewer needed)
- Timed questions with configurable time limits
- Auto-advance when time expires
- Interviewer reviews recordings later with copilot suggestions

### 6.5 Multi-Language Support
- Interview interface in multiple languages (English, Hindi, Spanish, etc.)
- Whisper supports 99 languages — expose language selection
- TTS in candidate's preferred language
- UI internationalization via next-intl

### 6.6 Team/Organization Features
- Organization-level accounts with multiple interviewers
- Shared question banks and interview templates
- Candidate pipeline tracking (applied → interviewing → hired/rejected)
- Team analytics dashboard

### 6.7 Enhanced AI Features
- Structured answer evaluation rubrics (per-question scoring criteria)
- Plagiarism detection (flag answers that are too similar across candidates)
- Interview difficulty calibration based on aggregate candidate performance
- AI-generated interview summaries for hiring managers

### 6.8 Integration Capabilities
- REST API for third-party integration (ATS systems, HR tools)
- Webhook support for interview events (started, completed, scored)
- Calendar integration for scheduling interviews
- Email notifications (interview invites, results, coaching plans)

### 6.9 Accessibility & UX
- Keyboard-navigable interview flow
- Screen reader support (ARIA labels throughout)
- High contrast mode
- Adjustable font sizes
- Progress persistence (resume interview after browser crash)

---

## 7. Migration Strategy

### Phase 1: Foundation (Week 1-2)
1. Set up Next.js 15 project with TypeScript, Tailwind, shadcn/ui
2. Set up FastAPI project with SQLAlchemy 2.0, Alembic, Pydantic v2
3. Design and migrate database schema (PostgreSQL + Alembic)
4. Implement authentication (JWT register/login/refresh)
5. Create Docker Compose setup (PostgreSQL, Redis, API, Frontend)
6. Set up shared types/interfaces between frontend and backend

### Phase 2: Core Interview Flow (Week 3-4)
1. Migrate resume parsing module to FastAPI service
2. Implement candidate CRUD endpoints
3. Build interview creation and management API
4. Port question generation (template + LLM) to new architecture
5. Build the live interview UI (question display, text answer, progress)
6. Implement WebSocket for real-time interview state updates

### Phase 3: ML Pipeline (Week 5-6)
1. Migrate speech-to-text to faster-whisper with Celery async tasks
2. Port voice emotion analysis (librosa) to async service
3. Migrate answer evaluation (semantic + keyword + concept) to service layer
4. Implement confidence scoring as a service
5. Build audio upload and processing pipeline
6. Integrate emotion detection (optional DeepFace or lighter alternative)

### Phase 4: Results & Reporting (Week 7)
1. Build results page with charts (Recharts)
2. Port PDF report generation to new architecture
3. Implement interview replay with emotion timeline
4. Build coaching plan generation and display
5. Implement report download (PDF + structured data export)

### Phase 5: Advanced Features (Week 8-9)
1. Implement copilot mode with WebSocket real-time suggestions
2. Build analytics dashboard (global stats, candidate history)
3. Add job description matching with RAG pipeline
4. Implement async/recorded interview mode
5. Build admin panel (user management, system config)

### Phase 6: Polish & Deploy (Week 10)
1. Comprehensive testing (unit, integration, E2E)
2. Performance optimization (caching, lazy loading, code splitting)
3. Security audit (input validation, rate limiting, CORS, CSP)
4. Documentation (API docs via FastAPI auto-docs, user guide, deployment guide)
5. Production Docker setup with nginx reverse proxy
6. Monitoring and logging (structured logs, health checks)

---

## 8. Testing Strategy

### 8.1 Backend Tests (pytest + httpx)
- Unit tests for all service functions
- Integration tests for API endpoints (TestClient + async)
- Database tests with transaction rollback (pytest-asyncio + SQLAlchemy)
- ML module tests with mock models (no actual inference in CI)
- WebSocket tests for real-time features

### 8.2 Frontend Tests (Vitest + Testing Library)
- Component unit tests for all interactive components
- Hook tests for custom hooks (useInterview, useAuth, etc.)
- Integration tests for page flows (login → dashboard → interview)
- Visual regression tests (Playwright screenshot comparison)

### 8.3 E2E Tests (Playwright)
- Full interview flow: register → create interview → take interview → view results
- Authentication flow: register → login → refresh → logout
- Copilot flow: start copilot → receive suggestions → review
- Admin flow: manage users → view system stats

### 8.4 Performance Tests
- Load testing with Locust (concurrent interviews, API throughput)
- ML inference benchmarks (Whisper latency, embedding generation speed)

---

## 9. DevOps & Deployment

### 9.1 Docker Compose (Development)
- postgres:16 — Database
- redis:7 — Cache + Celery broker
- minio — S3-compatible file storage
- api — FastAPI application
- worker — Celery worker for async tasks
- web — Next.js frontend

### 9.2 Production Deployment
- Docker Compose or Kubernetes
- nginx as reverse proxy (SSL termination, static file serving)
- Environment-specific config via .env files
- Database backups (pg_dump scheduled via cron)
- Log aggregation (structured JSON logs → file or stdout for Docker)

### 9.3 CI/CD (GitHub Actions)
- Lint (ruff for Python, ESLint for TypeScript)
- Type check (mypy for Python, tsc for TypeScript)
- Test (pytest for backend, vitest for frontend, playwright for E2E)
- Build (Docker images)
- Deploy (manual trigger or tag-based)

---

## 10. Configuration Management

### 10.1 Backend (.env)
- DATABASE_URL — PostgreSQL connection string
- REDIS_URL — Redis connection string
- JWT_SECRET — Token signing key
- JWT_ACCESS_EXPIRE_MINUTES — Access token TTL (default: 30)
- JWT_REFRESH_EXPIRE_DAYS — Refresh token TTL (default: 7)
- OPENAI_API_KEY — For LLM features
- OPENAI_BASE_URL — Custom endpoint (for proxies/alternatives)
- OPENAI_MODEL — Default model name
- S3_ENDPOINT, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY — MinIO config
- WHISPER_MODEL — faster-whisper model size
- SPACY_MODEL — spaCy model name
- SENTENCE_TRANSFORMER_MODEL — Embedding model
- CELERY_BROKER_URL — Redis URL for Celery
- CORS_ORIGINS — Allowed frontend origins
- LOG_LEVEL — Logging verbosity

### 10.2 Frontend (.env.local)
- NEXT_PUBLIC_API_URL — Backend API base URL
- NEXT_PUBLIC_WS_URL — WebSocket base URL
- NEXT_PUBLIC_APP_NAME — Application name
- NEXT_PUBLIC_APP_VERSION — Current version

---

## 11. What Gets Preserved vs. Replaced

### Preserved (logic migrates, implementation changes)
- Resume parsing algorithm (pdfplumber + PyPDF2 fallback) — move to FastAPI service
- Skill extraction (spaCy NER + taxonomy matching) — move to ML service
- Skill graph (NetworkX) — move to service, store in PostgreSQL JSONB
- Question generation (template + OpenAI LLM) — move to service
- Difficulty manager (rolling average) — move to service
- Answer evaluation (semantic + keyword + concept) — move to service
- Confidence model (4-signal fusion) — move to service
- Voice emotion analysis (librosa) — move to Celery task
- TTS (gTTS + pyttsx3) — move to service
- STT (Whisper) — replace with faster-whisper, move to Celery task
- Performance engine — move to analytics service
- Feedback generator — move to report service
- PDF report generator — move to Celery task
- Chart generation — replace with Recharts on frontend (server sends data, client renders)
- Copilot suggestion engine — move to service with WebSocket delivery
- Coaching plan generator — move to service
- RAG chain — move to service with pgvector
- Adaptive pacer — move to service
- All constants, templates, prompt definitions — move to config/seeds

### Replaced
- Streamlit → Next.js 15 + React 19
- MongoDB → PostgreSQL 16 + Redis 7
- pymongo → SQLAlchemy 2.0 (async) + Alembic
- Manual dataclass models → SQLAlchemy ORM + Pydantic schemas
- Streamlit session state → JWT auth + Zustand + TanStack Query
- Streamlit st.camera_input → WebRTC video (LiveKit/Daily.js)
- Plotly server-side charts → Recharts client-side charts
- FPDF2 → react-pdf or server-side WeasyPrint (better typography)
- Global in-memory sessions → Redis-backed session cache
- Synchronous everything → Async FastAPI + Celery tasks
- DeepFace (broken) → Optional: lighter model or API service

### Removed
- All __pycache__ directories
- Unused/commented-out DeepFace references
- Dummy stub fallbacks in frontend pages
- Manual sys.path manipulation

---

## 12. Estimated Effort

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 1. Foundation | 2 weeks | Working auth, DB, Docker setup, basic pages |
| 2. Core Interview | 2 weeks | End-to-end interview flow (text-based) |
| 3. ML Pipeline | 2 weeks | Voice, emotion, evaluation working |
| 4. Results & Reports | 1 week | Charts, PDF, coaching plans |
| 5. Advanced Features | 2 weeks | Copilot, analytics, JD matching, async mode |
| 6. Polish & Deploy | 1 week | Tests, docs, production setup |
| **Total** | **10 weeks** | **Production-ready platform** |

---

## 13. Quick Wins (Implementable Immediately)

These can be done before the full rebuild to improve the current system:

1. **Add .gitignore entries** for __pycache__, outputs/, .env, *.pyc
2. **Fix DeepFace** — uncomment in requirements.txt or replace with a lighter alternative
3. **Add proper error boundaries** in Streamlit pages (try/except with user-friendly messages)
4. **Add database indexes** — create_indexes() call on startup for MongoDB collections
5. **Add input validation** — validate email format, name length, file type on upload
6. **Add session persistence** — save interview progress to MongoDB so it survives restarts
7. **Improve Whisper performance** — switch to faster-whisper or use smaller model
8. **Add rate limiting** — protect API endpoints from abuse
9. **Add structured logging** — JSON log format for better debugging
10. **Clean up dead code** — remove commented-out imports, unused functions, __pycache__ from repo
