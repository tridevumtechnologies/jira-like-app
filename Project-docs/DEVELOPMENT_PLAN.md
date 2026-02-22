# Development Plan
## Jira-Like Project Management Application

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18 + TypeScript + Vite |
| Styling | TailwindCSS |
| State / Data | Redux Toolkit (auth state) + React Query (server state) |
| HTTP Client | Axios |
| Routing | React Router v6 |
| Backend | Python 3.12 + FastAPI + Uvicorn |
| Auth | python-jose (JWT) + passlib[bcrypt] |
| ORM / Migrations | SQLAlchemy 2.0 (async) + Alembic |
| Validation | Pydantic v2 |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| Package Manager | Poetry (backend) / npm (frontend) |
| Dev Environment | Docker Compose |
| API Docs | FastAPI auto-generated Swagger UI (`/docs`) |

---

## MVP1.0 — Scope: Login, Registration & Ticket Creation

**Timeline**: 3 weeks  
**Target Release**: MVP1.0 — Working authentication and ticket creation  

### What Is In Scope
- User registration (email + password)
- User login / logout (JWT-based)
- Protected routes (redirect to login if unauthenticated)
- Create a ticket (title, type, priority, description)
- View list of tickets (table view)
- View ticket detail

### What Is Out of Scope (→ MVP2.0)
- Sprint management and sprint board
- Backlog drag-and-drop
- Comments and @mentions
- Activity log
- Project member management
- Advanced search and filters
- Notifications
- Reports and analytics
- File attachments
- Ticket linking / watchers
- Bulk operations

---

## Phase 0: Project Setup

### Backend Setup
- [ ] **BE-001**: Initialize FastAPI project with Python 3.12 + Poetry
  - Folder structure: `app/api/v1/`, `app/core/`, `app/models/`, `app/schemas/`, `app/services/`, `app/db/`
  - Configure `pyproject.toml` dependencies, `.env`, `ruff` for linting, `mypy` for type checking
  - Entry point: `uvicorn app.main:app --reload`
  - **Effort**: 3h

- [ ] **BE-002**: Docker Compose — PostgreSQL 15 + Redis 7
  - `docker-compose.yml` with `db`, `redis`, and `api` services
  - Volume mounts for Postgres data persistence
  - `.env.example` with `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`
  - **Effort**: 2h

- [ ] **BE-003**: SQLAlchemy 2.0 async models + Alembic migrations
  - `asyncpg` driver, async `AsyncSession`
  - Models: `User`, `Project`, `ProjectMember`, `Ticket`
  - `alembic init` + initial migration
  - **Effort**: 4h

- [ ] **BE-004**: Auth foundation
  - `passlib[bcrypt]` for password hashing
  - `python-jose[cryptography]` for JWT signing/decoding
  - `get_current_user` dependency (`Depends`)
  - **Effort**: 3h

- [ ] **BE-005**: FastAPI app wiring
  - `CORSMiddleware` (allow `http://localhost:5173`)
  - Health check: `GET /health`
  - Auto Swagger docs at `/docs`
  - **Effort**: 1h

### Frontend Setup
- [ ] **FE-001**: Initialize React 18 + TypeScript project with Vite
  - Folder structure: `src/api/`, `src/components/`, `src/pages/`, `src/store/`, `src/hooks/`, `src/types/`
  - Configure ESLint + Prettier
  - **Effort**: 2h

- [ ] **FE-002**: TailwindCSS
  - Install and configure with `postcss`
  - Define design tokens in `tailwind.config.ts` (colors, font sizes)
  - **Effort**: 1h

- [ ] **FE-003**: React Router v6
  - `BrowserRouter` + route definitions
  - `ProtectedRoute` component (redirects to `/login` if not authenticated)
  - Public layout (auth pages) vs. AppLayout (main app with nav/sidebar)
  - **Effort**: 3h

- [ ] **FE-004**: Axios client (`src/api/client.ts`)
  - Base URL from `import.meta.env.VITE_API_URL`
  - Request interceptor: attach `Authorization: Bearer <token>` from Redux store
  - Response interceptor: on 401, attempt `POST /api/v1/auth/refresh`, retry original request; on failure redirect to `/login`
  - **Effort**: 3h

- [ ] **FE-005**: Redux Toolkit — `authSlice`
  - State: `{ user, accessToken, isAuthenticated, loading }`
  - Actions: `setCredentials`, `clearCredentials`
  - **Effort**: 2h

- [ ] **FE-006**: React Query — `QueryClient` setup
  - `QueryClientProvider` at app root
  - Global error handling (401 → logout)
  - **Effort**: 1h

---

## Sprint 1: Authentication & Ticket Management (MVP1.0)

### Objectives
- Users can register, login, and logout
- Authenticated users can create, list, and view tickets

