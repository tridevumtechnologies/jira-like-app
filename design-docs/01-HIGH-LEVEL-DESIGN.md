# High-Level Design (HLD)
## Jira-Like Project Management Application

**Version**: 2.0 | **Date**: February 21, 2026 | **Status**: Approved

> Backend: **FastAPI (Python 3.12)** + SQLAlchemy 2.0 + Alembic + Pydantic v2.  
> Frontend: **React 18 + TypeScript** (unchanged).  
> Database: **PostgreSQL 15** (unchanged).

---

## 1. Introduction

### 1.1 Purpose
Authoritative architectural blueprint establishing system boundaries, major components, and interaction patterns across all four delivery phases.

### 1.2 Design Principles
| Principle | Rationale |
|-----------|-----------|
| **API-First** | All functionality via versioned REST APIs; React SPA is just one consumer |
| **Separation of Concerns** | Frontend, backend, and data layers independently deployable |
| **Async-First Backend** | FastAPI + asyncpg + redis-py async for high-concurrency without threading overhead |
| **Security by Default** | Auth, RBAC, and data protection at every layer |
| **Pythonic Backend** | Enables Phase 3 analytics via Pandas/NumPy inside the same Python service |
| **Progressive Delivery** | MVP → Enhanced → Analytics → Advanced (4 phases) |
| **Horizontal Scalability** | Stateless FastAPI processes; all shared state in Redis |
| **Observability** | Structured logs (structlog), metrics (CloudWatch), traces (AWS X-Ray) |

---

