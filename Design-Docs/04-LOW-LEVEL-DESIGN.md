# Low-Level Design (LLD)
## Jira-Like Project Management Application

**Version**: 1.0  
**Date**: February 21, 2026  
**Author**: Architecture Team  
**Status**: Approved

---

## 1. Database Schema

### 1.1 Entity-Relationship Overview
```
users ──< project_members >── projects ──< tickets
                                 └──< sprints ──< tickets
                                                    ├──< comments
                                                    ├──< ticket_history
                                                    ├──< ticket_labels >── labels
                                                    └──< ticket_watchers
```

### 1.2 Complete Schema (Prisma SDL)

```prisma
// ─────────────────────────────────────────────
// USERS
// ─────────────────────────────────────────────
model User {
  id            String    @id @default(uuid())
  email         String    @unique
  passwordHash  String
  firstName     String
  lastName      String
  avatarUrl     String?
  role          SystemRole @default(MEMBER)   // Global system role
  isVerified    Boolean   @default(false)
  isActive      Boolean   @default(true)
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt

  projectMemberships  ProjectMember[]
  assignedTickets     Ticket[]        @relation("TicketAssignee")
  reportedTickets     Ticket[]        @relation("TicketReporter")
  comments            Comment[]
  ticketHistory       TicketHistory[]
  notifications       Notification[]
  watchedTickets      TicketWatcher[]

  @@index([email])
}

enum SystemRole {
  ADMIN
  MEMBER
}

// ─────────────────────────────────────────────
// PROJECTS
// ─────────────────────────────────────────────
model Project {
  id          String        @id @default(uuid())
  key         String        @unique   // e.g. "PROJ" — used as ticket prefix
  name        String
  description String?
  isPublic    Boolean       @default(false)
  isArchived  Boolean       @default(false)
  createdAt   DateTime      @default(now())
  updatedAt   DateTime      @updatedAt

  members     ProjectMember[]
  tickets     Ticket[]
  sprints     Sprint[]
  labels      Label[]

  @@index([key])
}

model ProjectMember {
  id          String      @id @default(uuid())
  projectId   String
  userId      String
  role        ProjectRole @default(MEMBER)
  joinedAt    DateTime    @default(now())

  project     Project     @relation(fields: [projectId], references: [id])
  user        User        @relation(fields: [userId], references: [id])

  @@unique([projectId, userId])
  @@index([projectId])
  @@index([userId])
}

enum ProjectRole {
  OWNER
  MEMBER
  VIEWER
}

// ─────────────────────────────────────────────
// SPRINTS
// ─────────────────────────────────────────────
model Sprint {
  id          String        @id @default(uuid())
  projectId   String
  name        String
  goal        String?
  status      SprintStatus  @default(DRAFT)
  startDate   DateTime?
  endDate     DateTime?
  completedAt DateTime?
  createdAt   DateTime      @default(now())
  updatedAt   DateTime      @updatedAt

  project     Project       @relation(fields: [projectId], references: [id])
  tickets     Ticket[]

  @@index([projectId, status])
}

enum SprintStatus {
  DRAFT
  ACTIVE
  COMPLETED
}

// ─────────────────────────────────────────────
// TICKETS
// ─────────────────────────────────────────────
model Ticket {
  id              String        @id @default(uuid())
  key             String        @unique   // e.g. "PROJ-42" — auto-generated
  projectId       String
  sprintId        String?
  parentId        String?       // for subtasks
  
  title           String        @db.VarChar(255)
  description     String?       @db.Text
  type            TicketType    @default(TASK)
  status          TicketStatus  @default(TODO)
  priority        Priority      @default(MEDIUM)
  storyPoints     Int?
  dueDate         DateTime?
  
  assigneeId      String?
  reporterId      String
  
  backlogOrder    Int?          // position in backlog for drag-reorder
  boardOrder      Int?          // position within status column on board
  
  isDeleted       Boolean       @default(false)
  createdAt       DateTime      @default(now())
  updatedAt       DateTime      @updatedAt

  project         Project       @relation(fields: [projectId], references: [id])
  sprint          Sprint?       @relation(fields: [sprintId], references: [id])
  parent          Ticket?       @relation("TicketSubtasks", fields: [parentId], references: [id])
  subtasks        Ticket[]      @relation("TicketSubtasks")
  assignee        User?         @relation("TicketAssignee", fields: [assigneeId], references: [id])
  reporter        User          @relation("TicketReporter", fields: [reporterId], references: [id])
  comments        Comment[]
  history         TicketHistory[]
  labels          TicketLabel[]
  watchers        TicketWatcher[]
  attachments     Attachment[]
  
  // Full-text search vector (maintained by trigger)
  searchVector    Unsupported("tsvector")?

  @@index([projectId, status])
  @@index([projectId, sprintId])
  @@index([assigneeId, projectId])
  @@index([sprintId, status])
  @@index([isDeleted, projectId])
}

enum TicketType {
  EPIC
  STORY
  TASK
  BUG
  SUBTASK
}

enum TicketStatus {
  TODO
  IN_PROGRESS
  IN_REVIEW
  DONE
  CANCELLED
}

enum Priority {
  BLOCKER
  CRITICAL
  HIGH
  MEDIUM
  LOW
}

// ─────────────────────────────────────────────
// COMMENTS
// ─────────────────────────────────────────────
model Comment {
  id          String    @id @default(uuid())
  ticketId    String
  authorId    String
  content     String    @db.Text
  isDeleted   Boolean   @default(false)
  createdAt   DateTime  @default(now())
  updatedAt   DateTime  @updatedAt

  ticket      Ticket    @relation(fields: [ticketId], references: [id])
  author      User      @relation(fields: [authorId], references: [id])
  mentions    Mention[]

  @@index([ticketId, createdAt])
}

model Mention {
  id          String    @id @default(uuid())
  commentId   String
  userId      String
  comment     Comment   @relation(fields: [commentId], references: [id])
  
  @@unique([commentId, userId])
}

// ─────────────────────────────────────────────
// AUDIT / HISTORY
// ─────────────────────────────────────────────
model TicketHistory {
  id          String    @id @default(uuid())
  ticketId    String
  userId      String
  field       String    // e.g. "status", "assignee", "priority"
  oldValue    String?
  newValue    String?
  changedAt   DateTime  @default(now())

  ticket      Ticket    @relation(fields: [ticketId], references: [id])
  user        User      @relation(fields: [userId], references: [id])

  @@index([ticketId, changedAt])
}

// ─────────────────────────────────────────────
// LABELS
// ─────────────────────────────────────────────
model Label {
  id          String        @id @default(uuid())
  projectId   String
  name        String
  color       String        @default("#6B7280")
  project     Project       @relation(fields: [projectId], references: [id])
  tickets     TicketLabel[]

  @@unique([projectId, name])
}

model TicketLabel {
  ticketId    String
  labelId     String
  ticket      Ticket    @relation(fields: [ticketId], references: [id])
  label       Label     @relation(fields: [labelId], references: [id])

  @@id([ticketId, labelId])
}

// ─────────────────────────────────────────────
// WATCHERS
// ─────────────────────────────────────────────
model TicketWatcher {
  ticketId    String
  userId      String
  ticket      Ticket    @relation(fields: [ticketId], references: [id])
  user        User      @relation(fields: [userId], references: [id])

  @@id([ticketId, userId])
  @@index([userId])
}

// ─────────────────────────────────────────────
// ATTACHMENTS
// ─────────────────────────────────────────────
model Attachment {
  id          String    @id @default(uuid())
  ticketId    String
  uploadedBy  String
  fileName    String
  fileSize    Int
  mimeType    String
  s3Key       String
  createdAt   DateTime  @default(now())
  ticket      Ticket    @relation(fields: [ticketId], references: [id])

  @@index([ticketId])
}

// ─────────────────────────────────────────────
// NOTIFICATIONS
// ─────────────────────────────────────────────
model Notification {
  id          String            @id @default(uuid())
  userId      String
  type        NotificationType
  title       String
  body        String
  resourceId  String?           // e.g., ticketId or sprintId
  isRead      Boolean           @default(false)
  createdAt   DateTime          @default(now())

  user        User              @relation(fields: [userId], references: [id])

  @@index([userId, isRead, createdAt])
}

enum NotificationType {
  TICKET_ASSIGNED
  STATUS_CHANGED
  COMMENT_ADDED
  MENTIONED
  SPRINT_STARTED
  SPRINT_COMPLETED
  DUE_DATE_APPROACHING
}
```

