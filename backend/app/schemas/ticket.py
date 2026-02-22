import uuid
from datetime import datetime
from pydantic import BaseModel, field_validator

from app.models.ticket import TicketPriority, TicketStatus, TicketType


class CreateTicketRequest(BaseModel):
    title: str
    ticket_type: TicketType
    priority: TicketPriority
    description: str | None = None
    assignee_id: uuid.UUID | None = None

    @field_validator("title")
    @classmethod
    def title_length(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) > 255:
            raise ValueError("title must be 1–255 characters")
        return v


class UpdateTicketRequest(BaseModel):
    """All fields optional — partial update."""
    title: str | None = None
    ticket_type: TicketType | None = None
    priority: TicketPriority | None = None
    status: TicketStatus | None = None
    description: str | None = None
    assignee_id: uuid.UUID | None = None
    story_points: int | None = None

    @field_validator("title")
    @classmethod
    def title_length(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v or len(v) > 255:
                raise ValueError("title must be 1–255 characters")
        return v


class TicketResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    key: str
    title: str
    ticket_type: TicketType
    priority: TicketPriority
    status: TicketStatus
    description: str | None
    assignee_id: uuid.UUID | None
    reporter_id: uuid.UUID
    project_id: uuid.UUID
    story_points: int | None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
