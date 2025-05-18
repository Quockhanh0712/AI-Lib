# app/schemas/user.py
from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    member_code: constr(max_length=50)
    full_name: constr(max_length=255)
    email: Optional[EmailStr] = None
    phone_number: Optional[constr(max_length=20)] = None

class UserCreate(UserBase): # Admin tạo user mới
    pass # status sẽ được set ở backend

class UserUpdate(BaseModel): # Người dùng tự cập nhật tại máy
    full_name: Optional[constr(max_length=255)] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[constr(max_length=20)] = None

class User(UserBase): # Hiển thị thông tin user
    id: int
    status: str
    created_at: datetime
    updated_at: datetime # Model đã có onupdate

    class Config:
        from_attributes = True