# API Contract — MVP1.0
## Jira-Like Project Management Application

**Version**: 1.0  
**Date**: February 22, 2026  
**Scope**: MVP1.0 — Authentication, Projects, Tickets  
**Stack**: FastAPI (Python 3.12) + PostgreSQL 15 + Redis 7  

> This document is the single source of truth for all API shapes.  
> Backend implements against it. Frontend consumes against it.  
> Do not deviate without updating this document first.

---

## 1. Base Conventions

| Property | Value |
|---|---|
| Base URL (local) | `http://localhost:8000/api/v1` |
| Content-Type | `application/json` |
| Auth header | `Authorization: Bearer <access_token>` |
| Refresh token | HttpOnly cookie named `refresh_token`; path `/api/v1/auth`; `SameSite=Lax` |
| Timestamps | ISO 8601 UTC — `2026-02-22T10:00:00Z` |
| IDs | UUID v4 strings |
| API versioning | `/api/v1/` prefix on all routes |

---

## 2. Common Schemas

### 2.1 Error Response
All `4xx` and `5xx` responses return this shape:

```json
{
  "detail": "Human-readable description of the error.",
  "code": "MACHINE_READABLE_CODE"
}
```

| Code | Meaning |
|---|---|
| `EMAIL_TAKEN` | Email address is already registered |
| `PROJECT_KEY_TAKEN` | Project key is already in use |
| `INVALID_CREDENTIALS` | Wrong email or password |
| `TOKEN_EXPIRED` | JWT or refresh token is expired / missing |
| `FORBIDDEN` | Authenticated but not authorized for this action |
| `NOT_FOUND` | Resource does not exist (or is soft-deleted) |
| `VALIDATION_ERROR` | Request body failed Pydantic validation |

> **422 Unprocessable Entity** uses FastAPI's native Pydantic shape instead:
> ```json
> {
>   "detail": [
>     {
>       "loc": ["body", "email"],
>       "msg": "value is not a valid email address",
>       "type": "value_error"
>     }
>   ]
> }
> ```

---

### 2.2 Paginated Response
All list endpoints that support pagination return:

```json
{
  "items": [ ...resource objects... ],
  "total": 42,
  "skip": 0,
  "limit": 20
}
```

---

### 2.3 Enums

#### TicketType
```
BUG | STORY | TASK | EPIC
```

#### TicketPriority
```
BLOCKER | HIGH | MEDIUM | LOW
```

#### TicketStatus
```
TODO | IN_PROGRESS | IN_REVIEW | DONE
```

#### ProjectMemberRole
```
OWNER | ADMIN | MEMBER
```

---

## 3. Auth Endpoints

### 3.1 Register
```
POST /auth/register
```
No authentication required.

**Request Body**
```json
{
  "full_name": "Jane Doe",
  "email": "jane@example.com",
  "password": "MinLength8WithNumber1"
}
```

| Field | Type | Rules |
|---|---|---|
| `full_name` | string | 1–100 chars |
| `email` | string | valid email format, unique |
| `password` | string | min 8 chars |

**Response `201 Created`**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```
Sets response header:
```
Set-Cookie: refresh_token=<token>; HttpOnly; SameSite=Lax; Path=/api/v1/auth; Max-Age=604800
```

**Error Responses**
| Status | Code | Condition |
|---|---|---|
| 409 | `EMAIL_TAKEN` | Email already registered |
| 422 | — | Pydantic validation failure |

---

### 3.2 Login
```
POST /auth/login
```
No authentication required.

**Request Body**
```json
{
  "email": "jane@example.com",
  "password": "MinLength8WithNumber1"
}
```

**Response `200 OK`**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```
Sets `refresh_token` cookie (same as register).

**Error Responses**
| Status | Code | Condition |
|---|---|---|
| 401 | `INVALID_CREDENTIALS` | Email not found or password incorrect |
| 422 | — | Validation failure |

---

### 3.3 Refresh Token
```
POST /auth/refresh
```
No `Authorization` header required.  
`refresh_token` HttpOnly cookie **must** be present (browser sends automatically).

**Request Body** — none

**Response `200 OK`**
```json
{
  "access_token": "<new_jwt>",
  "token_type": "bearer"
}
```
Old refresh token is deleted from Redis. New `refresh_token` cookie is set.

**Error Responses**
| Status | Code | Condition |
|---|---|---|
| 401 | `TOKEN_EXPIRED` | Cookie missing, Redis TTL expired, or token tampered |

---

### 3.4 Logout
```
POST /auth/logout
```
🔒 Requires `Authorization: Bearer <access_token>`

**Request Body** — none

**Response `204 No Content`** — no body

Deletes refresh token from Redis. Clears `refresh_token` cookie (`Max-Age=0`).

---

## 4. User Endpoints

### 4.1 Get Current User
```
GET /users/me
```
🔒 Requires Bearer token.

