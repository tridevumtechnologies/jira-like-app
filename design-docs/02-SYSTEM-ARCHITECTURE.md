# System Architecture Document
## Jira-Like Project Management Application

**Version**: 1.0  
**Date**: February 21, 2026  
**Author**: Architecture Team  
**Status**: Approved

---

## 1. Architecture Overview

The system is designed as a **MARN** stack application:

| Letter | Technology | Role |
|--------|------------|------|
| **M** | MongoDB-compatible / **PostgreSQL** (Relational) | Primary data store |
| **A** | **AWS** | Cloud hosting & managed services |
| **R** | **React** | Frontend SPA |
| **N** | **NestJS** (Node.js) | Backend API |

> Note: We use PostgreSQL (not MongoDB) as the relational nature of projects, tickets, sprints, and members benefits from ACID transactions and foreign-key integrity.

---

## 2. Component Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT TIER                                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     React SPA (Browser)                               │  │
│  │                                                                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │  │
│  │  │  Auth    │  │ Projects │  │  Board   │  │ Reports  │            │  │
│  │  │  Module  │  │  Module  │  │  Module  │  │  Module  │            │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │  │
│  │                                                                       │  │
│  │  ┌──────────────────┐    ┌──────────────────┐                       │  │
│  │  │   Redux Store     │    │   React Query    │                       │  │
│  │  │ (auth, ui state) │    │ (server cache)   │                       │  │
│  │  └──────────────────┘    └──────────────────┘                       │  │
│  │                                                                       │  │
│  │  ┌────────────────────────────────────────────────────────────────┐  │  │
│  │  │         Axios HTTP Client + Socket.IO Client                   │  │  │
│  │  └────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────┬───────────────────────┘
                         │ REST/HTTPS                  │ WebSocket (WSS)
                         │                             │
┌────────────────────────▼─────────────────────────────▼───────────────────────┐
│                              API TIER (NestJS)                                │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                          Request Pipeline                               │  │
│  │  Request → Logger → CORS → RateLimit → Auth Guard → RBAC Guard        │  │
│  │  Response ← Global Exception Filter ← Serializer ← Controller         │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │   Auth   │ │  Users   │ │ Projects │ │ Tickets  │ │ Sprints  │          │
│  │ Module   │ │  Module  │ │  Module  │ │  Module  │ │  Module  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│                                                                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                       │
│  │Comments  │ │  Search  │ │ Reports  │ │Realtime  │                       │
│  │  Module  │ │  Module  │ │  Module  │ │(Socket)  │                       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                       │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                        Shared Infrastructure                            │  │
│  │   PrismaService │ RedisService │ MailService │ StorageService          │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
└──────────┬────────────────────┬─────────────────────┬─────────────────────────┘
           │                    │                      │
┌──────────▼──────┐  ┌──────────▼──────┐  ┌──────────▼──────┐
│  DATA TIER      │  │  CACHE TIER     │  │  STORAGE TIER   │
│                 │  │                 │  │                 │
│  PostgreSQL 15  │  │    Redis 7      │  │    AWS S3       │
│  (AWS RDS)      │  │  (ElastiCache)  │  │  (Attachments)  │
│                 │  │                 │  │                 │
│  - users        │  │ - Sessions      │  │ - /attachments/ │
│  - projects     │  │ - Board State   │  │ - /avatars/     │
│  - tickets      │  │ - Rate Limits   │  │                 │
│  - sprints      │  │ - Active Sprint │  │                 │
│  - comments     │  │ - Token Blklist │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## 3. Module Interaction Matrix

| Source Module | Target Module | Interaction Type | Description |
|---------------|---------------|-----------------|-------------|
| Auth | Users | In-process call | Validate user credentials on login |
| Auth | Redis | Cache write | Store refresh tokens |
| Projects | Users | In-process call | Verify user membership |
| Tickets | Projects | In-process call | Validate project access |
| Tickets | Sprints | In-process call | Assign ticket to sprint |
| Tickets | Realtime | Event emit | Broadcast ticket update |
| Sprints | Tickets | In-process call | Bulk ticket status on sprint complete |
| Comments | Notifications | Event emit | Trigger notification on new comment |
| Search | PostgreSQL | Full-text query | `tsvector` search over titles/descriptions |
| Reports | PostgreSQL | Aggregation query | Burndown, velocity calculations |