## 2. System Context

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL USERS                                │
│                                                                         │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                 │
│   │  Developer  │   │   Product   │   │  Scrum      │                 │
│   │  (Browser)  │   │   Manager   │   │  Master     │                 │
│   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘                 │
└──────────┼─────────────────┼─────────────────┼────────────────────────┘
           └─────────────────┴─────────────────┘
                             │ HTTPS / WSS
                    ┌────────▼────────┐
                    │   AWS ALB       │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼──────┐ ┌─────▼──────┐ ┌───▼────────────┐
     │  React SPA    │ │  FastAPI   │ │  WebSocket     │
     │  (CloudFront  │ │  REST API  │ │  (socketio)    │
     │  + S3)        │ │  Python    │ │  /ws endpoint  │
     └──────────────-┘ └─────┬──────┘ └────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼──-───┐ ┌─────▼─────┐ ┌─────▼─────────┐
     │ PostgreSQL 15 │ │  Redis 7  │ │    AWS S3     │
     │  (RDS Multi-AZ│ │(ElastiCache│ │  (Files)      │
     └───────────────┘ └───────────┘ └───────────────┘
```

---

## 3. Major System Components

### 3.1 Frontend Application (React SPA)
| Attribute | Value |
|-----------|-------|
| Technology | React 18 + TypeScript + Vite |
| State Management | Redux Toolkit + React Query (TanStack) |
| Styling | TailwindCSS + shadcn/ui |
| Routing | React Router v6 |
| Real-time Client | Socket.IO Client 4.x |
| HTTP Client | Axios |
| Hosting | AWS CloudFront + S3 |

### 3.2 Backend API (FastAPI — Python 3.12)
| Attribute | Value |
|-----------|-------|
| Framework | FastAPI 0.110+ |
| Runtime | Python 3.12 + Uvicorn ASGI |
| ORM | SQLAlchemy 2.0 (async) |
| DB Driver | asyncpg |
| Migrations | Alembic |
| Schema Validation | Pydantic v2 |
| Authentication | python-jose (JWT HS256) + passlib (bcrypt) |
| API Docs | Auto-generated OpenAPI / Swagger UI at `/docs` |
| Real-time | python-socketio 5.x + AsyncRedisManager |
| Rate Limiting | slowapi |
| Hosting | AWS ECS Fargate (python:3.12-slim container) |

#### FastAPI Router Structure
```
app/
├── main.py                  ← app factory, lifespan hooks, CORS, middleware
├── core/
│   ├── config.py            ← pydantic-settings (DATABASE_URL, JWT_SECRET, etc.)
│   ├── security.py          ← create_access_token(), verify_token(), hash_password()
│   ├── database.py          ← create_async_engine(), AsyncSessionLocal, get_db()
│   └── redis.py             ← get_redis() async dependency
├── api/
│   └── v1/
│       ├── router.py        ← aggregates all sub-routers under /api/v1
│       ├── auth.py          ← POST /auth/login, /register, /refresh, /logout
│       ├── users.py         ← GET/PUT /users/me
│       ├── projects.py      ← CRUD /projects, /projects/{id}/members
│       ├── tickets.py       ← CRUD /tickets, /tickets/{id}/transition
│       ├── sprints.py       ← CRUD /sprints, /sprints/{id}/start, /complete
│       ├── comments.py      ← CRUD /tickets/{id}/comments
│       ├── search.py        ← GET /search/tickets
│       └── notifications.py ← GET /notifications
├── models/                  ← SQLAlchemy ORM declarative models
├── schemas/                 ← Pydantic v2 BaseModel request/response schemas
├── services/                ← Business logic layer (async Python classes)
├── repositories/            ← DB query layer (SQLAlchemy select/insert/update)
├── dependencies/            ← FastAPI Depends() — auth, RBAC, pagination, db session
├── websocket/               ← python-socketio server + event handler registrations
└── migrations/              ← Alembic revision files
```

### 3.3 Primary Database (PostgreSQL 15)
- Hosted on AWS RDS Multi-AZ (production)
- Connected via `asyncpg` driver with SQLAlchemy async sessions
- Migrations managed by Alembic (`alembic upgrade head` in ECS task on deployment)
- **Core tables**: `users`, `projects`, `project_members`, `tickets`, `ticket_history`, `sprints`, `sprint_tickets`, `comments`, `labels`, `ticket_labels`, `notifications`

### 3.4 Cache Layer (Redis 7)
| Data | Cache Key | TTL |
|------|-----------|-----|
| Sprint Board | `board:{sprint_id}` | 5 min |
| Active Sprint | `project:{id}:active_sprint` | 10 min |
| User Profile | `user:{id}:profile` | 30 min |
| Refresh Tokens | `rt:{user_id}:{jti}` | 7 days |
| Rate Limit | `rl:{ip}:{endpoint}` | 60 sec |

### 3.5 Real-time (python-socketio)
- `socketio.ASGIApp` mounted inside FastAPI at `/ws`
- `AsyncRedisManager` for multi-ECS-task room broadcasting
- Rooms: `board:{sprint_id}`, `ticket:{ticket_id}`, `user:{user_id}`

### 3.6 File Storage (AWS S3)
- Attachments uploaded via pre-signed POST URL generated by `boto3`
- Max 25 MB per file; virus scanning in Phase 2

### 3.7 Email (AWS SES)
- Transactional email via `boto3` SES client
- Stubbed as `NotificationService.queue_email()` in Phase 1, wired in Phase 2

---

## 4. Delivery Phases

### Phase 1 — MVP (Weeks 1–10) ← CURRENT
| Feature | Scope |
|---------|-------|
| Auth | Registration, login, JWT, RBAC (4 roles) |
| Projects | Create, configure, invite members |
| Tickets | Full CRUD, status transitions, assignment, labels, priorities |
| Sprints | Create, start, complete; Kanban board |
| Backlog | Prioritized list, drag-to-reorder |
| Search | Basic keyword + filter by status/assignee/priority |

### Phase 2 — Enhanced (Weeks 11–18)
Comments, @mentions, ticket linking, bulk operations, audit log, email notifications, file attachments

### Phase 3 — Analytics (Weeks 19–24)
Burndown / velocity charts (Pandas/NumPy on Python backend), cumulative flow, workload distribution

### Phase 4 — Advanced (Future)
Real-time collaboration, workflow automation, GitHub/Slack integrations, ML-based ticket assignment

---

## 5. Data Flow Patterns

### 5.1 Read Flow (Cache Hit)
```
Browser → CloudFront → ALB → ECS FastAPI → Redis HIT → 200 Response
```

### 5.2 Read Flow (Cache Miss)
```
Browser → ALB → ECS FastAPI → Redis MISS → PostgreSQL (asyncpg)
                                         → Cache Write → 200 Response
```

### 5.3 Write Flow
```
Browser → ALB → ECS FastAPI → PostgreSQL write (async)
                             → Redis cache invalidation
                             → python-socketio broadcast to room
                             → SES email queue (Phase 2)
```

### 5.4 Auth Flow
```
POST /auth/login
  → passlib verify_password(plain, hashed)
  → python-jose create_access_token (HS256, 15min)
  → UUID4 refresh_token stored in Redis (7d)
  → Response: { access_token } + HttpOnly cookie: refresh_token

GET /api/v1/any-protected-route
  → Depends(get_current_user)
  → python-jose decode JWT
  → SQLAlchemy fetch user (with cache)
  → 401 if expired or not found
```

---

## 6. Cross-Cutting Concerns

### 6.1 Security
- All routes protected via `Depends(get_current_user)` except public auth endpoints
- RBAC via `Depends(require_project_role(ProjectRole.OWNER, ProjectRole.MEMBER))`
- Passwords: `passlib.context.CryptContext(schemes=["bcrypt"], deprecated="auto")` cost=12
- Pydantic v2 validation: automatic 422 on malformed input with detailed field errors
- Rate limiting via `slowapi` (100 req/min general, 10 req/min on `/auth/*`)
- CORS restricted to allowed frontend origins via FastAPI `CORSMiddleware`
- SQL injection impossible via SQLAlchemy parameterized statements

### 6.2 Observability
- Structured JSON logs: `structlog` with correlation ID injected by middleware
- Metrics: AWS CloudWatch (ECS + custom `boto3` metrics)
- Traces: AWS X-Ray via `aws-xray-sdk` middleware
- Alerts: error rate > 1%, P95 latency > 500ms

---

## 7. Technology Stack Summary

| Layer | Technology | Version |
|-------|------------|---------|
| Frontend Framework | React | 18 |
| Frontend Language | TypeScript | 5.x |
| Frontend Build | Vite | 5.x |
| Frontend State | Redux Toolkit + React Query | Latest |
| Frontend UI | TailwindCSS + shadcn/ui | Latest |
| Frontend Real-time | Socket.IO Client | 4.x |
| Backend Runtime | Python | 3.12 |
| Backend Framework | FastAPI | 0.110+ |
| Backend Server | Uvicorn (ASGI) | Latest |
| ORM | SQLAlchemy 2.0 (async) | 2.x |
| DB Driver | asyncpg | Latest |
| Migrations | Alembic | Latest |
| Schema Validation | Pydantic v2 | 2.x |
| Auth JWT | python-jose | 3.x |
| Auth Passwords | passlib + bcrypt | Latest |
| Redis Client | redis-py (async) | 5.x |
| Real-time Server | python-socketio | 5.x |
| Rate Limiting | slowapi | Latest |
| Structured Logging | structlog | Latest |
| HTTP Test Client | httpx | Latest |
| Primary Database | PostgreSQL | 15 |
| Cache | Redis | 7 |
| File Storage | AWS S3 (boto3) | Latest |
| Email | AWS SES (boto3) | Latest |
| Container | Docker (python:3.12-slim) | Latest |
| Orchestration | AWS ECS Fargate | - |
| CI/CD | GitHub Actions | - |
| Backend Testing | pytest + pytest-asyncio | Latest |
| Frontend Testing | Vitest + React Testing Library | Latest |
| E2E Testing | Playwright | Latest |
