# app/schemas/user.py

from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime
from db.models import UserStatus


class UserBase(BaseModel):
    member_code: constr(max_length=50)
    full_name: constr(max_length=255)
    email: Optional[EmailStr] = None
    phone_number: Optional[constr(max_length=20)] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    full_name: Optional[constr(max_length=255)] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[constr(max_length=20)] = None



class User(UserBase):
    id: int
    status: UserStatus
    created_at: datetime
    updated_at: datetime # Model đã có onupdate

    class Config:
        from_attributes = True

class UserInLibraryResponse(BaseModel):
    id: int
    user_id: int
    entry_time: str

    user_session_owner: User

    class Config:
        from_attributes = True