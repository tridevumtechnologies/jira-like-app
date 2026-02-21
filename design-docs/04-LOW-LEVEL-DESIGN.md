# Low-Level Design (LLD)
## Jira-Like Project Management Application

**Version**: 2.0 | **Date**: February 21, 2026 | **Status**: Approved

> Backend: **FastAPI (Python 3.12)** + **SQLAlchemy 2.0 (async)** + **Alembic** + **Pydantic v2**.  
> Frontend and PostgreSQL schema are unchanged from original intent.

---

## 1. Database Schema (SQLAlchemy 2.0 ORM Models)

### 1.1 Base & Mixins
```python
# app/models/base.py
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy import DateTime, func
import uuid
from datetime import datetime

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
```

### 1.2 User Model
```python
# app/models/user.py
from sqlalchemy import String, Boolean, Enum as SAEnum
from sqlalchemy.orm import relationship, mapped_column, Mapped
from app.models.base import Base, TimestampMixin
import enum, uuid
from datetime import datetime

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER  = "user"

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id:           Mapped[uuid.UUID]   = mapped_column(primary_key=True, default=uuid.uuid4)
    email:        Mapped[str]         = mapped_column(String(255), unique=True, nullable=False, index=True)
    username:     Mapped[str]         = mapped_column(String(50), unique=True, nullable=False, index=True)
    full_name:    Mapped[str]         = mapped_column(String(255), nullable=False)
    password_hash:Mapped[str]         = mapped_column(String(255), nullable=False)
    role:         Mapped[UserRole]    = mapped_column(SAEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active:    Mapped[bool]        = mapped_column(Boolean, default=True, nullable=False)
    avatar_url:   Mapped[str | None]  = mapped_column(String(500))
    last_login_at:Mapped[datetime | None]

    project_memberships: Mapped[list["ProjectMember"]] = relationship(back_populates="user")
    assigned_tickets:    Mapped[list["Ticket"]]         = relationship(back_populates="assignee",
                                                                       foreign_keys="Ticket.assignee_id")
    created_tickets:     Mapped[list["Ticket"]]         = relationship(back_populates="reporter",
                                                                       foreign_keys="Ticket.reporter_id")
    comments:            Mapped[list["Comment"]]        = relationship(back_populates="author")
    notifications:       Mapped[list["Notification"]]   = relationship(back_populates="recipient")
```

### 1.3 Project & ProjectMember Models
```python
# app/models/project.py
import uuid, enum
from sqlalchemy import String, Text, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship, mapped_column, Mapped
from app.models.base import Base, TimestampMixin

class ProjectRole(str, enum.Enum):
    OWNER   = "owner"
    ADMIN   = "admin"
    MEMBER  = "member"
    VIEWER  = "viewer"

class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id:          Mapped[uuid.UUID]  = mapped_column(primary_key=True, default=uuid.uuid4)
    name:        Mapped[str]        = mapped_column(String(255), nullable=False)
    key:         Mapped[str]        = mapped_column(String(10), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_active:   Mapped[bool]       = mapped_column(Boolean, default=True, nullable=False)
    owner_id:    Mapped[uuid.UUID]  = mapped_column(ForeignKey("users.id"), nullable=False)

    owner:   Mapped["User"]               = relationship(foreign_keys=[owner_id])
    members: Mapped[list["ProjectMember"]] = relationship(back_populates="project",
                                                           cascade="all, delete-orphan")
    tickets: Mapped[list["Ticket"]]        = relationship(back_populates="project",
                                                           cascade="all, delete-orphan")
    sprints: Mapped[list["Sprint"]]        = relationship(back_populates="project",
                                                           cascade="all, delete-orphan")

class ProjectMember(Base, TimestampMixin):
    __tablename__ = "project_members"

    id:         Mapped[uuid.UUID]   = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID]   = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"),
                                                      nullable=False, index=True)
    user_id:    Mapped[uuid.UUID]   = mapped_column(ForeignKey("users.id", ondelete="CASCADE"),
                                                      nullable=False, index=True)
    role:       Mapped[ProjectRole] = mapped_column(SAEnum(ProjectRole), nullable=False)

    project: Mapped["Project"] = relationship(back_populates="members")
    user:    Mapped["User"]    = relationship(back_populates="project_memberships")

    __table_args__ = (UniqueConstraint("project_id", "user_id"),)
```

