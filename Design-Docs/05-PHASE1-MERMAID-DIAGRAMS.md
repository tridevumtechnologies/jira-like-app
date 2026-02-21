# Phase 1 — Mermaid Diagrams
## Jira-Like Project Management Application

**Version**: 1.0  
**Date**: February 21, 2026  
**Author**: Architecture Team  
**Scope**: Sprint 0 → Sprint 4 (MVP)

---

## Diagram 1 — System Architecture (C4 Context)

```mermaid
C4Context
    title System Context — Jira-Like App (Phase 1)

    Person(developer, "Developer", "Creates and updates tickets, views sprint board")
    Person(pm, "Product Manager", "Creates projects, plans sprints, reviews reports")
    Person(scrumMaster, "Scrum Master", "Starts/completes sprints, assigns tickets")
    Person(viewer, "Viewer/Stakeholder", "Read-only access to projects and tickets")

    System(app, "Jira-Like App", "React SPA + NestJS API — project & sprint management")

    System_Ext(ses, "AWS SES", "Transactional email delivery")
    System_Ext(s3, "AWS S3", "File attachment storage")

    Rel(developer, app, "Manages tickets, views board", "HTTPS")
    Rel(pm, app, "Plans sprints, creates projects", "HTTPS")
    Rel(scrumMaster, app, "Runs sprint ceremony", "HTTPS")
    Rel(viewer, app, "Views progress", "HTTPS")
    Rel(app, ses, "Sends notifications", "SMTP/API")
    Rel(app, s3, "Stores/retrieves files", "HTTPS")
```

---

## Diagram 2 — MARN Stack Container Diagram

```mermaid
C4Container
    title Container Diagram — Phase 1 Infrastructure

    Person(user, "User", "Any authenticated team member")

    Container_Boundary(aws, "AWS Cloud") {
        Container(cf, "CloudFront + S3", "CDN", "Serves React SPA static assets")
        Container(alb, "Application Load Balancer", "AWS ALB", "Routes HTTPS traffic to API tasks")
        Container(api, "API Service", "NestJS/Node.js on ECS Fargate", "All business logic, REST endpoints, WebSocket gateway")
        ContainerDb(pg, "PostgreSQL 15", "AWS RDS Multi-AZ", "Primary relational datastore")
        ContainerDb(redis, "Redis 7", "AWS ElastiCache", "Session cache, board state, rate limits")
        ContainerDb(s3, "S3 Bucket", "AWS S3", "Attachments and avatar images")
    }

    Rel(user, cf, "Loads SPA", "HTTPS")
    Rel(user, alb, "API/WebSocket calls", "HTTPS/WSS")
    Rel(alb, api, "Forwards requests", "HTTP/WS")
    Rel(api, pg, "Reads/Writes", "TCP 5432 (Prisma)")
    Rel(api, redis, "Cache + Sessions", "TCP 6379")
    Rel(api, s3, "Stores files", "HTTPS SDK")
    Rel(cf, s3, "Origin pull", "HTTPS")
```

---

## Diagram 3 — Authentication Flow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Browser
    participant API as NestJS API
    participant DB as PostgreSQL
    participant Cache as Redis

    User->>Browser: Enter email + password
    Browser->>API: POST /api/v1/auth/login
    API->>DB: SELECT user WHERE email = ?
    DB-->>API: User record
    API->>API: bcrypt.compare(password, hash)
    
    alt Invalid credentials
        API-->>Browser: 401 Unauthorized
    else Valid credentials
        API->>API: Sign Access Token (JWT, 15min)
        API->>API: Generate Refresh Token (UUID)
        API->>Cache: SET rt:{userId}:{jti} = "valid" TTL 7d
        API-->>Browser: { accessToken } + Set-Cookie: refreshToken (HttpOnly)
        Browser->>Browser: Store accessToken in memory
        Browser-->>User: Redirect to Dashboard
    end

    Note over Browser,API: Later — access token expires
    Browser->>API: POST /api/v1/auth/refresh (cookie sent automatically)
    API->>Cache: GET rt:{userId}:{jti}
    
    alt Token not in Redis
        API-->>Browser: 401 — token revoked
    else Token valid
        API->>Cache: DELETE old refresh token
        API->>API: Sign new Access Token
        API->>API: Generate new Refresh Token
        API->>Cache: SET new refresh token
        API-->>Browser: { accessToken } + new refreshToken cookie
    end
