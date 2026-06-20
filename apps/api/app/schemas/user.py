"""User response and update schemas."""

from pydantic import BaseModel
from datetime import datetime
import uuid


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    avatar_url: str | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = None
    avatar_url: str | None = None