### 1.4 Ticket Model
```python
# app/models/ticket.py
import uuid, enum
from sqlalchemy import String, Text, Integer, ForeignKey, Enum as SAEnum, Index
from sqlalchemy import event
from sqlalchemy.orm import relationship, mapped_column, Mapped
from app.models.base import Base, TimestampMixin

class TicketStatus(str, enum.Enum):
    BACKLOG      = "backlog"
    TODO         = "todo"
    IN_PROGRESS  = "in_progress"
    IN_REVIEW    = "in_review"
    DONE         = "done"

class TicketPriority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"

class TicketType(str, enum.Enum):
    STORY  = "story"
    BUG    = "bug"
    TASK   = "task"
    EPIC   = "epic"

class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"

    id:           Mapped[uuid.UUID]      = mapped_column(primary_key=True, default=uuid.uuid4)
    ticket_number:Mapped[int]            = mapped_column(Integer, nullable=False)  # per-project sequence
    project_id:   Mapped[uuid.UUID]      = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"),
                                                          nullable=False, index=True)
    sprint_id:    Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sprints.id", ondelete="SET NULL"))
    assignee_id:  Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reporter_id:  Mapped[uuid.UUID]      = mapped_column(ForeignKey("users.id", ondelete="CASCADE"),
                                                          nullable=False)
    title:        Mapped[str]            = mapped_column(String(500), nullable=False)
    description:  Mapped[str | None]     = mapped_column(Text)
    status:       Mapped[TicketStatus]   = mapped_column(SAEnum(TicketStatus),
                                                          default=TicketStatus.BACKLOG, nullable=False)
    priority:     Mapped[TicketPriority] = mapped_column(SAEnum(TicketPriority),
                                                          default=TicketPriority.MEDIUM, nullable=False)
    ticket_type:  Mapped[TicketType]     = mapped_column(SAEnum(TicketType),
                                                          default=TicketType.TASK, nullable=False)
    story_points: Mapped[int | None]
    order_index:  Mapped[int]            = mapped_column(Integer, default=0, nullable=False)
    is_deleted:   Mapped[bool]           = mapped_column(default=False, nullable=False)

    project:  Mapped["Project"]         = relationship(back_populates="tickets")
    sprint:   Mapped["Sprint | None"]   = relationship(back_populates="tickets")
    assignee: Mapped["User | None"]     = relationship(back_populates="assigned_tickets",
                                                        foreign_keys=[assignee_id])
    reporter: Mapped["User"]            = relationship(back_populates="created_tickets",
                                                        foreign_keys=[reporter_id])
    comments: Mapped[list["Comment"]]   = relationship(back_populates="ticket",
                                                        cascade="all, delete-orphan")
    history:  Mapped[list["TicketHistory"]] = relationship(back_populates="ticket",
                                                            cascade="all, delete-orphan")
    labels:   Mapped[list["Label"]]     = relationship(secondary="ticket_labels")

    __table_args__ = (
        Index("ix_tickets_project_status",  "project_id", "status"),
        Index("ix_tickets_sprint_status",   "sprint_id",  "status"),
        Index("ix_tickets_assignee_project","assignee_id","project_id"),
    )
```

### 1.5 Sprint Model
```python
# app/models/sprint.py
import uuid, enum
from datetime import date
from sqlalchemy import String, Text, Date, ForeignKey, Enum as SAEnum, Index
from sqlalchemy.orm import relationship, mapped_column, Mapped
from app.models.base import Base, TimestampMixin

class SprintStatus(str, enum.Enum):
    PLANNING   = "planning"
    ACTIVE     = "active"
    COMPLETED  = "completed"

class Sprint(Base, TimestampMixin):
    __tablename__ = "sprints"

    id:         Mapped[uuid.UUID]    = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID]    = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"),
                                                      nullable=False, index=True)
    name:       Mapped[str]          = mapped_column(String(255), nullable=False)
    goal:       Mapped[str | None]   = mapped_column(Text)
    status:     Mapped[SprintStatus] = mapped_column(SAEnum(SprintStatus),
                                                      default=SprintStatus.PLANNING, nullable=False)
    start_date: Mapped[date | None]
    end_date:   Mapped[date | None]

    project: Mapped["Project"]     = relationship(back_populates="sprints")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="sprint")
```