```

---

## Diagram 4 — Ticket Creation Flow

```mermaid
sequenceDiagram
    autonumber
    actor TeamMember
    participant UI as React UI
    participant API as NestJS API
    participant DB as PostgreSQL
    participant Cache as Redis
    participant WS as Socket.IO Gateway

    TeamMember->>UI: Clicks "Create Ticket"
    UI->>UI: Open CreateTicketModal
    TeamMember->>UI: Fills form (title, type, priority, assignee...)
    UI->>UI: class-validator client-side check
    UI->>API: POST /api/v1/projects/:id/tickets (Bearer token)
    
    API->>API: JwtAuthGuard validates token
    API->>API: ProjectMemberGuard checks membership
    API->>DB: SELECT project WHERE id = ?
    DB-->>API: Project (key = "PROJ")
    
    API->>DB: SELECT nextval('ticket_seq_PROJ')
    DB-->>API: 42
    
    API->>DB: BEGIN TRANSACTION
    API->>DB: INSERT ticket { key: "PROJ-42", ... }
    DB-->>API: Created ticket
    API->>DB: INSERT ticket_history { field: "created" }
    API->>DB: COMMIT
    
    API->>Cache: DEL board:{sprintId} (if assigned to sprint)
    
    API->>WS: emit("ticket:created", { ticket }) to board room
    WS-->>UI: Real-time update (other board viewers)
    
    API-->>UI: 201 { data: ticket }
    UI->>UI: React Query invalidate ["projects", id, "tickets"]
    UI-->>TeamMember: Navigate to PROJ-42 detail page
```

---

## Diagram 5 — Sprint Board Kanban Flow (Drag & Drop)

```mermaid
sequenceDiagram
    autonumber
    actor Dev
    participant UI as React Board UI
    participant DnD as react-dnd
    participant Query as React Query
    participant API as NestJS API
    participant DB as PostgreSQL
    participant Cache as Redis
    participant WS as Socket.IO

    Dev->>UI: Opens Sprint Board (sprintId=X)
    UI->>WS: board:join { sprintId: "X" }
    UI->>API: GET /api/v1/sprints/X/board
    
    API->>Cache: GET board:X
    alt Cache Hit
        Cache-->>API: Cached board JSON
    else Cache Miss
        API->>DB: SELECT tickets WHERE sprint_id=X ORDER BY board_order
        DB-->>API: All columns with tickets
        API->>Cache: SET board:X TTL 5min
    end
    
    API-->>UI: { TODO: [...], IN_PROGRESS: [...], IN_REVIEW: [...], DONE: [...] }
    UI-->>Dev: Renders Kanban board

    Dev->>UI: Drags PROJ-42 from IN_PROGRESS → IN_REVIEW
    UI->>DnD: onDragEnd callback
    UI->>UI: Optimistic update: move card locally
    
    UI->>API: POST /api/v1/tickets/PROJ-42/transition { status: "IN_REVIEW" }
    API->>API: Validate transition: IN_PROGRESS → IN_REVIEW ✅
    API->>DB: UPDATE tickets SET status='IN_REVIEW' WHERE key='PROJ-42'
    API->>DB: INSERT ticket_history { field: "status", old: "IN_PROGRESS", new: "IN_REVIEW" }
    
    API->>Cache: DEL board:X
    API->>WS: emit("ticket:moved", { ticketId, fromStatus, toStatus, movedBy })
    WS-->>UI: Broadcast to all board:X room members
    
    API-->>UI: 200 { data: updatedTicket }
    
    alt Other user on same board
        WS->>UI: ticket:moved event received
        UI->>Query: invalidate ["sprints","X","board"]
        UI-->>Dev: Board refreshes for other viewers
    end
```

---

## Diagram 6 — Sprint Lifecycle State Machine

```mermaid
stateDiagram-v2
    direction LR

    [*] --> DRAFT : Create Sprint\n(POST /sprints)

    DRAFT --> ACTIVE : Start Sprint\n(POST /sprints/:id/start)\n[no other active sprint]

    DRAFT --> [*] : Delete Sprint\n(DELETE /sprints/:id)\n[no tickets assigned]

    ACTIVE --> COMPLETION_REVIEW : Complete Sprint\n(POST /sprints/:id/complete)

    COMPLETION_REVIEW --> COMPLETED : User resolves\nincomplete tickets\n(move to backlog or next sprint)

    COMPLETED --> [*] : Sprint archived\n(read-only)

    note right of ACTIVE
        Sprint Board accessible
        Drag-and-drop enabled
        Real-time via Socket.IO
    end note

    note right of COMPLETION_REVIEW
        System shows incomplete tickets
        User chooses: backlog | next sprint
        Transaction applied atomically
    end note