---

## 2. Key Design Decisions

### 2.1 Ticket Key Generation
```typescript
// Service: TicketsService.generateKey()
async generateKey(projectId: string): Promise<string> {
  const project = await this.prisma.project.findUnique({
    where: { id: projectId },
    select: { key: true }
  });
  
  // Atomic counter using PostgreSQL sequence
  const result = await this.prisma.$queryRaw<{ nextval: bigint }[]>`
    SELECT nextval('ticket_seq_${Prisma.raw(project.key)}')
  `;
  
  return `${project.key}-${result[0].nextval}`;
}
```

**Rationale**: PostgreSQL sequences are gap-tolerant, thread-safe, and never re-use values even on rollback.

### 2.2 Ticket Status Workflow
```
           ┌──────────────────────────────┐
           │                              │
    ┌──────▼──────┐                       │
    │    TODO     │──────────────┐        │
    └──────┬──────┘              │        │
           │                     │        │
    ┌──────▼──────┐               │        │
    │ IN_PROGRESS │───────────────┤        │
    └──────┬──────┘               │        │
           │                     │        │
    ┌──────▼──────┐               │        │
    │  IN_REVIEW  │───────────────┤        │
    └──────┬──────┘               │        │
           │                     │        │
    ┌──────▼──────┐        ┌──────▼──────┐│
    │    DONE     │        │ CANCELLED   ││
    └─────────────┘        └─────────────┘┘
```