### 1.6 Comment Model
```python
# app/models/comment.py
import uuid
from sqlalchemy import Text, ForeignKey, Index
from sqlalchemy.orm import relationship, mapped_column, Mapped
from app.models.base import Base, TimestampMixin

class Comment(Base, TimestampMixin):
    __tablename__ = "comments"

    id:        Mapped[uuid.UUID]   = mapped_column(primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID]   = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"),
                                                    nullable=False, index=True)
    author_id: Mapped[uuid.UUID]   = mapped_column(ForeignKey("users.id", ondelete="CASCADE"),
                                                    nullable=False)
    body:      Mapped[str]         = mapped_column(Text, nullable=False)
    is_edited: Mapped[bool]        = mapped_column(default=False, nullable=False)

    ticket: Mapped["Ticket"] = relationship(back_populates="comments")
    author: Mapped["User"]   = relationship(back_populates="comments")
```

### 1.7 TicketHistory Model
```python
# app/models/ticket_history.py
import uuid
from sqlalchemy import String, JSON, ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped
from app.models.base import Base, TimestampMixin

class TicketHistory(Base, TimestampMixin):
    __tablename__ = "ticket_history"

    id:         Mapped[uuid.UUID]  = mapped_column(primary_key=True, default=uuid.uuid4)
    ticket_id:  Mapped[uuid.UUID]  = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"),
                                                    nullable=False, index=True)
    actor_id:   Mapped[uuid.UUID]  = mapped_column(ForeignKey("users.id"), nullable=False)
    action:     Mapped[str]        = mapped_column(String(100), nullable=False)
    field_name: Mapped[str | None] = mapped_column(String(100))
    old_value:  Mapped[dict | None] = mapped_column(JSON)
    new_value:  Mapped[dict | None] = mapped_column(JSON)

    ticket: Mapped["Ticket"] = relationship(back_populates="history")
    actor:  Mapped["User"]   = relationship()
```

---

## 2. Alembic Migration Workflow

```bash
# Create a new migration (auto-detect from model changes)
alembic revision --autogenerate -m "add_ticket_full_text_search"

# Apply all pending migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1

# Show current migration state
alembic current

# Show migration history
alembic history --verbose
```

### 2.1 Example Migration — Full-Text Search Index
```python
# alembic/versions/0002_add_fts_index.py
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Add tsvector column maintained by trigger
    op.execute("""
        ALTER TABLE tickets
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(title,'')), 'A') ||
            setweight(to_tsvector('english', coalesce(description,'')), 'B')
        ) STORED;
    """)
    op.execute("""
        CREATE INDEX ix_tickets_search_vector
        ON tickets USING GIN(search_vector);
    """)

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tickets_search_vector;")
    op.execute("ALTER TABLE tickets DROP COLUMN IF EXISTS search_vector;")
```

---

## 3. Pydantic v2 Schemas

### 3.1 Common / Pagination
```python
# app/schemas/common.py
from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    meta: PaginationMeta

class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
```

### 3.2 Auth Schemas
```python
# app/schemas/auth.py
from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str       # min 8 chars validated in model validator

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

### 3.3 User Schemas
```python
# app/schemas/user.py
from pydantic import BaseModel, EmailStr
import uuid
from datetime import datetime
from app.models.user import UserRole

class UserResponse(BaseModel):
    model_config = {"from_attributes": True}   # replaces orm_mode=True in Pydantic v1

    id:         uuid.UUID
    email:      EmailStr
    username:   str
    full_name:  str
    role:       UserRole
    is_active:  bool
    avatar_url: str | None
    created_at: datetime

class UpdateProfileRequest(BaseModel):
    full_name:  str | None = None
    avatar_url: str | None = None
```

### 3.4 Ticket Schemas
```python
# app/schemas/ticket.py
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from app.models.ticket import TicketStatus, TicketPriority, TicketType

class CreateTicketRequest(BaseModel):
    title:        str             = Field(min_length=1, max_length=500)
    description:  str | None     = None
    priority:     TicketPriority  = TicketPriority.MEDIUM
    ticket_type:  TicketType      = TicketType.TASK
    assignee_id:  uuid.UUID | None = None
    sprint_id:    uuid.UUID | None = None
    story_points: int | None      = Field(default=None, ge=1, le=100)
    label_ids:    list[uuid.UUID] = []