```

---

## Diagram 7 — Entity Relationship Diagram (Phase 1 Core)

```mermaid
erDiagram
    USERS {
        uuid id PK
        string email UK
        string password_hash
        string first_name
        string last_name
        string avatar_url
        enum role
        boolean is_verified
        boolean is_active
        timestamp created_at
    }

    PROJECTS {
        uuid id PK
        string key UK
        string name
        string description
        boolean is_public
        boolean is_archived
        timestamp created_at
    }

    PROJECT_MEMBERS {
        uuid id PK
        uuid project_id FK
        uuid user_id FK
        enum role
        timestamp joined_at
    }

    SPRINTS {
        uuid id PK
        uuid project_id FK
        string name
        string goal
        enum status
        timestamp start_date
        timestamp end_date
        timestamp completed_at
    }

    TICKETS {
        uuid id PK
        string key UK
        uuid project_id FK
        uuid sprint_id FK
        uuid parent_id FK
        string title
        text description
        enum type
        enum status
        enum priority
        int story_points
        uuid assignee_id FK
        uuid reporter_id FK
        int backlog_order
        int board_order
        boolean is_deleted
        timestamp created_at
    }

    COMMENTS {
        uuid id PK
        uuid ticket_id FK
        uuid author_id FK
        text content
        boolean is_deleted
        timestamp created_at
    }

    TICKET_HISTORY {
        uuid id PK
        uuid ticket_id FK
        uuid user_id FK
        string field
        string old_value
        string new_value
        timestamp changed_at
    }

    LABELS {
        uuid id PK
        uuid project_id FK
        string name
        string color
    }

    TICKET_LABELS {
        uuid ticket_id FK
        uuid label_id FK
    }

    NOTIFICATIONS {
        uuid id PK
        uuid user_id FK
        enum type
        string title
        string body
        uuid resource_id
        boolean is_read
        timestamp created_at
    }

    USERS ||--o{ PROJECT_MEMBERS : "is member of"
    PROJECTS ||--o{ PROJECT_MEMBERS : "has"
    PROJECTS ||--o{ SPRINTS : "has"
    PROJECTS ||--o{ TICKETS : "contains"
    PROJECTS ||--o{ LABELS : "defines"
    SPRINTS ||--o{ TICKETS : "contains"
    USERS ||--o{ TICKETS : "assigned to"
    USERS ||--o{ TICKETS : "reported by"
    TICKETS ||--o{ TICKETS : "subtask of"
    TICKETS ||--o{ COMMENTS : "has"
    TICKETS ||--o{ TICKET_HISTORY : "has"
    TICKETS ||--o{ TICKET_LABELS : "tagged with"
    LABELS ||--o{ TICKET_LABELS : "applied to"
    USERS ||--o{ NOTIFICATIONS : "receives"
```

---

## Diagram 8 — Frontend Application Flow (User Journey)

```mermaid
flowchart TD
    A([User opens app]) --> B{Authenticated?}
    B -- No --> C[Login Page]
    C --> D{Login success?}
    D -- No --> C
    D -- Yes --> E[Dashboard / Projects List]
    B -- Yes --> E

    E --> F{Choose action}
    F --> G[Create Project]
    F --> H[Open Existing Project]

    G --> I[Project created] --> H

    H --> J{Project Section}
    J --> K[Backlog]
    J --> L[Sprint Board]
    J --> M[Sprint Planning]
    J --> N[Project Settings]

    K --> K1[View all unplanned tickets]
    K1 --> K2{Action}
    K2 --> K3[Create new ticket]
    K2 --> K4[Drag to reorder]
    K2 --> K5[Move ticket to sprint]
    K2 --> K6[Click ticket → Ticket Detail]

    L --> L1[View active sprint columns]
    L1 --> L2{Action}
    L2 --> L3[Drag ticket between columns]
    L2 --> L4[Filter by assignee/priority]
    L2 --> L5[Complete Sprint]
    L2 --> L6[Click ticket → Ticket Detail]

    M --> M1[Drag backlog tickets into sprint]
    M1 --> M2[View sprint capacity]
    M2 --> M3[Start Sprint]

    K6 --> O[Ticket Detail Page]
    L6 --> O
    O --> P{Ticket Actions}
    P --> P1[Edit fields inline]
    P --> P2[Change status]
    P --> P3[Assign/reassign]
    P --> P4[Add to sprint]
    P --> P5[Add labels]

    N --> N1[Manage members]
    N --> N2[Configure project settings]
```

---

## Diagram 9 — CI/CD Pipeline

```mermaid
flowchart LR
    A[Developer pushes code] --> B[GitHub Actions triggered]

    subgraph CI["CI — Quality Gates"]
        B --> C[Lint & Format Check\nESLint + Prettier]
        C --> D[Unit Tests\nJest coverage ≥ 70%]
        D --> E[Integration Tests\ntestcontainers: Postgres + Redis]
        E --> F[Docker Build\nmulti-stage minimal image]
        F --> G[ECR Image Scan\nblock on CRITICAL CVE]
    end

    subgraph CD_Staging["CD — Staging Deploy"]
        G --> H{Branch?}
        H -- develop --> I[Push image to ECR\ntag: staging-SHA]
        I --> J[ECS Deploy to Staging\nrolling update 1 task]
        J --> K[Smoke Tests\n5 key Playwright flows]
    end

    subgraph CD_Prod["CD — Production Deploy"]
        H -- main --> L[Manual Approval Gate\nRequired reviewer sign-off]
        L --> M[Push image to ECR\ntag: v1.x.x-SHA]
        M --> N[ECS Deploy to Production\nrolling update min 1 healthy]
        N --> O[Post-deploy Smoke Tests]
        O --> P{Error rate spike?}
        P -- Yes --> Q[Auto-rollback to previous task def]
        P -- No --> R[Deploy complete ✅]
    end
```

---

## Diagram 10 — RBAC Permission Flow

```mermaid
flowchart TD
    A[Incoming API Request] --> B[JwtAuthGuard\nDecode & validate JWT]
    B --> C{Token valid?}
    C -- No --> Z1[401 Unauthorized]
    C -- Yes --> D[Attach user to request context]

    D --> E{System Role check\nrequired?}
    E -- ADMIN only route --> F{user.role === ADMIN?}
    F -- No --> Z2[403 Forbidden]
    F -- Yes --> K[Execute Handler]

    E -- Project route --> G[ProjectMemberGuard\nQuery: project_members table]
    G --> H{User is member?}
    H -- No --> Z3[403 Not a member]
    H -- Yes --> I[Attach projectRole to context]

    I --> J[RolesGuard\nCheck decorator-defined minimum role]
    J --> L{projectRole ≥ required?}
    L -- No --> Z4[403 Insufficient role]
    L -- Yes --> K

    K --> M[Controller Handler runs]
    M --> N[Response returned]

    style Z1 fill:#ef4444,color:#fff
    style Z2 fill:#ef4444,color:#fff
    style Z3 fill:#ef4444,color:#fff
    style Z4 fill:#ef4444,color:#fff
    style K fill:#22c55e,color:#fff
    style N fill:#22c55e,color:#fff
```

---

## Diagram 11 — Database Migration & Seeding Flow (Sprint 0)

```mermaid
flowchart LR
    A[Developer runs\nnpx prisma migrate dev] --> B[Prisma reads schema.prisma]
    B --> C[Generates SQL migration file\nmigrations/YYYYMMDDHHMMSS_init.sql]
    C --> D[Applies migration to DB]
    D --> E[Prisma generates TypeScript client]
    E --> F[Run seed script\nnpx prisma db seed]
    F --> G[(PostgreSQL DB\nwith sample data)]

    subgraph Seed Data
        G --> H[Admin user\nadmin@example.com]
        G --> I[Sample project\nkey: DEMO]
        G --> J[5 sample tickets\nDEMO-1 to DEMO-5]
        G --> K[1 active sprint\nSprint 1]
    end
```

---

## Diagram 12 — Phase 1 Sprint Delivery Timeline

```mermaid
gantt
    title Phase 1 — MVP Delivery Timeline
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d

    section Sprint 0 (Foundation)
    Project Setup & Tooling        :done,    s0a, 2026-02-21, 3d
    DB Schema & Migrations         :done,    s0b, after s0a, 3d
    CI/CD Pipeline                 :done,    s0c, after s0a, 4d
    Docker Dev Environment         :done,    s0d, after s0b, 2d
    Design System Components       :done,    s0e, 2026-02-21, 7d

    section Sprint 1 (Auth & Projects)
    User Registration & Login      :active,  s1a, 2026-03-07, 4d
    JWT + Refresh Token            :         s1b, after s1a, 2d
    Project CRUD API               :         s1c, after s1a, 5d
    Project Members API            :         s1d, after s1c, 3d
    Auth UI Pages                  :         s1e, 2026-03-07, 5d
    Project Management UI          :         s1f, after s1e, 5d

    section Sprint 2 (Tickets)
    Ticket CRUD API                :         s2a, 2026-03-21, 7d
    Ticket Status Transitions      :         s2b, after s2a, 3d
    Ticket List UI                 :         s2c, 2026-03-21, 5d
    Ticket Detail UI               :         s2d, after s2c, 5d
    Search & Filter UI             :         s2e, after s2d, 3d

    section Sprint 3 (Sprints & Backlog)
    Sprint Lifecycle API           :         s3a, 2026-04-04, 5d
    Backlog API                    :         s3b, after s3a, 3d
    Backlog UI (drag-and-drop)     :         s3c, 2026-04-04, 7d
    Sprint Planning UI             :         s3d, after s3c, 3d

    section Sprint 4 (Board & Polish)
    Sprint Board (Kanban) UI       :         s4a, 2026-04-18, 7d
    Real-time WebSocket            :         s4b, after s4a, 3d
    Comments API                   :         s4c, 2026-04-18, 4d
    E2E Tests & Bug Fixes          :         s4e, 2026-04-25, 5d
    Production Deployment          :         s4f, 2026-04-30, 2d
```