### Backend Tasks — Auth

- [ ] **BE-101**: `POST /api/v1/auth/register`
  - Pydantic schema: `RegisterRequest { full_name, email, password }`
  - Validate email uniqueness; hash password with `passlib`
  - Return `TokenResponse { access_token, token_type }`
  - **Effort**: 4h

- [ ] **BE-102**: `POST /api/v1/auth/login`
  - Schema: `LoginRequest { email, password }`
  - Verify credentials, issue JWT access token (15 min) + HttpOnly refresh token cookie (7 days)
  - Store refresh token in Redis: `rt:{user_id}:{jti}` with 7-day TTL
  - Return `TokenResponse { access_token, token_type }`
  - **Effort**: 4h

- [ ] **BE-103**: `POST /api/v1/auth/refresh`
  - Read refresh token from HttpOnly cookie
  - Validate against Redis; rotate — delete old, issue new pair
  - Return new `access_token`
  - **Effort**: 3h

- [ ] **BE-104**: `POST /api/v1/auth/logout`
  - Delete refresh token entry from Redis
  - Clear cookie
  - **Effort**: 1h

- [ ] **BE-105**: `GET /api/v1/users/me`
  - `Depends(get_current_user)` guard
  - Return `UserResponse { id, email, full_name, created_at }`
  - **Effort**: 1h

### Backend Tasks — Projects

- [ ] **BE-106**: `POST /api/v1/projects`
  - Schema: `CreateProjectRequest { name, key, description? }`
  - `key` must be uppercase, unique (e.g. `PROJ`)
  - Auto-add creator as OWNER in `project_members` table
  - Return `ProjectResponse`
  - **Effort**: 3h

- [ ] **BE-107**: `GET /api/v1/projects`
  - Return all projects where the current user is a member
  - **Effort**: 2h

- [ ] **BE-108**: `GET /api/v1/projects/{project_id}`
  - Return project detail; 403 if current user is not a member
  - **Effort**: 1h

### Backend Tasks — Tickets

- [ ] **BE-109**: `POST /api/v1/projects/{project_id}/tickets`
  - Schema: `CreateTicketRequest { title, ticket_type, priority, description?, assignee_id? }`
  - Auto-generate ticket key: `{PROJECT_KEY}-{count+1}` (e.g. `PROJ-1`)
  - Return `TicketResponse`
  - **Effort**: 5h

- [ ] **BE-110**: `GET /api/v1/projects/{project_id}/tickets`
  - Paginated (`skip`, `limit` query params)
  - Return `PaginatedResponse[TicketResponse]`
  - **Effort**: 3h

- [ ] **BE-111**: `GET /api/v1/tickets/{ticket_id}`
  - Full ticket detail; 403 if not project member; 404 if not found
  - **Effort**: 2h

- [ ] **BE-112**: `PUT /api/v1/tickets/{ticket_id}`
  - Schema: `UpdateTicketRequest` (all fields optional — partial update)
  - Permission: assignee or project OWNER/ADMIN
  - **Effort**: 3h

- [ ] **BE-113**: `DELETE /api/v1/tickets/{ticket_id}`
  - Soft delete (`is_deleted = true`); OWNER/ADMIN only
  - **Effort**: 1h

### Frontend Tasks — Auth

- [ ] **FE-101**: Login page (`/login`)
  - Form: email + password with client-side validation
  - Calls `POST /api/v1/auth/login`, stores `access_token` in Redux
  - Redirect to `/projects` on success; inline error on 401
  - **Effort**: 4h

- [ ] **FE-102**: Register page (`/register`)
  - Form: full name, email, password, confirm password
  - Calls `POST /api/v1/auth/register`, auto-login on success
  - **Effort**: 4h

- [ ] **FE-103**: Session restore on app load
  - App init: call `POST /api/v1/auth/refresh` (cookie sent automatically)
  - Success → restore auth state in Redux; failure → stay on `/login`
  - **Effort**: 3h

### Frontend Tasks — Layout & Navigation

- [ ] **FE-104**: `ProtectedRoute` component
  - Checks `isAuthenticated` from Redux; redirects to `/login` if false
  - **Effort**: 1h

- [ ] **FE-105**: `AppLayout` component
  - Top navbar: app logo, user avatar + name, logout button
  - Left sidebar: project list navigation links
  - Main `<Outlet />` content area
  - **Effort**: 5h

### Frontend Tasks — Projects

- [ ] **FE-106**: Projects list page (`/projects`)
  - `useQuery` → `GET /api/v1/projects`
  - Display project cards (name, key, description)
  - "New Project" button opens create modal
  - **Effort**: 4h

- [ ] **FE-107**: Create project modal
  - Fields: name, key (auto-suggested, uppercase), description
  - `useMutation` → `POST /api/v1/projects`; invalidates `["projects"]` query on success
  - **Effort**: 3h

