# app/schemas/admin.py
from pydantic import BaseModel, constr
from typing import Optional

class AdminUserBase(BaseModel):
    username: constr(max_length=100)
    full_name: Optional[constr(max_length=255)] = None
    contact_info: Optional[constr(max_length=255)] = None

class AdminUserCreate(AdminUserBase):
    password: str

class AdminUserLogin(BaseModel):
    username: str
    password: str

class AdminUser(AdminUserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True