Valid transitions enforced in `TicketTransitionService`:
```typescript
const ALLOWED_TRANSITIONS: Record<TicketStatus, TicketStatus[]> = {
  TODO:        ['IN_PROGRESS', 'CANCELLED'],
  IN_PROGRESS: ['TODO', 'IN_REVIEW', 'DONE', 'CANCELLED'],
  IN_REVIEW:   ['IN_PROGRESS', 'DONE', 'CANCELLED'],
  DONE:        ['IN_PROGRESS'],        // allow reopening
  CANCELLED:   ['TODO'],               // allow re-activating
};
```

### 2.3 Backlog Ordering
- `backlogOrder` is a floating-point field (f64)
- Insert between items A and B: `order = (A.backlogOrder + B.backlogOrder) / 2`
- Re-index (reset to integers 1000, 2000, 3000...) when gap < 0.001 to avoid precision loss

---

## 3. NestJS Module Internal Design

### 3.1 Tickets Module Structure
```
tickets/
├── tickets.module.ts          → Import declarations
├── tickets.controller.ts      → HTTP route handlers, validation pipes
├── tickets.service.ts         → Business logic orchestration
├── ticket-transition.service.ts  → Workflow validation
├── ticket-search.service.ts   → Full-text search queries
├── dto/
│   ├── create-ticket.dto.ts   → class-validator decorated DTO
│   ├── update-ticket.dto.ts
│   ├── transition-ticket.dto.ts
│   └── list-tickets.dto.ts    → Filter/sort/page query params
├── entities/
│   └── ticket.entity.ts       → Response serialization class
├── guards/
│   └── ticket-access.guard.ts → Per-resource RBAC
└── events/
    └── ticket.events.ts       → EventEmitter2 event classes
```

### 3.2 TicketsService Core Methods
```typescript
class TicketsService {
  async create(projectId: string, dto: CreateTicketDto, userId: string): Promise<Ticket>
  async findAll(projectId: string, filters: ListTicketsDto): Promise<PaginatedResult<Ticket>>
  async findById(id: string): Promise<Ticket>
  async update(id: string, dto: UpdateTicketDto, userId: string): Promise<Ticket>
  async softDelete(id: string, userId: string): Promise<void>
  async transition(id: string, dto: TransitionTicketDto, userId: string): Promise<Ticket>
  async assignToSprint(id: string, sprintId: string | null): Promise<Ticket>
  async search(projectId: string, query: string, filters: Partial<ListTicketsDto>): Promise<Ticket[]>
  private async generateKey(projectId: string): Promise<string>
  private async recordHistory(ticketId: string, userId: string, changes: FieldChange[]): Promise<void>
  private async invalidateBoardCache(sprintId: string): Promise<void>
}
```

### 3.3 Authorization Guard Chain
```
Request
  │
  ▼
JwtAuthGuard           → Decodes JWT, attaches user to request
  │
  ▼
ProjectMemberGuard     → Checks user has membership in the project
  │
  ▼
RolesGuard             → Checks user has sufficient project role for the operation
  │
  ▼
Route Handler
```

---

## 4. Frontend Component Architecture

