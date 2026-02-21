# System Architecture Document
## Jira-Like Project Management Application

**Version**: 2.0 | **Date**: February 21, 2026 | **Status**: Approved

> **v2.0**: Backend is **FastAPI (Python 3.12)**. ORM is **SQLAlchemy 2.0 (async) + Alembic**. Schemas are **Pydantic v2 BaseModel**. Frontend (React + TypeScript), Database (PostgreSQL 15), and Cloud (AWS) are unchanged.

---

## 1. Architecture Overview — RAPP Stack

| Letter | Technology | Role |
|--------|------------|------|
| **R** | React 18 + TypeScript | Frontend SPA |
| **A** | AWS (ECS, RDS, ElastiCache, S3, CloudFront) | Cloud hosting |
| **P** | PostgreSQL 15 | Primary relational data store |
| **P** | Python 3.12 / FastAPI | Backend REST + WebSocket API |

**Why FastAPI over NestJS?**
- Native async/await without Node.js event-loop limitations
- Pydantic v2 provides zero-cost serialization/validation via Rust-backed core
- Auto-generated OpenAPI docs with no extra configuration
- Python ecosystem enables future analytics phase (Pandas, NumPy, scikit-learn) inside same service boundary

---

## 2. Component Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT TIER                                     │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     React SPA (Browser)                              │   │
│  │                                                                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │   │
│  │  │  Auth    │  │ Projects │  │  Board   │  │ Reports  │           │   │
│  │  │  Pages   │  │  Pages   │  │  Pages   │  │  Pages   │           │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │   │
│  │                                                                      │   │
│  │  ┌──────────────────┐    ┌──────────────────┐                      │   │
│  │  │   Redux Store    │    │   React Query    │                      │   │
│  │  │ (auth, ui, notif)│    │ (server state)   │                      │   │
│  │  └──────────────────┘    └──────────────────┘                      │   │
│  │                                                                      │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │   Axios REST Client  │  Socket.IO Client (WSS)                │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────┬──────────────────────────┬────────────────────────┘
                          │ REST / HTTPS              │ WebSocket (WSS)
                          │                           │
