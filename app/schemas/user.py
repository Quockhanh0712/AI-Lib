# app/schemas/user.py

from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime

# Import UserStatus Enum từ models
from db.models import UserStatus


class UserBase(BaseModel):
    member_code: constr(max_length=50)
    full_name: constr(max_length=255)
    email: Optional[EmailStr] = None
    phone_number: Optional[constr(max_length=20)] = None
    # status không có ở đây vì nó được quản lý bởi backend


class UserCreate(UserBase): # Admin tạo user mới
    # Có thể thêm các trường khác cần thiết khi tạo user
    pass


class UserUpdate(BaseModel): # Người dùng tự cập nhật tại máy hoặc Admin cập nhật
    full_name: Optional[constr(max_length=255)] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[constr(max_length=20)] = None
    # Admin có thể cập nhật status, user bình thường thì không
    # status: Optional[UserStatus] = None # Nếu Admin có thể cập nhật status qua endpoint này


class User(UserBase): # Schema đầy đủ cho User (khi lấy thông tin từ DB)
    id: int
    status: UserStatus # Sử dụng UserStatus Enum
    created_at: datetime
    updated_at: datetime # Model đã có onupdate

    class Config:
        # orm_mode = True # Deprecated in Pydantic V2
        from_attributes = True # Cho phép Pydantic đọc dữ liệu từ ORM model


# --- Schema cho phản hồi của endpoint kiểm tra User (/users/{member_code}/check) ---
# Endpoint này chỉ trả về một số thông tin cơ bản sau khi kiểm tra thành công
class UserCheckResponse(BaseModel):
    id: int
    member_code: str
    full_name: str
    status: UserStatus # Trạng thái user

    class Config:
        from_attributes = True


# --- Schema cho phản hồi của endpoint nhận diện/xác minh khuôn mặt (/recognize_face) ---
# Endpoint này trả về success/message và thông tin user nếu thành công
class FaceRecognitionResponse(BaseModel):
    success: bool
    message: str
    user: Optional[UserCheckResponse] = None # Sử dụng UserCheckResponse schema cho thông tin user


# --- Schema cho phản hồi của endpoint lấy danh sách người đang ở thư viện (/attendance/in-library) ---
# Endpoint này trả về danh sách các AttendanceSession, mỗi session có thông tin user liên quan
class UserInLibraryResponse(BaseModel):
    id: int # Session ID
    user_id: int
    entry_time: datetime
    # exit_time: Optional[datetime] = None # Có thể thêm nếu cần hiển thị cả session đã thoát
    # duration_minutes: Optional[int] = None # Có thể thêm nếu cần hiển thị

    user_session_owner: User # Thông tin user liên quan (quan hệ trong model)

    class Config:
         from_attributes = True


# --- Schema cho phản hồi của endpoint đăng ký thành viên (/registration-requests/) ---
class RegistrationRequestResponse(BaseModel):
    message: str
    requested_member_code: str
    full_name: str
    photo_received: bool
    # Có thể thêm ID yêu cầu đăng ký nếu backend trả về


# --- Schema cho phản hồi của endpoint profile (/users/{member_code}/profile) ---
# Có thể sử dụng lại schema User đầy đủ nếu endpoint trả về tất cả thông tin
class UserProfileResponse(User):
    pass # Kế thừa tất cả các trường từ schema User

# --- Schema cho lịch sử chuyên cần (/users/{member_code}/attendance-history/completed) ---
# Cần định nghĩa schema cho AttendanceSession khi exit_time is not null
# Ví dụ:
class CompletedAttendanceSession(BaseModel):
    id: int
    user_id: int
    entry_time: datetime
    exit_time: datetime
    duration_minutes: Optional[int] = None # Có thể null nếu tính duration ở frontend

    class Config:
         from_attributes = True