### 4.1 Page Component Tree (Phase 1)
```
App
├── AuthLayout
│   ├── LoginPage
│   ├── RegisterPage
│   └── ForgotPasswordPage
│
└── AppLayout
    ├── TopNav
    │   ├── ProjectSelector
    │   └── UserMenu
    ├── SideNav
    │   └── ProjectNavLinks
    │
    └── Pages
        ├── ProjectsListPage
        ├── ProjectSettingsPage
        │   └── MembersTab
        │
        ├── BacklogPage
        │   ├── BacklogList (react-dnd)
        │   └── CreateSprintModal
        │
        ├── SprintPlanningPage
        │   ├── BacklogColumn
        │   └── SprintColumn (react-dnd)
        │
        ├── SprintBoardPage (Kanban)
        │   ├── BoardToolbar (filters)
        │   └── BoardColumn × N (react-dnd)
        │       └── TicketCard
        │
        ├── TicketDetailPage
        │   ├── TicketHeader
        │   ├── TicketFields (inline editable)
        │   ├── DescriptionEditor
        │   ├── CommentsSection (Phase 2)
        │   └── ActivityLog (Phase 2)
        │
        └── SearchPage
            ├── SearchBar
            ├── FilterPanel
            └── TicketTable
```

### 4.2 Custom Hooks
```typescript
// Data fetching hooks (React Query wrappers)
useProject(projectId: string)
useProjectTickets(projectId: string, filters: TicketFilters)
useTicket(ticketId: string)
useSprintBoard(sprintId: string)
useBacklog(projectId: string)
useSprints(projectId: string)

// Mutation hooks
useCreateTicket()
useUpdateTicket()
useTransitionTicket()
useCreateSprint()
useStartSprint()
useCompleteSprint()

// Real-time hooks
useBoardRealtime(sprintId: string)  → subscribes to Socket.IO board room
useNotifications(userId: string)    → subscribes to personal notification room
```

---

## 5. Sprint Service — Lifecycle Logic

### 5.1 Start Sprint
```
Preconditions:
  - Sprint.status === DRAFT
  - No other ACTIVE sprint exists for the project
  - Sprint has at least 1 ticket
  
Steps:
  1. Validate preconditions (throw 400 if failed)
  2. Set sprint.status = ACTIVE, sprint.startDate = now()
  3. Emit socket event: sprint:started to /board:{sprintId}
  4. Create notification for all project members
  5. Invalidate Redis key: project:{id}:activeSprint
```

### 5.2 Complete Sprint
```
Preconditions:
  - Sprint.status === ACTIVE

Steps:
  1. Get incomplete tickets (status != DONE and != CANCELLED)
  2. Return list to client with options: move to backlog OR next sprint
  3. Client sends back resolution for incomplete tickets
  4. Transaction:
     a. Update sprint.status = COMPLETED, sprint.completedAt = now()
     b. For each incomplete ticket:
        - If moveToBacklog: set ticket.sprintId = null
        - If moveToNext: set ticket.sprintId = nextSprintId
     c. Create sprint completion record
  5. Emit socket event: sprint:completed
  6. Invalidate Redis: project:{id}:activeSprint, board:{sprintId}
```

---

## 6. Search Implementation

### 6.1 Full-Text Search Setup (PostgreSQL)
```sql
-- Add tsvector column to tickets
ALTER TABLE tickets ADD COLUMN search_vector tsvector;

-- Create GIN index
CREATE INDEX tickets_search_idx ON tickets USING GIN (search_vector);

-- Trigger to keep vector updated
CREATE OR REPLACE FUNCTION update_ticket_search_vector()
RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tickets_search_update
  BEFORE INSERT OR UPDATE ON tickets
  FOR EACH ROW EXECUTE FUNCTION update_ticket_search_vector();
```

### 6.2 Search Query
```typescript
async search(projectId: string, query: string, filters: TicketFilters) {
  // Exact match on ticket key (e.g. PROJ-42)
  if (/^[A-Z]+-\d+$/.test(query)) {
    return this.prisma.ticket.findMany({ where: { key: query } });
  }
  
  // Full-text search
  return this.prisma.$queryRaw`
    SELECT t.*, ts_rank(t.search_vector, plainto_tsquery('english', ${query})) AS rank
    FROM tickets t
    WHERE t.project_id = ${projectId}
      AND t.is_deleted = false
      AND t.search_vector @@ plainto_tsquery('english', ${query})
      ${filters.status ? Prisma.sql`AND t.status = ${filters.status}` : Prisma.empty}
      ${filters.assigneeId ? Prisma.sql`AND t.assignee_id = ${filters.assigneeId}` : Prisma.empty}
    ORDER BY rank DESC
    LIMIT 50
  `;
}
```

---

## 7. Redis Key Design

