"""Integration schemas."""
from typing import List, Optional

from pydantic import BaseModel


class SlackConnectRequest(BaseModel):
    webhook_url: str
    channel_name: str
    events: List[str]


class SlackIntegrationResponse(BaseModel):
    id: str
    channel_name: str
    events: list
    is_active: bool
    created_at: Optional[str] = None


class TeamsConnectRequest(BaseModel):
    webhook_url: str
    channel_name: str
    events: List[str]


class TeamsIntegrationResponse(BaseModel):
    id: str
    channel_name: str
    events: list
    is_active: bool
    created_at: Optional[str] = None