class UpdateTicketRequest(BaseModel):
    title:        str | None          = Field(default=None, min_length=1, max_length=500)
    description:  str | None          = None
    priority:     TicketPriority | None = None
    assignee_id:  uuid.UUID | None    = None
    story_points: int | None          = Field(default=None, ge=1, le=100)

class TransitionRequest(BaseModel):
    status: TicketStatus

class TicketResponse(BaseModel):
    model_config = {"from_attributes": True}

    id:           uuid.UUID
    ticket_number:int
    project_id:   uuid.UUID
    sprint_id:    uuid.UUID | None
    title:        str
    description:  str | None
    status:       TicketStatus
    priority:     TicketPriority
    ticket_type:  TicketType
    story_points: int | None
    assignee_id:  uuid.UUID | None
    reporter_id:  uuid.UUID
    created_at:   datetime
    updated_at:   datetime
```

### 3.5 Sprint Schemas
```python
# app/schemas/sprint.py
from pydantic import BaseModel, Field
import uuid
from datetime import date, datetime
from app.models.sprint import SprintStatus

class CreateSprintRequest(BaseModel):
    name:       str             = Field(min_length=1, max_length=255)
    goal:       str | None      = None
    start_date: date | None     = None
    end_date:   date | None     = None

class UpdateSprintRequest(BaseModel):
    name:       str | None  = Field(default=None, min_length=1)
    goal:       str | None  = None
    start_date: date | None = None
    end_date:   date | None = None

class SprintResponse(BaseModel):
    model_config = {"from_attributes": True}

    id:         uuid.UUID
    project_id: uuid.UUID
    name:       str
    goal:       str | None
    status:     SprintStatus
    start_date: date | None
    end_date:   date | None
    created_at: datetime

class SprintBoardResponse(BaseModel):
    sprint: SprintResponse
    columns: dict[str, list["TicketResponse"]]   # status → tickets
    total_points: int
    completed_points: int
```

---

## 4. FastAPI Router Internals

### 4.1 Main App Factory
```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
from app.websocket.server import socket_app

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up: verifying DB connection...")
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title="Jira-Like API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)         # REST routes at /api/v1/...
app.mount("/ws", socket_app)           # WebSocket at /ws/...
```

### 4.2 Tickets Router
```python
# app/api/v1/tickets.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_db
from app.dependencies.auth import get_current_user, require_project_role
from app.models.project import ProjectRole
from app.schemas.ticket import CreateTicketRequest, UpdateTicketRequest, TransitionRequest, TicketResponse
from app.services.ticket_service import TicketService
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/tickets", tags=["Tickets"])
project_router = APIRouter(prefix="/projects/{project_id}/tickets", tags=["Tickets"])

@project_router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_project_role(ProjectRole.MEMBER, ProjectRole.ADMIN, ProjectRole.OWNER))]
)
async def create_ticket(
    project_id: uuid.UUID,
    body: CreateTicketRequest,
    db: AsyncSession           = Depends(get_db),
    current_user               = Depends(get_current_user),
    svc: TicketService         = Depends(),
) -> TicketResponse:
    return await svc.create(db, project_id, body, reporter_id=current_user.id)

@project_router.get("", response_model=PaginatedResponse[TicketResponse])
async def list_tickets(
    project_id: uuid.UUID,
    page: int           = 1,
    page_size: int      = 25,
    status_filter: str  = None,
    assignee_id: uuid.UUID = None,
    db: AsyncSession    = Depends(get_db),
    _user               = Depends(get_current_user),
    svc: TicketService  = Depends(),
):
    return await svc.list(db, project_id, page, page_size, status_filter, assignee_id)

@router.post("/{ticket_id}/transition", response_model=TicketResponse)
async def transition_ticket(
    ticket_id: uuid.UUID,
    body: TransitionRequest,
    db: AsyncSession   = Depends(get_db),
    current_user       = Depends(get_current_user),
    svc: TicketService = Depends(),
) -> TicketResponse:
    return await svc.transition(db, ticket_id, body.status, actor=current_user)
```

### 4.3 Ticket Service (Business Logic)
```python
# app/services/ticket_service.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid

