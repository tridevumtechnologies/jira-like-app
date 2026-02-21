# Phase 1 Mermaid Diagrams
## Jira-Like Project Management Application

**Version**: 2.0 | **Date**: February 21, 2026 | **Stack**: React + FastAPI (Python 3.12) + PostgreSQL + AWS

> All diagrams updated for FastAPI/Python backend. "NestJS API" is now "FastAPI API". CI/CD uses Poetry + pytest.

---

## Diagram 1 — System Context (C4 Level 1)

```mermaid
C4Context
    title System Context — Jira-Like App

    Person(developer, "Developer", "Creates and updates tickets, views sprint board")
    Person(pm, "Product Manager", "Manages projects, creates backlog, reviews reports")
    Person(sm, "Scrum Master", "Plans and manages sprint lifecycle")

    System(jiraApp, "Jira-Like App", "Project management tool — React SPA + FastAPI (Python 3.12) backend + PostgreSQL")

    System_Ext(email, "AWS SES", "Transactional email delivery")
    System_Ext(storage, "AWS S3", "File attachment storage")
    System_Ext(cdn, "AWS CloudFront", "CDN for React SPA and static assets")

    Rel(developer, jiraApp, "Uses", "HTTPS / WSS")
    Rel(pm, jiraApp, "Uses", "HTTPS")
    Rel(sm, jiraApp, "Uses", "HTTPS")
    Rel(jiraApp, email, "Sends notifications via", "HTTPS / boto3")
    Rel(jiraApp, storage, "Stores attachments via", "HTTPS / boto3")
    Rel(cdn, jiraApp, "Delivers SPA via", "HTTPS")
```

---

## Diagram 2 — Container Diagram (C4 Level 2)

```mermaid
C4Container
    title Container Diagram — Jira-Like App (Phase 1)

    Person(user, "User", "Any authenticated role")

    Container(spa, "React SPA", "React 18 + TypeScript + Vite", "Single-page application served from S3 via CloudFront")
    Container(api, "FastAPI API", "Python 3.12 / FastAPI / Uvicorn (ECS Fargate)", "REST API + WebSocket server. Pydantic v2 validation, python-jose JWT, python-socketio.")
    Container(pg, "PostgreSQL 15", "AWS RDS Multi-AZ", "Primary relational data store. asyncpg driver, Alembic migrations.")
    Container(redis, "Redis 7", "AWS ElastiCache", "Session cache, board state, rate limiting, WebSocket rooms")
    Container(s3, "AWS S3", "Object Storage", "Ticket attachments and user avatars")

    Rel(user, spa, "Opens", "HTTPS")
    Rel(spa, api, "REST calls", "HTTPS / JSON")
    Rel(spa, api, "WebSocket events", "WSS / socket.io")
    Rel(api, pg, "Read / Write", "asyncpg / SQLAlchemy 2.0")
    Rel(api, redis, "Cache & pub/sub", "redis-py async")
    Rel(api, s3, "Upload/Download", "boto3 / pre-signed URLs")
```

---

## Diagram 3 — Authentication Flow (Sequence)

```mermaid
sequenceDiagram
    participant Browser
    participant SPA as React SPA
    participant API as FastAPI API
    participant DB as PostgreSQL
    participant Cache as Redis

    Browser->>SPA: Navigate to /login
    SPA->>Browser: Render LoginForm

    Browser->>SPA: Submit { email, password }
    SPA->>API: POST /api/v1/auth/login { email, password }

    API->>DB: SELECT * FROM users WHERE email = ?
    DB-->>API: user row

    API->>API: passlib.verify_password(plain, hashed)
    alt Invalid credentials
        API-->>SPA: 401 Unauthorized
        SPA-->>Browser: Show error
    else Valid credentials
        API->>API: python-jose.create_access_token(sub=user.id, exp=+15min)
        API->>API: uuid4() → refresh_token
        API->>Cache: SET rt:{user_id}:{jti} "valid" EX 604800
        API-->>SPA: 200 { access_token } + Set-Cookie: refresh_token (HttpOnly)
        SPA->>SPA: Store access_token in Redux (memory only)
        SPA-->>Browser: Redirect to /dashboard
    end

    Note over Browser,Cache: Subsequent requests
    Browser->>SPA: Navigate to /projects
    SPA->>API: GET /api/v1/projects  Authorization: Bearer <access_token>
    API->>API: Depends(get_current_user) → python-jose.decode JWT
    API->>DB: SELECT user WHERE id = ?
    API-->>SPA: 200 { data: [...projects] }

    Note over Browser,Cache: Token refresh flow
    SPA->>API: POST /api/v1/auth/refresh  Cookie: refresh_token
    API->>Cache: GET rt:{user_id}:{jti}
    Cache-->>API: "valid"
    API->>API: Rotate: delete old, issue new pair
    API-->>SPA: 200 { access_token } + new refresh cookie
```

