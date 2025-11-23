from pydantic import BaseModel
from typing import Optional, Any, List


class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class User(BaseModel):
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    provider: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
   # 简单管理：目前只允许改 name，如果你想以后加备注、角色，都可以往这里加字段