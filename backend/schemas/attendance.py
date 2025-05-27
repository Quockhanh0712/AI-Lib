# backend/schemas/attendance.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from schemas.user import User as UserSchema # Import User schema

# Base Schema cho AttendanceSession
# Dùng cho việc tạo hoặc xử lý nội bộ khi thời gian là datetime object
class AttendanceSessionBase(BaseModel):
    user_id: int
    entry_time: datetime # Giữ là datetime cho mục đích xử lý Python

# Schema để tạo một bản ghi AttendanceSession (khi check-in)
class AttendanceSessionCreate(AttendanceSessionBase):
    pass # Kế thừa entry_time là datetime từ Base

# Schema cho bản ghi AttendanceSession hoàn chỉnh từ DB
# *** QUAN TRỌNG: Đây là schema dùng làm response_model, nên thời gian sẽ là str ***
class AttendanceSession(BaseModel): # <-- KHÔNG KẾ THỪA AttendanceSessionBase nữa
    id: int
    user_id: int # <-- Thêm lại trường user_id
    entry_time: str # <-- THAY datetime THÀNH str
    exit_time: Optional[str] = None # <-- THAY Optional[datetime] THÀNH Optional[str]
    duration_minutes: Optional[int] = None # Có thể là NULL

    class Config:
        from_attributes = True # Dùng cho Pydantic v2 trở lên (vẫn cần để ánh xạ từ model DB)

# Schema cho Response khi lấy danh sách người dùng đang ở trong thư viện
# Đây là schema sẽ được trả về từ GET /machine/current-members/
class UserInLibraryResponse(BaseModel):
    id: int # Đây là ID của bản ghi attendance_session
    user_id: int
    entry_time: str # <-- GIỮ LÀ str để khớp với định dạng trả về
    user_session_owner: UserSchema # Thông tin chi tiết của người dùng

    class Config:
        from_attributes = True