| Key Pattern | Type | Value | TTL |
|------------|------|-------|-----|
| `rt:{userId}:{jti}` | String | `"valid"` | 7 days |
| `rl:{ip}:{endpoint}` | Counter | request count | 1 min sliding window |
| `board:{sprintId}` | JSON String | Serialized board columns | 5 min |
| `project:{id}:activeSprint` | String | sprintId | 10 min |
| `project:{id}:members` | JSON String | Array of member objects | 15 min |
| `user:{id}:profile` | JSON String | User profile object | 30 min |

---

## 8. Error Codes Reference

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTH_001` | 401 | Invalid or expired access token |
| `AUTH_002` | 401 | Refresh token invalid or not found |
| `AUTH_003` | 400 | Invalid credentials |
| `AUTH_004` | 409 | Email already registered |
| `PROJ_001` | 404 | Project not found |
| `PROJ_002` | 403 | Not a project member |
| `PROJ_003` | 403 | Insufficient project role |
| `TICKET_001` | 404 | Ticket not found |
| `TICKET_002` | 400 | Invalid status transition |
| `TICKET_003` | 422 | Missing required fields |
| `SPRINT_001` | 404 | Sprint not found |
| `SPRINT_002` | 409 | Active sprint already exists |
| `SPRINT_003` | 400 | Sprint is not in DRAFT status |

---

## 9. DTO Definitions (Key Examples)

### 9.1 CreateTicketDto
```typescript
export class CreateTicketDto {
  @IsString()
  @MaxLength(255)
  @IsNotEmpty()
  title: string;

  @IsEnum(TicketType)
  type: TicketType;

  @IsEnum(Priority)
  priority: Priority;

  @IsString()
  @IsOptional()
  description?: string;

  @IsUUID()
  @IsOptional()
  assigneeId?: string;

  @IsUUID()
  @IsOptional()
  sprintId?: string;

  @IsInt()
  @Min(0)
  @Max(100)
  @IsOptional()
  storyPoints?: number;

  @IsDateString()
  @IsOptional()
  dueDate?: string;

  @IsArray()
  @IsUUID('4', { each: true })
  @IsOptional()
  labelIds?: string[];
}
```

### 9.2 ListTicketsDto (Filters)
```typescript
export class ListTicketsDto {
  @IsEnum(TicketStatus)
  @IsOptional()
  status?: TicketStatus;

  @IsEnum(Priority)
  @IsOptional()
  priority?: Priority;

  @IsEnum(TicketType)
  @IsOptional()
  type?: TicketType;

  @IsUUID()
  @IsOptional()
  assigneeId?: string;

  @IsUUID()
  @IsOptional()
  sprintId?: string;

  @IsString()
  @IsOptional()
  search?: string;

  @IsIn(['backlog', 'sprint'])
  @IsOptional()
  scope?: 'backlog' | 'sprint';

  @Type(() => Number)
  @IsInt()
  @Min(1)
  @IsOptional()
  page?: number = 1;

  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(100)
  @IsOptional()
  pageSize?: number = 25;

  @IsIn(['createdAt', 'updatedAt', 'priority', 'backlogOrder'])
  @IsOptional()
  sortBy?: string = 'backlogOrder';

  @IsIn(['asc', 'desc'])
  @IsOptional()
  sortOrder?: 'asc' | 'desc' = 'asc';
}
```

---

## 10. Database Indexes Summary

```sql
-- Users
CREATE UNIQUE INDEX users_email_idx ON users(email);

-- Project Members
CREATE UNIQUE INDEX pm_project_user_idx ON project_members(project_id, user_id);
CREATE INDEX pm_user_idx ON project_members(user_id);

-- Tickets (most performance-critical)
CREATE INDEX tickets_project_status_idx ON tickets(project_id, status) WHERE is_deleted = false;
CREATE INDEX tickets_sprint_status_idx ON tickets(sprint_id, status) WHERE is_deleted = false;
CREATE INDEX tickets_assignee_idx ON tickets(assignee_id, project_id) WHERE is_deleted = false;
CREATE INDEX tickets_backlog_order_idx ON tickets(project_id, backlog_order) 
    WHERE sprint_id IS NULL AND is_deleted = false;
CREATE INDEX tickets_search_vector_idx ON tickets USING GIN(search_vector);

-- Comments
CREATE INDEX comments_ticket_created_idx ON comments(ticket_id, created_at) WHERE is_deleted = false;

-- Ticket History
CREATE INDEX th_ticket_changed_idx ON ticket_history(ticket_id, changed_at);

-- Notifications
CREATE INDEX notif_user_unread_idx ON notifications(user_id, is_read, created_at);

-- Sprints
CREATE INDEX sprints_project_status_idx ON sprints(project_id, status);
```