---

## 4. API Design

### 4.1 Base URL Structure
```
https://api.yourdomain.com/api/v1/
```

### 4.2 Authentication Endpoints
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Create new account | No |
| POST | `/auth/login` | Login, receive tokens | No |
| POST | `/auth/logout` | Invalidate refresh token | Yes |
| POST | `/auth/refresh` | Exchange refresh for new access token | No (uses refresh) |
| POST | `/auth/forgot-password` | Request password reset email | No |
| POST | `/auth/reset-password` | Apply new password via token | No |
| GET | `/auth/me` | Get current user profile | Yes |

### 4.3 User Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/me` | Get own profile |
| PUT | `/users/me` | Update own profile |
| PUT | `/users/me/password` | Change password |
| GET | `/users/:id` | Get user by ID (project member lookup) |

### 4.4 Project Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects` | Create project |
| GET | `/projects` | List user's projects |
| GET | `/projects/:id` | Get project detail |
| PUT | `/projects/:id` | Update project |
| DELETE | `/projects/:id` | Soft-delete project |
| GET | `/projects/:id/members` | List members |
| POST | `/projects/:id/members` | Invite member |
| PUT | `/projects/:id/members/:userId` | Update member role |
| DELETE | `/projects/:id/members/:userId` | Remove member |

### 4.5 Ticket Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/:id/tickets` | Create ticket |
| GET | `/projects/:id/tickets` | List tickets (paginated, filterable) |
| GET | `/tickets/:id` | Get ticket detail |
| PUT | `/tickets/:id` | Update ticket fields |
| DELETE | `/tickets/:id` | Soft-delete ticket |
| POST | `/tickets/:id/transition` | Change workflow status |
| PUT | `/tickets/:id/sprint` | Assign to sprint |
| POST | `/tickets/:id/labels` | Attach label |
| DELETE | `/tickets/:id/labels/:labelId` | Remove label |
| GET | `/tickets/:id/history` | Get activity log |
| POST | `/tickets/:id/watch` | Watch ticket |
| DELETE | `/tickets/:id/watch` | Unwatch ticket |
| GET | `/tickets/search` | Search tickets with query params |

### 4.6 Sprint Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/:id/sprints` | Create sprint |
| GET | `/projects/:id/sprints` | List sprints |
| GET | `/sprints/:id` | Get sprint detail |
| PUT | `/sprints/:id` | Update sprint |
| POST | `/sprints/:id/start` | Activate sprint |
| POST | `/sprints/:id/complete` | Complete sprint |
| GET | `/sprints/:id/board` | Get board (grouped by status) |
| GET | `/sprints/:id/stats` | Sprint statistics |
| PUT | `/sprints/:id/tickets` | Bulk assign tickets to sprint |
| GET | `/projects/:id/backlog` | Get project backlog |

### 4.7 Comment Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/tickets/:id/comments` | Add comment |
| GET | `/tickets/:id/comments` | List comments |
| PUT | `/comments/:id` | Edit own comment |
| DELETE | `/comments/:id` | Delete own comment |

### 4.8 Standard Response Envelope
```json
{
  "data": { ... },
  "meta": {
    "page": 1,
    "pageSize": 25,
    "total": 150,
    "totalPages": 6
  }
}
```

### 4.9 Error Response (RFC 7807)
```json
{
  "type": "https://api.yourdomain.com/errors/not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "Ticket PROJ-123 does not exist",
  "instance": "/api/v1/tickets/PROJ-123",
  "correlationId": "abc-123-xyz"
}
```

---

## 5. Real-Time Architecture (Socket.IO)

### 5.1 Namespace and Room Strategy
```
Namespace:  /board
  Room:     board:{sprintId}      → broadcast ticket status updates
  Room:     ticket:{ticketId}     → broadcast comment additions
  
Namespace:  /notifications
  Room:     user:{userId}         → personal notifications
```

### 5.2 Events (Server → Client)
| Event | Payload | Trigger |
|-------|---------|---------|
| `ticket:updated` | `{ ticketId, changes }` | Any ticket field change |
| `ticket:moved` | `{ ticketId, fromStatus, toStatus, movedBy }` | Status transition |
| `ticket:assigned` | `{ ticketId, assigneeId }` | Assignment change |
| `comment:added` | `{ ticketId, comment }` | New comment posted |
| `sprint:started` | `{ sprintId }` | Sprint activated |
| `sprint:completed` | `{ sprintId }` | Sprint completed |
| `notification:new` | `{ notification }` | Any notification event |

