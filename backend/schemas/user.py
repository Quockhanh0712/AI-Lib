# app/schemas/user.py

from pydantic import BaseModel, EmailStr, constr
from typing import Optional # Giữ lại Optional nếu UserBase/UserUpdate vẫn cần Optional fields
from datetime import datetime

# Import UserStatus Enum từ models
from db.models import UserStatus


class UserBase(BaseModel):
    member_code: constr(max_length=50)
    full_name: constr(max_length=255)
    email: Optional[EmailStr] = None
    phone_number: Optional[constr(max_length=20)] = None
    # status không có ở đây vì nó được quản lý bởi backend


class UserCreate(UserBase): # Admin tạo user mới - GIỮ LẠI (liên quan admin)
    # Có thể thêm các trường khác cần thiết khi tạo user
    pass


class UserUpdate(BaseModel): # Người dùng tự cập nhật tại máy hoặc Admin cập nhật - GIỮ LẠI (liên quan admin)
    full_name: Optional[constr(max_length=255)] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[constr(max_length=20)] = None
    # Admin có thể cập nhật status, user bình thường thì không
    # status: Optional[UserStatus] = None # Nếu Admin có thể cập nhật status qua endpoint này


class User(UserBase): # Schema đầy đủ cho User (khi lấy thông tin từ DB) - GIỮ LẠI
    id: int
    status: UserStatus # Sử dụng UserStatus Enum
    created_at: datetime
    updated_at: datetime # Model đã có onupdate

    class Config:
        from_attributes = True


# --- Schema cho phản hồi của endpoint lấy danh sách người đang ở thư viện (/attendance/in-library) ---
# Endpoint này trả về danh sách các AttendanceSession, mỗi session có thông tin user liên quan
class UserInLibraryResponse(BaseModel): # GIỮ LẠI
    id: int # Session ID
    user_id: int
    entry_time: str # Đã thay đổi thành str để khớp với định dạng trả về từ backend
    # exit_time: Optional[datetime] = None # Có thể thêm nếu cần hiển thị cả session đã thoát
    # duration_minutes: Optional[int] = None # Có thể thêm nếu cần hiển thị

    user_session_owner: User # Thông tin user liên quan (quan hệ trong model)

    class Config:
        from_attributes = True