# High-Level Design (HLD)
## Jira-Like Project Management Application

**Version**: 1.0  
**Date**: February 21, 2026  
**Author**: Architecture Team  
**Status**: Approved

---

## 1. Introduction

### 1.1 Purpose
This document describes the high-level design of the Jira-Like Project Management Application. It serves as the authoritative architectural blueprint for the engineering team, establishing system boundaries, major components, and interaction patterns across all four delivery phases.

### 1.2 Scope
The system enables teams to create and manage projects, plan and execute sprints, track tickets through a configurable workflow, collaborate via comments, and gain insight through analytics and reporting.

### 1.3 Design Principles
| Principle | Rationale |
|-----------|-----------|
| **Separation of Concerns** | Frontend, backend, and data layers are decoupled and independently deployable |
| **API-First** | All functionality exposed via versioned REST APIs; UI is just one consumer |
| **Security by Default** | Authentication, authorization, and data protection baked in at every layer |
| **Progressive Delivery** | Phased rollout: MVP → Enhanced → Analytics → Advanced |
| **Horizontal Scalability** | Stateless services that scale out under load |
| **Observability** | Logs, metrics, and traces captured from day one |

---

## 2. System Context

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL WORLD                                │
│                                                                         │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                 │
│   │  Developer  │   │   Product   │   │  Scrum      │                 │
│   │  (Browser)  │   │   Manager   │   │  Master     │                 │
│   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘                 │
│          │                 │                  │                         │
│          └─────────────────┴──────────────────┘                        │
│                            │ HTTPS                                      │
└────────────────────────────┼────────────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Load Balancer  │
                    │   (AWS ALB)     │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼────┐  ┌──────▼─────┐  ┌───▼──────────┐
     │  React SPA  │  │  REST API  │  │  WebSocket   │
     │  (CloudFront│  │  (NestJS)  │  │  Gateway     │
     │  + S3)      │  │            │  │              │
     └─────────────┘  └──────┬─────┘  └──────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼────┐  ┌──────▼───┐  ┌──────▼────────┐
     │ PostgreSQL  │  │  Redis   │  │  AWS S3       │
     │  (RDS)      │  │  (Cache) │  │  (Files)      │
     └─────────────┘  └──────────┘  └───────────────┘
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
| Real-time | Socket.IO Client |
| Hosting | AWS CloudFront + S3 |

**Responsibilities**:
- Render all user-facing interfaces
- Manage client-side state (auth tokens, UI preferences)
- Communicate with backend exclusively via REST and WebSocket
- Handle optimistic UI updates for drag-and-drop operations

### 3.2 Backend API (NestJS Monolith → Modular)
| Attribute | Value |
|-----------|-------|
| Technology | Node.js 20 LTS + NestJS + TypeScript |
| ORM | Prisma |
| Authentication | JWT (Access Token 15min + Refresh Token 7d) |
| Documentation | OpenAPI / Swagger |
| Hosting | AWS ECS Fargate |

**Modules** (NestJS feature modules):
```
src/
├── auth/           → Registration, login, JWT, refresh
├── users/          → Profile, preferences, RBAC
├── projects/       → Project CRUD, members, settings
├── tickets/        → Ticket CRUD, transitions, labels
├── sprints/        → Sprint lifecycle, board, planning
├── comments/       → Comment CRUD, @mentions
├── notifications/  → In-app + email notifications
├── search/         → Full-text search, filters
├── reports/        → Burndown, velocity, analytics
└── realtime/       → WebSocket gateway (Socket.IO)
```

### 3.3 Primary Database (PostgreSQL)
| Attribute | Value |
|-----------|-------|
| Technology | PostgreSQL 15 |
| Hosting | AWS RDS (Multi-AZ for production) |
| Schema Management | Prisma Migrations |
| Backup | Automated daily snapshots, 30-day retention |

**Core Schemas**: `users`, `projects`, `project_members`, `tickets`, `ticket_history`, `sprints`, `comments`, `labels`, `notifications`

### 3.4 Cache Layer (Redis)
| Attribute | Value |
|-----------|-------|
| Technology | Redis 7 |
| Hosting | AWS ElastiCache |
| TTL Strategy | Short (5min) for board data; Long (1hr) for user sessions |

**Cached Resources**:
- User sessions and JWT refresh token storage
- Sprint board state (heavily-read, infrequently-written)
- Active sprint metadata per project
- Rate-limiting counters

### 3.5 File Storage (AWS S3)
- Ticket attachments stored in versioned S3 buckets
- Pre-signed URL generation for secure time-limited access
- Maximum file size: 25 MB per attachment
- Supported types: images, PDFs, documents, archives

### 3.6 Email Service (AWS SES)
- Transactional email delivery (registration, password reset, notifications)
- Phase 2+ feature; stubbed in Phase 1

### 3.7 Real-time Gateway (Socket.IO)
- WebSocket connections for live board updates
- Ticket status changes broadcast to all board viewers
- Comment additions streamed in real-time
- Presence indicators (who is viewing a ticket)

---

## 4. Delivery Phases

### Phase 1 — MVP (Weeks 1–10)
**Goal**: A functional, deployable product that a team can use to manage work.