---

## Diagram 4 — Ticket Creation Flow (Sequence)

```mermaid
sequenceDiagram
    participant Browser
    participant SPA as React SPA
    participant API as FastAPI API
    participant DB as PostgreSQL
    participant Cache as Redis
    participant WS as python-socketio

    Browser->>SPA: Open "Create Ticket" modal
    SPA->>API: GET /api/v1/projects/{id}/members  (populate assignee dropdown)
    API-->>SPA: 200 { data: [...members] }

    Browser->>SPA: Fill form + submit
    SPA->>API: POST /api/v1/projects/{id}/tickets\n{ title, description, priority, sprint_id, assignee_id }

    API->>API: Pydantic v2 validates CreateTicketRequest
    API->>API: Depends(require_project_role(MEMBER, ADMIN, OWNER))

    API->>DB: SELECT COUNT(*) FROM tickets WHERE project_id = ? (for ticket_number)
    DB-->>API: count

    API->>DB: INSERT INTO tickets VALUES (...)
    DB-->>API: Ticket row (id, ticket_number)

    API->>Cache: DEL board:{sprint_id}  (invalidate board cache)

    API->>DB: INSERT INTO ticket_history (action=created)
    DB-->>API: OK

    API-->>SPA: 201 TicketResponse

    API->>WS: sio.emit("ticket:updated", {ticket_id, ...}, room="board:{sprint_id}")

    SPA->>SPA: React Query invalidateQueries(["projects", id, "tickets"])
    SPA-->>Browser: Close modal, show new ticket on board
```

---

## Diagram 5 — Sprint Board Drag-and-Drop (Sequence)

```mermaid
sequenceDiagram
    participant User
    participant SPA as React SPA
    participant API as FastAPI API (FastAPI)
    participant DB as PostgreSQL
    participant Cache as Redis
    participant OtherSPA as Other Browser

    User->>SPA: Drag ticket from "In Progress" → "In Review"

    SPA->>SPA: Optimistic UI update (move card immediately)

    SPA->>API: POST /api/v1/tickets/{id}/transition\n{ status: "in_review" }

    API->>API: Depends(get_current_user) check JWT
    API->>API: validate_transition(IN_PROGRESS → IN_REVIEW)  [workflow rules]
    API->>DB: UPDATE tickets SET status = 'in_review', updated_at = now() WHERE id = ?
    DB-->>API: OK

    API->>DB: INSERT INTO ticket_history (field=status, old=in_progress, new=in_review)
    DB-->>API: OK

    API->>Cache: DEL board:{sprint_id}

    API->>API: sio.emit("ticket:moved", room="board:{sprint_id}", namespace="/board")
    API-->>SPA: 200 TicketResponse

    Note over SPA,OtherSPA: Real-time broadcast
    API->>OtherSPA: WebSocket event: ticket:moved { ticket_id, from: "in_progress", to: "in_review" }
    OtherSPA->>OtherSPA: React Query: update board cache
    OtherSPA->>OtherSPA: Card moves on their board in real time

    alt API returns error (invalid transition)
        API-->>SPA: 409 Conflict
        SPA->>SPA: Rollback optimistic update (restore card position)
        SPA-->>User: Show toast error
    end
```

---

## Diagram 6 — Sprint Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> Planning : POST /projects/{id}/sprints

    Planning --> Active : POST /sprints/{id}/start\n[constraint: no other active sprint]

    Active --> Completed : POST /sprints/{id}/complete\n[all DONE or moved to backlog]

    Active --> Active : Ticket add/remove\nTicket status changes\nSprint goal update

    Completed --> [*]

    note right of Planning
        Fields editable:
        name, goal, dates
        SQLAlchemy: SprintStatus.PLANNING
    end note

    note right of Active
        Board view enabled
        python-socketio broadcasts ticket events
        Redis key: project:{id}:active_sprint
        Unique index: one ACTIVE per project
    end note

    note right of Completed
        Read-only (archive)
        Incomplete tickets
        returned to backlog
        (Sprint.complete() service)
    end note