┌─────────────────────────▼───────────────────────────▼────────────────────────┐
│                   API TIER — FastAPI (Python 3.12, Uvicorn ASGI)              │
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                     Middleware Pipeline (LIFO)                         │  │
│  │  Incoming →  CorrelationID  →  CORS  →  RateLimitMiddleware           │  │
│  │          →  X-Ray Tracing  →  RequestLogger  → Router dispatch        │  │
│  │  Outgoing ← GlobalExceptionHandler ← Pydantic serialize ← Response   │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │  auth    │ │  users   │ │ projects │ │ tickets  │ │ sprints  │         │
│  │ router   │ │  router  │ │  router  │ │  router  │ │  router  │         │
│  │/api/v1/  │ │/api/v1/  │ │/api/v1/  │ │/api/v1/  │ │/api/v1/  │         │
│  │auth/*    │ │users/*   │ │projects/*│ │tickets/* │ │sprints/* │         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
│                                                                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────────────────────┐    │
│  │comments  │ │  search  │ │notificat.│ │  python-socketio             │    │
│  │  router  │ │  router  │ │  router  │ │  ASGIApp at /ws              │    │
│  └──────────┘ └──────────┘ └──────────┘ └─────────────────────────────┘    │
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                     Shared Infrastructure Layer                        │  │
│  │  AsyncSession (SQLAlchemy + asyncpg)  │  Redis (redis-py async)       │  │
│  │  Security (python-jose + passlib)     │  S3 / SES (boto3)             │  │
│  │  Settings (pydantic-settings)         │  Structlog / X-Ray            │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────┬─────────────────────┬──────────────────────┬──────────────────────┘
           │                     │                       │
┌──────────▼────────┐  ┌─────────▼──────────┐  ┌────────▼──────────┐
│  DATA TIER        │  │  CACHE TIER         │  │  STORAGE TIER     │
│  PostgreSQL 15    │  │  Redis 7            │  │  AWS S3           │
│  (AWS RDS)        │  │  (AWS ElastiCache)  │  │  (boto3 SDK)      │
│  asyncpg driver   │  │  redis-py async     │  │                   │
│                   │  │                     │  │ /attachments/{id} │
│  tables:          │  │  board:{sprint_id}  │  │ /avatars/{user_id}│
│  users            │  │  project:{id}:      │  │                   │
│  projects         │  │    active_sprint    │  └───────────────────┘
│  project_members  │  │  user:{id}:profile  │
│  tickets          │  │  rt:{uid}:{jti}     │
│  ticket_history   │  │  rl:{ip}:{endpoint} │
│  sprints          │  └─────────────────────┘
│  sprint_tickets   │
│  comments         │
│  labels           │
│  ticket_labels    │
│  notifications    │
└───────────────────┘
```

---

## 3. REST API Design

### 3.1 Base URL
```
https://api.yourdomain.com/api/v1/
```
FastAPI auto-serves:
- `/docs` — Swagger UI
- `/redoc` — ReDoc
- `/openapi.json` — raw schema

### 3.2 Authentication Endpoints
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/register` | Create account | No |
| POST | `/auth/login` | Login → `access_token` + refresh cookie | No |
| POST | `/auth/logout` | Revoke refresh token | Yes |
| POST | `/auth/refresh` | New token pair from refresh cookie | Cookie |
| POST | `/auth/forgot-password` | Request reset email | No |
| POST | `/auth/reset-password` | Apply new password | No |
| GET | `/auth/me` | Current user profile | Yes |

### 3.3 Project Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects` | Create project |
| GET | `/projects` | List user's projects |
| GET | `/projects/{id}` | Get project detail |
| PUT | `/projects/{id}` | Update project |
| DELETE | `/projects/{id}` | Soft-delete project |
| GET | `/projects/{id}/members` | List members |
| POST | `/projects/{id}/members` | Invite member |
| PUT | `/projects/{id}/members/{user_id}` | Update member role |
| DELETE | `/projects/{id}/members/{user_id}` | Remove member |

### 3.4 Ticket Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/{id}/tickets` | Create ticket |
| GET | `/projects/{id}/tickets` | List tickets (paginated + filterable) |
| GET | `/tickets/{id}` | Get ticket detail |
| PUT | `/tickets/{id}` | Update ticket fields |
| DELETE | `/tickets/{id}` | Soft-delete |
| POST | `/tickets/{id}/transition` | Status workflow transition |
| PUT | `/tickets/{id}/sprint` | Assign/remove from sprint |
| GET | `/tickets/{id}/history` | Activity log |
| POST | `/tickets/{id}/watch` | Watch ticket |
| DELETE | `/tickets/{id}/watch` | Unwatch |
| GET | `/search/tickets` | Full-text search + filters |

### 3.5 Sprint Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/{id}/sprints` | Create sprint |
| GET | `/projects/{id}/sprints` | List sprints |
| GET | `/sprints/{id}` | Sprint detail |
| PUT | `/sprints/{id}` | Update sprint details |
| POST | `/sprints/{id}/start` | Activate sprint |
| POST | `/sprints/{id}/complete` | Complete sprint |
| GET | `/sprints/{id}/board` | Board grouped by status |
| GET | `/sprints/{id}/stats` | Sprint statistics |
| GET | `/projects/{id}/backlog` | Backlog with ordering |

### 3.6 Standard Response Envelope
```json
{
  "data": { "...resource..." },
  "meta": {
    "page": 1,
    "page_size": 25,
    "total": 150,
    "total_pages": 6
  }
}
```

### 3.7 Error Response (RFC 7807 Problem Detail)
```json
{
  "type": "https://api.yourdomain.com/errors/not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "Ticket PROJ-123 does not exist",
  "instance": "/api/v1/tickets/PROJ-123",
  "correlation_id": "abc-123-xyz"
}
```

### 3.8 Pydantic 422 Validation Error (auto by FastAPI)
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "title"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

---

## 4. Real-Time Architecture (python-socketio)

### 4.1 Setup
```python
# app/websocket/server.py
import socketio

sio = socketio.AsyncServer(
    async_mode="asgi",
    client_manager=socketio.AsyncRedisManager("redis://redis:6379"),
    cors_allowed_origins="*",
)
socket_app = socketio.ASGIApp(sio)

# app/main.py
app.mount("/ws", socket_app)  # WebSocket at wss://api.yourdomain.com/ws
```

### 4.2 Namespaces & Rooms
| Namespace | Room | Purpose |
|-----------|------|---------|
| `/board` | `board:{sprint_id}` | Ticket status changes on Kanban board |
| `/board` | `ticket:{ticket_id}` | Specific ticket updates |
| `/notifications` | `user:{user_id}` | Personal notifications |

### 4.3 Events (Server → Client)
| Event | Payload | Trigger |
|-------|---------|---------|
| `ticket:updated` | `{ ticket_id, changes, updated_by }` | Any field update |
| `ticket:moved` | `{ ticket_id, from_status, to_status }` | Status transition |
| `ticket:assigned` | `{ ticket_id, assignee_id }` | Assignee change |
| `comment:added` | `{ ticket_id, comment }` | New comment |
| `sprint:started` | `{ sprint_id, name }` | Sprint activated |
| `sprint:completed` | `{ sprint_id }` | Sprint completed |
| `notification:new` | `{ notification }` | Any notification |

### 4.4 Emitting from FastAPI Endpoint
```python
# Inside a FastAPI route handler
async def transition_ticket(ticket_id: UUID, body: TransitionRequest, sio=Depends(get_socketio)):
    ticket = await ticket_service.transition(db, ticket_id, body.status)
    await sio.emit(
        "ticket:moved",
        {"ticket_id": str(ticket_id), "from_status": old_status, "to_status": body.status},
        room=f"board:{ticket.sprint_id}",
        namespace="/board",
    )
    return ticket
```

---

## 5. Security Architecture

### 5.1 JWT Token Strategy
```python
# app/core/security.py

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS   = 7
ALGORITHM = "HS256"

def create_access_token(data: dict) -> str:
    payload = {**data, "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)  # python-jose

def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 5.2 FastAPI Auth Dependency Chain
```python
# app/dependencies/auth.py

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = verify_token(token)
    user = await user_repo.get(db, UUID(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401)
    return user

def require_project_role(*roles: ProjectRole):
    """Curried dependency factory — usage: Depends(require_project_role(OWNER, ADMIN))"""
    async def dependency(
        project_id: UUID,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> ProjectMember:
        member = await project_repo.get_member(db, project_id, current_user.id)
        if not member or member.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient project permissions")
        return member
    return dependency
```

### 5.3 RBAC Permission Matrix
| Action | Admin | Project Owner | Team Member | Viewer |
|--------|-------|---------------|-------------|--------|
| Create Project | ✅ | ✅ | ❌ | ❌ |
| Delete Project | ✅ | ✅ | ❌ | ❌ |
| Manage Members | ✅ | ✅ | ❌ | ❌ |
| Create Ticket | ✅ | ✅ | ✅ | ❌ |
| Edit Any Ticket | ✅ | ✅ | ❌ | ❌ |
| Edit Own Ticket | ✅ | ✅ | ✅ | ❌ |
| Delete Ticket | ✅ | ✅ | ❌ | ❌ |
| Create/Start Sprint | ✅ | ✅ | ❌ | ❌ |
| View Everything | ✅ | ✅ | ✅ | ✅ |

---

## 6. State Management (Frontend)

### 6.1 Redux Slices
```
store/
├── authSlice        { user, access_token, is_authenticated, loading }
├── uiSlice          { theme, sidebar_open, active_project_id }
└── notificationSlice { unread_count, items[] }
```

### 6.2 React Query Key Registry
```typescript
const keys = {
  projects:       () => ["projects"],
  project:        (id: string) => ["projects", id],
  tickets:        (projectId: string) => ["projects", projectId, "tickets"],
  ticket:         (id: string) => ["tickets", id],
  board:          (sprintId: string) => ["sprints", sprintId, "board"],
  backlog:        (projectId: string) => ["projects", projectId, "backlog"],
  ticketComments: (ticketId: string) => ["tickets", ticketId, "comments"],
  ticketHistory:  (ticketId: string) => ["tickets", ticketId, "history"],
  sprintStats:    (sprintId: string) => ["sprints", sprintId, "stats"],
};
```

---

## 7. Caching Strategy

| Data | Key Pattern | TTL | Invalidated When |
|------|-------------|-----|------------------|
| Sprint Board | `board:{sprint_id}` | 5 min | Ticket updated / moved |
| Active Sprint | `project:{id}:active_sprint` | 10 min | Sprint started / completed |
| User Profile | `user:{id}:profile` | 30 min | Profile updated |
| Project Members | `project:{id}:members` | 15 min | Member added / removed |
| Refresh Token | `rt:{user_id}:{jti}` | 7 days | Logout / token rotation |
| Rate Limit | `rl:{ip}:{endpoint}` | 60 sec | Auto-expire |

---

## 8. Database Connection Management

```python
# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator

engine = create_async_engine(
    settings.DATABASE_URL,   # "postgresql+asyncpg://user:pass@host/db"
    pool_size=10,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

---

## 9. Testing Strategy

| Level | Framework | Coverage Target |
|-------|-----------|----------------|
| Unit (services/utils) | pytest | 80% |
| Integration (API routes) | pytest + httpx AsyncClient | 70% |
| DB Integration | pytest + testcontainers (PostgreSQL) | 60% |
| Frontend Components | Vitest + React Testing Library | 70% |
| E2E | Playwright | Critical user flows |

```python
# tests/conftest.py — async test fixtures
@pytest_asyncio.fixture
async def async_client(app) -> AsyncGenerator:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def auth_headers(async_client, test_user) -> dict:
    resp = await async_client.post("/api/v1/auth/login", json={...})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
```

---

## 10. Non-Functional Architecture Decisions

### 10.1 Scalability
- FastAPI processes are **fully stateless** — shared state only in Redis
- python-socketio `AsyncRedisManager` means any ECS task can publish to any room
- ECS desired-count auto-scaling on CPU + ALB request count

### 10.2 Async Design
- Every DB operation: `await session.execute(select(...))`
- Every Redis operation: `await redis.get(key)`
- FastAPI never blocks the event loop
- Production: `gunicorn -k uvicorn.workers.UvicornWorker -w 4` per ECS task

### 10.3 Performance
- PostgreSQL composite indexes: `(project_id, status)`, `(sprint_id, status)`, `(assignee_id, project_id)`
- Full-text search: `tsvector` GIN index maintained by PostgreSQL trigger
- N+1 prevention: `selectinload()` / `joinedload()` in SQLAlchemy queries
- Pagination: offset-based for Phase 1; cursor-based option in Phase 3