### 5.3 Events (Client → Server)
| Event | Action |
|-------|--------|
| `board:join` | Subscribe to a sprint board room |
| `board:leave` | Unsubscribe from sprint board room |
| `ticket:join` | Subscribe to a ticket detail room |

---

## 6. State Management (Frontend)

### 6.1 Redux Store (Global Persistent State)
```
store/
├── auth/       { user, accessToken, isAuthenticated }
├── ui/         { theme, sidebarOpen, activeProject }
└── notifications/ { unreadCount, items }
```

### 6.2 React Query (Server State)
```
Query Keys:
  ['projects']                      → project list
  ['projects', id]                  → single project
  ['projects', id, 'tickets']       → project ticket list
  ['tickets', id]                   → single ticket
  ['sprints', id, 'board']          → sprint board data
  ['projects', id, 'backlog']       → backlog tickets
  ['tickets', id, 'comments']       → comments
  ['tickets', id, 'history']        → activity log
  ['sprints', id, 'stats']          → sprint stats
```

---

## 7. Security Architecture

### 7.1 Token Strategy
```
Access Token:
  - Type: JWT (RS256)
  - TTL: 15 minutes
  - Payload: { sub, email, role, projectRoles }
  - Stored: Memory (JS variable) — NOT localStorage
  
Refresh Token:
  - Type: Opaque random string (UUID v4)
  - TTL: 7 days
  - Stored: HttpOnly Cookie + Redis whitelist
  - Rotation: New refresh token issued on every refresh
```

### 7.2 RBAC Permission Matrix
| Resource | Admin | Project Owner | Team Member | Viewer |
|----------|-------|---------------|-------------|--------|
| Create Project | ✅ | ✅ | ❌ | ❌ |
| Delete Project | ✅ | ✅ | ❌ | ❌ |
| Manage Project Members | ✅ | ✅ | ❌ | ❌ |
| Create Ticket | ✅ | ✅ | ✅ | ❌ |
| Edit Any Ticket | ✅ | ✅ | ❌ | ❌ |
| Edit Assigned Ticket | ✅ | ✅ | ✅ | ❌ |
| Delete Ticket | ✅ | ✅ | ❌ | ❌ |
| Create Sprint | ✅ | ✅ | ❌ | ❌ |
| Start/Complete Sprint | ✅ | ✅ | ❌ | ❌ |
| View All | ✅ | ✅ | ✅ | ✅ |

---

## 8. Caching Strategy

| Data | Cache Key | TTL | Invalidation Trigger |
|------|-----------|-----|----------------------|
| Sprint Board | `board:{sprintId}` | 5 min | Any ticket update in sprint |
| Active Sprint | `project:{id}:activeSprint` | 10 min | Sprint start/complete |
| User Profile | `user:{id}:profile` | 30 min | Profile update |
| Project Members | `project:{id}:members` | 15 min | Member add/remove |
| Refresh Tokens | `rt:{userId}:{jti}` | 7 days | Logout / rotation |

---

## 9. Database Connection Pooling

```
Prisma Connection Pool:
  - Min connections: 5
  - Max connections: 20
  - Idle timeout: 60s
  - Connection timeout: 10s

Redis:
  - Max connections: 50
  - Retry strategy: exponential backoff (max 5 retries)
```

---

## 10. Non-Functional Architecture Decisions

### 10.1 Scalability
- NestJS app is **stateless** — all shared state (sessions, rate counters) is in Redis
- Horizontal scaling via ECS desired count; ALB distributes traffic
- Socket.IO uses Redis Adapter so multiple API instances share room membership

### 10.2 Reliability
- RDS Multi-AZ failover (≤30s RTO on DB failure)
- ECS tasks auto-replace on health check failure
- Dead Letter Queue for failed notification emails (SQS + SES)

### 10.3 Performance
- PostgreSQL query optimization: composite indexes on `(project_id, status)`, `(sprint_id, status)`, `(assignee_id, project_id)`
- Full-text search: `tsvector` column on `tickets.title` and `tickets.description`
- Pagination: cursor-based for board columns; offset-based for list views