| Feature Area | Scope |
|---|---|
| Authentication | Registration, login, JWT, RBAC (4 roles) |
| Project Management | Create, configure, invite members |
| Ticket Management | Full CRUD, status transitions, assignment, labels |
| Sprint Management | Create, start, complete; sprint board (Kanban) |
| Backlog | Prioritized list, drag to reorder |
| Search & Filter | Basic search by ID/keyword; filter by status/assignee/priority |

### Phase 2 — Enhanced (Weeks 11–18)
| Feature Area | Scope |
|---|---|
| Collaboration | Comments, @mentions, watchers |
| Relationships | Ticket linking, dependencies |
| Bulk Operations | Bulk status, assignment, sprint move |
| Activity Log | Full audit trail per ticket |
| Email Notifications | Assignment, mentions, sprint events |
| File Attachments | Upload and view on ticket detail |

### Phase 3 — Analytics (Weeks 19–24)
| Feature Area | Scope |
|---|---|
| Sprint Reports | Burndown chart, velocity chart |
| Project Dashboard | Cumulative flow, ticket age, created vs. resolved |
| User Reports | Individual velocity, workload distribution |
| Performance | Query optimization, CDN caching, lazy loading |

### Phase 4 — Advanced (Future)
| Feature Area | Scope |
|---|---|
| Real-time Collaboration | Live cursor, simultaneous editing |
| Workflow Automation | Triggers and actions (e.g., auto-assign on creation) |
| Integrations | GitHub, Slack, Webhook |
| Custom Fields | Admin-defined field types per project |
| Advanced Analytics | Custom JQL-like query language |

---

## 5. Data Flow Overview

### 5.1 Typical Read Flow
```
Browser → CloudFront → ALB → ECS (NestJS) → Redis Cache Hit → Response
                                           ↓ Cache Miss
                                       PostgreSQL → Response + Cache Write
```

### 5.2 Typical Write Flow
```
Browser → ALB → ECS (NestJS) → PostgreSQL (Write)
                             → Redis (Invalidate Cache)
                             → Socket.IO Gateway (Broadcast Event)
                             → SES (Trigger Email if needed)
```

### 5.3 Authentication Flow
```
Login Request → Auth Module → bcrypt verify → JWT sign (Access + Refresh)
                           → Store Refresh in Redis
                           → Return tokens to client

Subsequent Requests → JWT Guard → Decode Access Token → Attach user to request
Token Expired → Refresh endpoint → Validate Refresh from Redis → New pair issued
```

---

## 6. Cross-Cutting Concerns

### 6.1 Security
- All endpoints protected by JWT Guard except `/auth/register`, `/auth/login`
- RBAC enforced per resource and per operation (Guard + Decorator pattern)
- Passwords hashed with bcrypt (cost factor 12)
- Input validation via `class-validator` on all DTOs
- Rate limiting: 100 req/min per IP (general), 10 req/min (auth endpoints)
- CORS restricted to allowed origins only
- SQL injection prevented by Prisma parameterized queries

### 6.2 Error Handling
- Global exception filter returns RFC 7807 Problem Detail format
- HTTP 4xx errors logged at WARN; 5xx errors logged at ERROR with stack trace
- Frontend displays user-friendly messages mapped from error codes

### 6.3 Logging & Observability
- Structured JSON logs (Winston + correlation ID per request)
- Metrics collected by AWS CloudWatch
- Distributed traces via AWS X-Ray
- Alerts on error rate > 1% and P95 latency > 500ms

### 6.4 API Versioning
- URL-based versioning: `/api/v1/...`
- Deprecation headers added for sunset versions

---

## 7. Technology Stack Summary

| Layer | Technology | Version |
|---|---|---|
| Frontend Framework | React | 18 |
| Frontend Language | TypeScript | 5.x |
| Frontend Build | Vite | 5.x |
| Frontend State | Redux Toolkit + React Query | Latest |
| Frontend UI | TailwindCSS + shadcn/ui | Latest |
| Backend Runtime | Node.js | 20 LTS |
| Backend Framework | NestJS | 10.x |
| Backend Language | TypeScript | 5.x |
| ORM | Prisma | 5.x |
| Primary Database | PostgreSQL | 15 |
| Cache | Redis | 7 |
| Real-time | Socket.IO | 4.x |
| File Storage | AWS S3 | - |
| Email | AWS SES | - |
| Container | Docker | Latest |
| Orchestration | AWS ECS Fargate | - |
| CI/CD | GitHub Actions | - |

---

## 8. Assumptions and Constraints

| Item | Detail |
|---|---|
| Users | Up to 1,000 concurrent users initially; 10,000 target by Phase 3 |
| Data Volume | Up to 100 projects, 10,000+ tickets at MVP |
| Browser Support | Chrome, Firefox, Safari, Edge (latest 2 versions) |
| Mobile | Responsive web; no native app in Phase 1–3 |
| Availability | 99.9% SLA (≤8.7 hours downtime/year) |
| RTO | 1 hour |
| RPO | 24 hours (daily backup) |
| Compliance | No PII regulations beyond standard data protection in Phase 1 |
