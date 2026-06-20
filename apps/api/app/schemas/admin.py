from pydantic import BaseModel


class UserListItem(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: str
    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: list[UserListItem]
    total: int
    page: int
    per_page: int


class UserUpdateRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None


class SystemHealthResponse(BaseModel):
    status: str
    database: str
    timestamp: str


class SystemStatsResponse(BaseModel):
    total_users: int
    total_interviews: int
    total_candidates: int
    active_sessions: int
