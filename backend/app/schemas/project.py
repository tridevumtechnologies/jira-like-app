import re
import uuid
from datetime import datetime
from pydantic import BaseModel, field_validator


class CreateProjectRequest(BaseModel):
    name: str
    key: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_length(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) > 100:
            raise ValueError("name must be 1–100 characters")
        return v

    @field_validator("key")
    @classmethod
    def key_format(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r"^[A-Z]{2,10}$", v):
            raise ValueError("key must be 2–10 uppercase letters only (e.g. PROJ)")
        return v

    @field_validator("description")
    @classmethod
    def description_length(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 500:
            raise ValueError("description must be at most 500 characters")
        return v


class ProjectResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    key: str
    description: str | None
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