**Response `200 OK`**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "full_name": "Jane Doe",
  "email": "jane@example.com",
  "created_at": "2026-02-22T10:00:00Z"
}
```

---

## 5. Project Endpoints

### 5.1 Create Project
```
POST /projects
```
🔒 Requires Bearer token.

**Request Body**
```json
{
  "name": "My Project",
  "key": "MYPROJ",
  "description": "Optional project description"
}
```

| Field | Type | Rules |
|---|---|---|
| `name` | string | 1–100 chars |
| `key` | string | 2–10 uppercase letters only (e.g. `PROJ`), globally unique |
| `description` | string \| null | optional, max 500 chars |

**Response `201 Created`**
```json
{
  "id": "uuid",
  "name": "My Project",
  "key": "MYPROJ",
  "description": "Optional project description",
  "owner_id": "uuid",
  "created_at": "2026-02-22T10:00:00Z",
  "updated_at": "2026-02-22T10:00:00Z"
}
```
The creator is automatically inserted as `OWNER` in the `project_members` table.

**Error Responses**
| Status | Code | Condition |
|---|---|---|
| 409 | `PROJECT_KEY_TAKEN` | Key already used by another project |
| 422 | — | Key format invalid or name too long |

---

### 5.2 List My Projects
```
GET /projects
```
🔒 Requires Bearer token.

**Query Parameters** — none for MVP1.0

**Response `200 OK`**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "My Project",
      "key": "MYPROJ",
      "description": "Optional project description",
      "owner_id": "uuid",
      "created_at": "2026-02-22T10:00:00Z",
      "updated_at": "2026-02-22T10:00:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50
}
```
Returns only projects where the current user has a `project_members` row.

---

### 5.3 Get Project Detail
```
GET /projects/{project_id}
```
🔒 Requires Bearer token.

**Path Parameter**
| Param | Type | Description |
|---|---|---|
| `project_id` | UUID | Project identifier |

**Response `200 OK`** — same shape as the single project object above.

**Error Responses**
| Status | Code | Condition |
|---|---|---|
| 403 | `FORBIDDEN` | Authenticated user is not a member of this project |
| 404 | `NOT_FOUND` | Project does not exist |

---

## 6. Ticket Endpoints

### 6.1 Create Ticket
```
POST /projects/{project_id}/tickets
```
🔒 Requires Bearer token. User must be a project member.

**Path Parameter**
| Param | Type | Description |
|---|---|---|
| `project_id` | UUID | Parent project |

**Request Body**
```json
{
  "title": "Fix login bug",
  "ticket_type": "BUG",
  "priority": "HIGH",
  "description": "Steps to reproduce: ...",
  "assignee_id": "uuid"
}
```

| Field | Type | Rules |
|---|---|---|
| `title` | string | required, 1–255 chars |
| `ticket_type` | TicketType | required — `BUG \| STORY \| TASK \| EPIC` |
| `priority` | TicketPriority | required — `BLOCKER \| HIGH \| MEDIUM \| LOW` |
| `description` | string \| null | optional, markdown supported |
| `assignee_id` | UUID \| null | optional, must be a member of this project |

**Response `201 Created`**
```json
{
  "id": "uuid",
  "key": "MYPROJ-1",
  "title": "Fix login bug",
  "ticket_type": "BUG",
  "priority": "HIGH",
  "status": "TODO",
  "description": "Steps to reproduce: ...",
  "assignee_id": "uuid",
  "reporter_id": "uuid",
  "project_id": "uuid",
  "story_points": null,
  "is_deleted": false,
  "created_at": "2026-02-22T10:00:00Z",
  "updated_at": "2026-02-22T10:00:00Z"
}
```

> `key` is auto-generated as `{PROJECT_KEY}-{n}` where `n` is the next sequential integer for this project (e.g. `MYPROJ-1`, `MYPROJ-2`).  
> `status` always defaults to `TODO` on creation.  
> `reporter_id` is always set to the authenticated user.

**Error Responses**
| Status | Code | Condition |
|---|---|---|
| 403 | `FORBIDDEN` | User is not a member of this project |
| 404 | `NOT_FOUND` | Project not found |
| 422 | — | Validation failure |

---

### 6.2 List Tickets
```
GET /projects/{project_id}/tickets
```
🔒 Requires Bearer token. User must be a project member.

**Query Parameters**
| Param | Type | Default | Notes |
|---|---|---|---|
| `skip` | integer | `0` | Pagination offset |
| `limit` | integer | `20` | Max `100` |

**Response `200 OK`**
```json
{
  "items": [ ...ticket objects... ],
  "total": 42,
  "skip": 0,
  "limit": 20
}
```
Excludes soft-deleted tickets (`is_deleted = false` filter applied server-side).

**Error Responses**
| Status | Code | Condition |
|---|---|---|
| 403 | `FORBIDDEN` | User is not a project member |
| 404 | `NOT_FOUND` | Project not found |