from app.models.ticket import Ticket, TicketStatus, TicketHistory
from app.schemas.ticket import CreateTicketRequest, TicketResponse, UpdateTicketRequest
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.core.redis import get_redis

class TicketService:
    def __init__(self, redis=Depends(get_redis)):
        self.redis = redis

    async def create(
        self, db: AsyncSession, project_id: uuid.UUID,
        body: CreateTicketRequest, reporter_id: uuid.UUID
    ) -> Ticket:
        # Get next ticket number for project
        result = await db.execute(
            select(func.count()).select_from(Ticket).where(Ticket.project_id == project_id)
        )
        next_number = (result.scalar() or 0) + 1

        ticket = Ticket(
            project_id=project_id,
            ticket_number=next_number,
            reporter_id=reporter_id,
            **body.model_dump(exclude={"label_ids"}),
        )
        db.add(ticket)
        await db.flush()

        # Invalidate board cache
        if body.sprint_id:
            await self.redis.delete(f"board:{body.sprint_id}")

        return ticket

    async def transition(
        self, db: AsyncSession, ticket_id: uuid.UUID,
        new_status: TicketStatus, actor
    ) -> Ticket:
        ticket = await db.get(Ticket, ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        old_status = ticket.status
        ticket.status = new_status

        history = TicketHistory(
            ticket_id=ticket.id,
            actor_id=actor.id,
            action="status_changed",
            field_name="status",
            old_value={"status": old_status},
            new_value={"status": new_status},
        )
        db.add(history)
        await db.flush()

        if ticket.sprint_id:
            await self.redis.delete(f"board:{ticket.sprint_id}")

        return ticket

    async def list(
        self, db: AsyncSession, project_id: uuid.UUID,
        page: int, page_size: int,
        status_filter: str | None, assignee_id: uuid.UUID | None,
    ) -> PaginatedResponse:
        query = select(Ticket).where(
            Ticket.project_id == project_id,
            Ticket.is_deleted == False,
        )
        if status_filter:
            query = query.where(Ticket.status == status_filter)
        if assignee_id:
            query = query.where(Ticket.assignee_id == assignee_id)

        total_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar()

        items_result = await db.execute(
            query.order_by(Ticket.order_index)
                 .offset((page - 1) * page_size)
                 .limit(page_size)
        )
        items = items_result.scalars().all()

        return PaginatedResponse(
            data=[TicketResponse.model_validate(t) for t in items],
            meta=PaginationMeta(page=page, page_size=page_size, total=total,
                                total_pages=(total + page_size - 1) // page_size),
        )
```

---

## 5. Database Indexes

```sql
-- Tickets: most common query patterns
CREATE INDEX ix_tickets_project_status   ON tickets(project_id, status);
CREATE INDEX ix_tickets_sprint_status    ON tickets(sprint_id, status)  WHERE sprint_id IS NOT NULL;
CREATE INDEX ix_tickets_assignee_project ON tickets(assignee_id, project_id) WHERE assignee_id IS NOT NULL;
CREATE INDEX ix_tickets_order            ON tickets(project_id, order_index);

-- Full-text search
CREATE INDEX ix_tickets_search ON tickets USING GIN(search_vector);

-- Project members: role lookups
CREATE UNIQUE INDEX ix_project_members_unique ON project_members(project_id, user_id);
CREATE INDEX ix_project_members_user   ON project_members(user_id, project_id);

-- Comments: per-ticket listing
CREATE INDEX ix_comments_ticket ON comments(ticket_id, created_at);

-- Notifications: per-user unread count
CREATE INDEX ix_notifications_user_read ON notifications(recipient_id, is_read) WHERE is_read = FALSE;

-- Sprint: active sprint per project
CREATE UNIQUE INDEX ix_sprints_one_active ON sprints(project_id) WHERE status = 'active';
```

---

## 6. Redis Key Design

| Key Pattern | Type | TTL | Description |
|-------------|------|-----|-------------|
| `board:{sprint_id}` | Hash | 5 min | Sprint board: field=status, value=JSON ticket list |
| `project:{id}:active_sprint` | String | 10 min | Active sprint id for project |
| `user:{id}:profile` | Hash | 30 min | User profile fields |
| `project:{id}:members` | String | 15 min | JSON list of project members |
| `rt:{user_id}:{jti}` | String | 7 days | Refresh token validity — value="valid" |
| `rl:{ip}:auth` | String | 60 sec | Rate limit counter for auth endpoints |
| `rl:{ip}:api` | String | 60 sec | Rate limit counter for general endpoints |

---

## 7. Search Implementation

```sql
-- Full-text search query using tsvector GIN index
SELECT id, ticket_number, title, status, priority,
       ts_rank(search_vector, query) AS rank
FROM tickets,
     websearch_to_tsquery('english', :search_term) AS query
WHERE project_id = :project_id
  AND search_vector @@ query
  AND is_deleted = FALSE
ORDER BY rank DESC, created_at DESC
LIMIT :limit OFFSET :offset;
```

```python
# app/services/search_service.py
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

async def search_tickets(
    db: AsyncSession,
    project_id: uuid.UUID,
    query: str,
    page: int = 1,
    page_size: int = 25,
) -> list[dict]:
    sql = text("""
        SELECT id, ticket_number, title, status, priority,
               ts_rank(search_vector, q) AS rank
        FROM tickets,
             websearch_to_tsquery('english', :query) AS q
        WHERE project_id = :project_id
          AND search_vector @@ q
          AND is_deleted = FALSE
        ORDER BY rank DESC, created_at DESC
        LIMIT :limit OFFSET :offset
    """)
    result = await db.execute(sql, {
        "project_id": project_id,
        "query": query,
        "limit": page_size,
        "offset": (page - 1) * page_size,
    })
    return result.mappings().all()
```

---

## 8. Error Handling

### 8.1 Custom Exception Classes
```python
# app/core/exceptions.py
from fastapi import HTTPException

class AppException(HTTPException):
    def __init__(self, status_code: int, error_code: str, detail: str):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code

class NotFoundException(AppException):
    def __init__(self, resource: str, id):
        super().__init__(404, "NOT_FOUND", f"{resource} '{id}' not found")

class ForbiddenException(AppException):
    def __init__(self, message="Insufficient permissions"):
        super().__init__(403, "FORBIDDEN", message)

class ConflictException(AppException):
    def __init__(self, message: str):
        super().__init__(409, "CONFLICT", message)
```

### 8.2 Global Exception Handler
```python
# app/main.py — registered as exception_handler
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": f"https://api.yourdomain.com/errors/{exc.error_code.lower()}",
            "title": exc.error_code.replace("_", " ").title(),
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": str(request.url.path),
            "correlation_id": request.state.correlation_id,
        }
    )
