from __future__ import annotations

from pydantic import BaseModel, EmailStr


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PendingApprovalOut(BaseModel):
    request_id: int
    user_id: int
    user_email: str
    from_stage_id: int
    to_stage_id: int | None
    type: str
    created_at: str


class ApproveRequestIn(BaseModel):
    comment: str | None = None


class ApproveResponseOut(BaseModel):
    request_id: int
    status: str
    user_id: int
    from_stage_id: int
    to_stage_id: int | None