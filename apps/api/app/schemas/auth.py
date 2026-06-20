"""Auth request/response schemas."""

from typing import Literal

from pydantic import BaseModel, EmailStr, field_validator

from app.core.validation import sanitize_string


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Literal["interviewer", "candidate"] = "interviewer"

    @field_validator("full_name")
    @classmethod
    def sanitize_full_name(cls, v: str) -> str:
        return sanitize_string(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