```

---

## Diagram 7 — Entity Relationship Diagram

```mermaid
erDiagram
    USERS {
        uuid id PK
        string email UK
        string username UK
        string full_name
        string password_hash
        enum role
        boolean is_active
        string avatar_url
        timestamp last_login_at
        timestamp created_at
        timestamp updated_at
    }

    PROJECTS {
        uuid id PK
        string name
        string key UK
        text description
        boolean is_active
        uuid owner_id FK
        timestamp created_at
        timestamp updated_at
    }

    PROJECT_MEMBERS {
        uuid id PK
        uuid project_id FK
        uuid user_id FK
        enum role
        timestamp created_at
    }

    TICKETS {
        uuid id PK
        integer ticket_number
        uuid project_id FK
        uuid sprint_id FK
        uuid assignee_id FK
        uuid reporter_id FK
        string title
        text description
        enum status
        enum priority
        enum ticket_type
        integer story_points
        integer order_index
        tsvector search_vector
        boolean is_deleted
        timestamp created_at
        timestamp updated_at
    }

    TICKET_HISTORY {
        uuid id PK
        uuid ticket_id FK
        uuid actor_id FK
        string action
        string field_name
        json old_value
        json new_value
        timestamp created_at
    }

    SPRINTS {
        uuid id PK
        uuid project_id FK
        string name
        text goal
        enum status
        date start_date
        date end_date
        timestamp created_at
        timestamp updated_at
    }

    COMMENTS {
        uuid id PK
        uuid ticket_id FK
        uuid author_id FK
        text body
        boolean is_edited
        timestamp created_at
        timestamp updated_at
    }

    LABELS {
        uuid id PK
        uuid project_id FK
        string name
        string color
        timestamp created_at
    }

    TICKET_LABELS {
        uuid ticket_id FK
        uuid label_id FK
    }

    NOTIFICATIONS {
        uuid id PK
        uuid recipient_id FK
        string type
        json payload
        boolean is_read
        timestamp created_at
    }

    USERS            ||--o{ PROJECT_MEMBERS  : "has membership"
    PROJECTS         ||--o{ PROJECT_MEMBERS  : "has members"
    PROJECTS         ||--o{ TICKETS          : "contains"
    PROJECTS         ||--o{ SPRINTS          : "has"
    PROJECTS         ||--o{ LABELS           : "has"
    SPRINTS          ||--o{ TICKETS          : "contains"
    USERS            ||--o{ TICKETS          : "assigned to"
    USERS            ||--o{ TICKETS          : "reported by"
    TICKETS          ||--o{ COMMENTS         : "has"
    TICKETS          ||--o{ TICKET_HISTORY   : "has history"
    TICKETS          }o--o{ LABELS           : "labeled with"
    USERS            ||--o{ NOTIFICATIONS    : "receives"
```

---

## Diagram 8 — Frontend Application Flow

```mermaid
flowchart TD
    A([User visits app]) --> B{Has access_token\nin Redux?}

    B -->|No| C[Redirect to /login]
    B -->|Yes| D[Verify token exp time]
    D -->|Expired| E[POST /auth/refresh via cookie]
    D -->|Valid| F[Load Dashboard]

    C --> G[Enter credentials]
    G --> H[POST /api/v1/auth/login]
    H -->|401| I[Show error message]
    I --> G
    H -->|200| J[Store access_token in Redux]
    J --> F

    E -->|Success: new token| F
    E -->|Failure: no cookie| C

    F --> K[Load projects list\nGET /api/v1/projects]
    K --> L[Select project]
    L --> M{View?}

    M -->|Backlog| N[GET /projects/{id}/tickets\nstatus=backlog]
    M -->|Board| O[GET /sprints/{id}/board]
    M -->|Sprints| P[GET /projects/{id}/sprints]

    O --> Q[Render Kanban columns\nTodo | In Progress | In Review | Done]
    Q --> R[Connect Socket.IO to\n/board room:{sprint_id}]
    R --> S{WebSocket event?}
    S -->|ticket:moved| T[Update card position in UI]
    S -->|ticket:updated| U[Update card fields]
    S -->|None| V[User action]
    V -->|Drag card| W[POST /tickets/{id}/transition]
    W -->|200| X[React Query invalidate]
    W -->|409 Conflict| Y[Rollback optimistic update]
```

---

## Diagram 9 — CI/CD Pipeline

```mermaid
flowchart LR
    A([Push to\nmain branch]) --> B[Stage 1\nLint & Format\nruff + mypy\nESLint + tsc]

    B -->|Pass| C[Stage 2\nTest\npoetry run pytest\nnpm run test:coverage]
    B -->|Fail| X1([Block merge\nLint errors])

    C -->|≥70% coverage| D[Stage 3\nBuild & Push\ndocker build python:3.12-slim\npush to ECR\nnpm run build → S3]
    C -->|<70% coverage| X2([Block merge\nCoverage gate])

    D --> E[Stage 4\nDeploy\nalembic upgrade head\necs update-service\nhealth check /health]

    E -->|Healthy| F([Deploy\nComplete ✅])
    E -->|Unhealthy| G[Auto rollback\nredeploy previous\nECS task def]
    G --> H([Alert PagerDuty\nSlack notification])

    style A fill:#4CAF50,color:#fff
    style F fill:#4CAF50,color:#fff
    style X1 fill:#f44336,color:#fff
    style X2 fill:#f44336,color:#fff
    style H fill:#FF9800,color:#fff
```

---

## Diagram 10 — RBAC Permission Flow

```mermaid
flowchart TD
    A([Incoming\nHTTP Request]) --> B[Middleware:\nCorrelationID + CORS + RateLimit]

    B --> C{Bearer token\npresent?}
    C -->|No| D([401 Unauthorized])
    C -->|Yes| E[Depends\nget_current_user\npython-jose decode JWT]

    E -->|Invalid / expired| F([401 Unauthorized])
    E -->|Valid| G{Route requires\nproject role?}

    G -->|No - public route| H[Execute handler]
    G -->|Yes| I[Depends\nrequire_project_role\nfetch ProjectMember row]

    I -->|User not in project| J([403 Forbidden])
    I -->|Role insufficient| K([403 Forbidden])
    I -->|Role allowed| L[Execute handler]

    H --> M[Pydantic v2 validates\nrequest body]
    L --> M

    M -->|Invalid| N([422 Unprocessable Entity])
    M -->|Valid| O[Service layer\nBusiness logic]

    O -->|NotFoundException| P([404 Not Found])
    O -->|ConflictException| Q([409 Conflict])
    O -->|Success| R([2xx Response\nPydantic v2 serialized])

    style D fill:#f44336,color:#fff
    style F fill:#f44336,color:#fff
    style J fill:#f44336,color:#fff
    style K fill:#f44336,color:#fff
    style N fill:#FF9800,color:#fff
    style P fill:#f44336,color:#fff
    style Q fill:#FF9800,color:#fff
    style R fill:#4CAF50,color:#fff
```

---

## Diagram 11 — Database Migration & Seeding Flow

```mermaid
flowchart TD
    A([Deploy triggered\nGitHub Actions]) --> B[ECS: run migration task\npoetry run alembic current]

    B --> C{Pending\nmigrations?}
    C -->|None| D[Skip migration step]
    C -->|Yes| E[alembic upgrade head]

    E -->|Success| F[Log: migration applied]
    E -->|Error| G([Fail deployment\nAlert team])

    F --> H{Is first\ndeploy?}
    H -->|Yes| I[Run seed script:\ncreate admin user\ncreate demo project]
    H -->|No| J[Skip seed step]

    D --> K[ECS: rolling deploy\nnew FastAPI tasks]
    I --> K
    J --> K

    K --> L[ECS: health check\nGET /health → 200]
    L -->|Healthy| M([Deployment Complete ✅])
    L -->|Unhealthy| N[ECS: rollback\nprevious task definition]
    N --> O([Alert PagerDuty])

    style G fill:#f44336,color:#fff
    style O fill:#f44336,color:#fff
    style M fill:#4CAF50,color:#fff
```

---

## Diagram 12 — Phase 1 Sprint Timeline (Gantt)

```mermaid
gantt
    title Phase 1 MVP — 10 Week Sprint Plan
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d

    section Infrastructure
    AWS Setup + ECS + RDS + Redis          :done,    infra1, 2026-03-01, 5d
    Dockerfile (python:3.12-slim) + ECR    :done,    infra2, after infra1, 3d
    GitHub Actions CI/CD (pytest + poetry) :done,    infra3, after infra2, 3d
    FastAPI scaffold + Alembic init        :done,    infra4, 2026-03-01, 5d

    section Backend Core
    SQLAlchemy models + Alembic migrations :done,    be1, 2026-03-06, 5d
    Auth (python-jose, passlib, Redis RT)  :done,    be2, after be1, 5d
    User & Project APIs (FastAPI routers)  :done,    be3, after be2, 5d
    Ticket CRUD + Workflow rules           :active,  be4, after be3, 7d
    Sprint CRUD + Board endpoint           :         be5, after be4, 5d
    Search (PostgreSQL tsvector)           :         be6, after be5, 3d
    python-socketio real-time events       :         be7, after be3, 7d

    section Frontend
    React + Vite project scaffold          :done,    fe1, 2026-03-01, 3d
    Auth pages + Redux auth slice          :done,    fe2, after fe1, 5d
    Project + Backlog pages                :done,    fe3, after fe2, 5d
    Sprint Board (Kanban drag-and-drop)    :active,  fe4, after fe3, 7d
    Socket.IO integration                  :         fe5, after be7, 5d
    Search & Filter UI                     :         fe6, after fe4, 4d

    section Testing & QA
    Backend: pytest (unit + integration)   :         qa1, 2026-04-01, 7d
    Frontend: Vitest + React Testing Lib   :         qa2, 2026-04-01, 7d
    E2E: Playwright critical flows         :         qa3, after qa1, 5d
    Performance baseline                   :         qa4, after qa3, 3d

    section Phase 1 Milestone
    MVP Ready for Review                   :milestone, m1, 2026-04-20, 0d
```