---

### 6.3 Get Ticket Detail
```
GET /tickets/{ticket_id}
```
🔒 Requires Bearer token.

**Path Parameter**
| Param | Type | Description |
|---|---|---|
| `ticket_id` | UUID | Ticket identifier |

**Response `200 OK`** — full ticket object (same shape as create response).

**Error Responses**
| Status | Code | Condition |
|---|---|---|
| 403 | `FORBIDDEN` | User is not a member of the ticket's project |
| 404 | `NOT_FOUND` | Ticket not found or is soft-deleted |

---

### 6.4 Update Ticket
```
PUT /tickets/{ticket_id}
```
🔒 Requires Bearer token. Must be the assignee, reporter, or project OWNER/ADMIN.

**Request Body** — all fields optional (partial update; omitted fields are unchanged)
```json
{
  "title": "Updated title",
  "ticket_type": "STORY",
  "priority": "MEDIUM",
  "status": "IN_PROGRESS",
  "description": "Updated description",
  "assignee_id": "uuid",
  "story_points": 3
}
```

| Field | Type | Notes |
|---|---|---|
| `title` | string \| omit | 1–255 chars |
| `ticket_type` | TicketType \| omit | — |
| `priority` | TicketPriority \| omit | — |
| `status` | TicketStatus \| omit | `TODO \| IN_PROGRESS \| IN_REVIEW \| DONE` |
| `description` | string \| null \| omit | null clears the field |
| `assignee_id` | UUID \| null \| omit | null unassigns |
| `story_points` | integer \| null \| omit | null clears the field |

**Response `200 OK`** — updated ticket object.

**Error Responses**
| Status | Code | Condition |
|---|---|---|
| 403 | `FORBIDDEN` | User is not assignee, reporter, or OWNER/ADMIN |
| 404 | `NOT_FOUND` | Ticket not found |
| 422 | — | Invalid enum value or field length |

---

### 6.5 Delete Ticket (Soft)
```
DELETE /tickets/{ticket_id}
```
🔒 Requires Bearer token. Must be project OWNER.

**Response `204 No Content`** — no body.

Sets `is_deleted = true` and `updated_at = now()`. Ticket will no longer appear in list or detail endpoints.

**Error Responses**
| Status | Code | Condition |
|---|---|---|
| 403 | `FORBIDDEN` | User is not the project OWNER |
| 404 | `NOT_FOUND` | Ticket not found |

---

## 7. Health Check

### 7.1 Health
```
GET /health
```
No authentication required.

**Response `200 OK`**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

## 8. Endpoint Summary

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | ❌ Public | Register new user |
| `POST` | `/api/v1/auth/login` | ❌ Public | Login, get tokens |
| `POST` | `/api/v1/auth/refresh` | 🍪 Cookie only | Rotate access token |
| `POST` | `/api/v1/auth/logout` | 🔒 Bearer | Logout, clear tokens |
| `GET` | `/api/v1/users/me` | 🔒 Bearer | Get own profile |
| `POST` | `/api/v1/projects` | 🔒 Bearer | Create project |
| `GET` | `/api/v1/projects` | 🔒 Bearer | List my projects |
| `GET` | `/api/v1/projects/{id}` | 🔒 Bearer | Get project detail |
| `POST` | `/api/v1/projects/{id}/tickets` | 🔒 Bearer | Create ticket |
| `GET` | `/api/v1/projects/{id}/tickets` | 🔒 Bearer | List tickets (paginated) |
| `GET` | `/api/v1/tickets/{id}` | 🔒 Bearer | Get ticket detail |
| `PUT` | `/api/v1/tickets/{id}` | 🔒 Bearer | Partial update ticket |
| `DELETE` | `/api/v1/tickets/{id}` | 🔒 Bearer | Soft delete ticket |
| `GET` | `/health` | ❌ Public | Health check |

---

## 9. Frontend Integration Notes

### Axios Setup
```
baseURL: import.meta.env.VITE_API_URL  (e.g. http://localhost:8000/api/v1)
withCredentials: true                   (required for refresh token cookie)
Content-Type: application/json
```

### Token Lifecycle (Frontend)
1. On `login` / `register` → store `access_token` in Redux (memory only, never localStorage)
2. On every request → Axios interceptor adds `Authorization: Bearer <access_token>`
3. On `401` response → interceptor calls `POST /auth/refresh` (cookie sent automatically)
   - Success: update Redux with new token, retry original request
   - Failure: dispatch `clearCredentials`, redirect to `/login`
4. On app boot → call `POST /auth/refresh` to restore session from cookie

### CORS
Backend must allow:
```
Origin: http://localhost:5173
Credentials: true
Methods: GET, POST, PUT, DELETE, OPTIONS
Headers: Authorization, Content-Type
```

---

**Document Version**: 1.0  
**Last Updated**: February 22, 2026  
**Status**: Approved for MVP1.0 Development