### Frontend Tasks — Tickets

- [ ] **FE-108**: Tickets list page (`/projects/:projectId/tickets`)
  - `useQuery` → `GET /api/v1/projects/:projectId/tickets`
  - Table: Key, Title, Type, Priority, Status; clicking Key navigates to detail
  - "New Ticket" button
  - **Effort**: 5h

- [ ] **FE-109**: Create ticket modal
  - Fields: title (required), type (`Bug | Story | Task | Epic`), priority (`Blocker | High | Medium | Low`), description (textarea)
  - `useMutation` → `POST /api/v1/projects/:projectId/tickets`; invalidates ticket list query
  - **Effort**: 5h

- [ ] **FE-110**: Ticket detail page (`/tickets/:ticketId`)
  - `useQuery` → `GET /api/v1/tickets/:ticketId`
  - Display all fields; inline editable status dropdown
  - Back link to tickets list
  - **Effort**: 5h

### Deliverables — MVP1.0
- ✅ Users can register and login
- ✅ Authenticated users can create tickets
- ✅ Authenticated users can list and view ticket details
- ✅ Unauthenticated users are redirected to login

---

## MVP2.0 — Backlog (Future Sprints)

### Sprint Management
- Sprint creation, start, complete lifecycle  
- Sprint board (Kanban with drag-and-drop)  
- Sprint planning interface  
- Sprint statistics  

### Backlog Management
- Prioritized backlog list  
- Drag-to-reorder  
- Move tickets to sprint  

### Collaboration
- Comments with rich text and @mentions  
- Activity log / ticket history  
- Ticket watchers  

### Project & Team Management
- Add / remove project members  
- Role-based access control  

### Search & Filtering
- Advanced multi-criteria filters  
- Saved filters  
- Quick filters (my tickets, due this week, unassigned)  

### Notifications
- In-app notifications  
- Email notifications  

### Reporting & Analytics
- Burndown chart  
- Velocity chart  
- Sprint completion rate  
- User workload report  

### Polish & Deployment
- Skeleton loaders, optimistic updates  
- Mobile responsive design  
- Keyboard shortcuts  
- Code splitting / lazy loading  
- E2E testing (Playwright/Cypress)  
- Staging and production deployment  

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Database performance | Indexes on all FK columns; paginate every list endpoint from day 1 |
| Auth security | `passlib[bcrypt]`, 15-min JWT access tokens, Redis-backed refresh token rotation |
| Async SQLAlchemy pitfalls | Use `AsyncSession` throughout; never mix sync/async calls; scope sessions per request via `Depends` |
| Pydantic v2 breaking changes | Pin `pydantic>=2.0,<3.0`; use `model_config = ConfigDict(...)` not deprecated `class Config` |
| CORS in local dev | `CORSMiddleware` with `allow_origins=["http://localhost:5173"]` and `allow_credentials=True` |
| Refresh token cookie not sent | Axios: `withCredentials: true`; FastAPI: `Set-Cookie` with `SameSite=Lax` |
| Scope creep | Anything not listed in MVP1.0 scope is deferred to MVP2.0 — no exceptions |

---

## Definition of Done (MVP1.0)

A task is "done" when:
- [ ] Code written and follows project coding standards
- [ ] Feature works end-to-end (backend + frontend integrated)
- [ ] Basic error handling in place (API errors shown in UI)
- [ ] No unhandled crashes
- [ ] Merged to `main`

---

## Effort Summary — MVP1.0

| Area | Tasks | Estimated Hours |
|------|-------|-----------------|
| Backend setup (FastAPI, SQLAlchemy, Alembic, Docker) | BE-001 – BE-005 | ~13h |
| Backend auth endpoints | BE-101 – BE-105 | ~13h |
| Backend project endpoints | BE-106 – BE-108 | ~6h |
| Backend ticket endpoints | BE-109 – BE-113 | ~14h |
| Frontend setup (Vite, TailwindCSS, Router, Axios, Redux, React Query) | FE-001 – FE-006 | ~12h |
| Frontend auth pages & session restore | FE-101 – FE-103 | ~11h |
| Frontend layout & routing | FE-104 – FE-105 | ~6h |
| Frontend projects (list + create) | FE-106 – FE-107 | ~7h |
| Frontend tickets (list, create, detail) | FE-108 – FE-110 | ~15h |
| **Total** | | **~97h** |

---

**Document Version**: 2.1  
**Last Updated**: February 22, 2026  
**Stack**: React 18 + TypeScript + Vite (frontend) · Python 3.12 + FastAPI (backend) · PostgreSQL 15 · Redis 7  
**Status**: MVP1.0 Planning Complete — Ready to Build