```

---

## 9. Frontend Key Hooks (React + TypeScript — unchanged)

```typescript
// hooks/useTickets.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ticketsApi } from "../api/ticketsApi";
import { queryKeys } from "../queryKeys";

export const useTickets = (projectId: string, filters?: TicketFilters) => {
  return useQuery({
    queryKey: queryKeys.tickets(projectId, filters),
    queryFn: () => ticketsApi.list(projectId, filters),
    staleTime: 30_000,
  });
};

export const useTransitionTicket = (projectId: string) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ ticketId, status }: { ticketId: string; status: TicketStatus }) =>
      ticketsApi.transition(ticketId, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.tickets(projectId) });
    },
  });
};
```

---

## 10. Ticket Status Transition Rules

```python
# app/core/workflow.py
ALLOWED_TRANSITIONS: dict[TicketStatus, list[TicketStatus]] = {
    TicketStatus.BACKLOG:     [TicketStatus.TODO],
    TicketStatus.TODO:        [TicketStatus.IN_PROGRESS, TicketStatus.BACKLOG],
    TicketStatus.IN_PROGRESS: [TicketStatus.IN_REVIEW,  TicketStatus.TODO],
    TicketStatus.IN_REVIEW:   [TicketStatus.DONE,        TicketStatus.IN_PROGRESS],
    TicketStatus.DONE:        [TicketStatus.IN_PROGRESS],
}

def validate_transition(current: TicketStatus, target: TicketStatus) -> None:
    if target not in ALLOWED_TRANSITIONS.get(current, []):
        raise ConflictException(
            f"Cannot transition from '{current}' to '{target}'. "
            f"Allowed: {ALLOWED_TRANSITIONS[current]}"
        )
```
