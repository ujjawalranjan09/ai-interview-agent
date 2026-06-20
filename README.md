<div align="center">

# AI Interview Agent

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**Production-grade AI platform for conducting adaptive technical interviews with multimodal analysis.**

</div>

---

## Overview

AI Interview Agent is a full-stack platform that automates technical interviews using artificial intelligence. It parses resumes, generates adaptive questions, analyzes candidate responses through voice and video, and produces comprehensive performance reports.

### Key Capabilities

- **Multimodal Analysis** — Combines facial emotion, voice tone, and speech patterns for confidence scoring
- **Adaptive Questioning** — Dynamically adjusts question difficulty based on candidate performance
- **Real-time Processing** — WebSocket-powered live interview updates and AI copilot assistance
- **Enterprise Ready** — Multi-tenant architecture with RBAC, GDPR compliance, and audit logging

---

## Features

### Core Interview Engine
- Resume parsing with skill extraction and knowledge graph generation
- Adaptive difficulty system (Easy → Medium → Hard → Expert)
- Voice input via OpenAI Whisper with real-time transcription
- Facial emotion detection using DeepFace (7 emotion classes)
- Voice emotion analysis for pitch, speed, and hesitation patterns
- Semantic answer scoring with keyword and concept coverage

### Platform Features
- JWT authentication with role-based access control
- Organization management for multi-tenancy
- Analytics dashboard with aggregate metrics and trends
- AI copilot for real-time interviewer assistance
- Interview scheduling with calendar integration
- Global search across all entities
- GDPR compliance with consent management and data export

### Integrations
- Slack and Microsoft Teams notifications
- ATS sync (Greenhouse, Lever)
- Push notifications via Web Push Protocol
- Sentry error tracking
- 7-language internationalization

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.10+, FastAPI, SQLAlchemy (async) |
| Frontend | Next.js 16, React 19, TypeScript, TailwindCSS 4 |
| Database | PostgreSQL (primary), Redis (cache) |
| AI/ML | OpenAI Whisper, DeepFace, sentence-transformers, spaCy |
| Real-time | WebSockets (FastAPI + Next.js) |
| Auth | JWT (access + refresh tokens) |
| PWA | next-pwa (service worker, offline support) |
| Monitoring | Sentry, structured logging |
| I18n | next-intl (7 languages) |
| Package Manager | pnpm (monorepo) |
| Containerization | Docker, Docker Compose |

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- pnpm

### Installation

```bash
# Clone repository
git clone https://github.com/ujjawalranjan09/ai-interview-agent.git
cd ai-interview-agent

# Install dependencies
pnpm install
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database and API credentials

# Run database migrations
cd apps/api
alembic upgrade head
cd ../..

# Start development servers
pnpm dev
```

### Docker

```bash
docker-compose up --build
```

Services:
- API: http://localhost:8000
- Web: http://localhost:3000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

---

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://localhost:5432/ai_interview` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `JWT_SECRET` | Secret key for JWT tokens | — |
| `OPENAI_API_KEY` | OpenAI API key (optional) | — |
| `WHISPER_MODEL` | Speech recognition model size | `base` |

---

## Project Structure

```
ai-interview-agent/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/v1/        # API endpoints
│   │   │   ├── core/          # Config, security, database
│   │   │   ├── ml/            # AI/ML models
│   │   │   ├── schemas/       # Pydantic models
│   │   │   └── services/      # Business logic
│   │   └── tests/             # API tests
│   └── web/                    # Next.js frontend
│       ├── app/                # App router pages
│       ├── components/         # React components
│       └── hooks/              # Custom hooks
├── modules/                    # Shared Python modules
├── infra/                      # Docker and deployment configs
└── load_tests/                 # Performance testing
```

---

## API Documentation

Once running, access the interactive API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Testing

```bash
# Backend tests
cd apps/api
pytest tests/ -v

# Frontend tests
cd apps/web
pnpm test
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built by [Ujjawal Ranjan](https://github.com/ujjawalranjan09)**

</div>
