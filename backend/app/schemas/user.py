import uuid
from datetime import datetime
from pydantic import BaseModel


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    full_name: str
    email: str
    address: str | None
    created_at: datetime
