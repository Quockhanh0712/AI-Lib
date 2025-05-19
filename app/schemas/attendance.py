# app/schemas/attendance.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Import User schema để sử dụng trong UserInLibraryResponse
# Đảm bảo đường dẫn import này đúng với cấu trúc thư mục của bạn
from schemas.user import User

class AttendanceSessionBase(BaseModel):
    user_id: int
    entry_time: datetime
    exit_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None

class AttendanceSessionCreate(AttendanceSessionBase):
    pass # Khi tạo, entry_time sẽ được set tự động, exit_time là None

class AttendanceSession(AttendanceSessionBase):
    id: int # Session ID

    class Config:
        from_attributes = True


# --- Schema cho danh sách người đang ở trong thư viện ---
# Điều này sẽ trả về Session ID và thông tin đầy đủ của User liên quan
class UserInLibraryResponse(BaseModel):
    id: int # ID của Attendance Session
    user_id: int
    entry_time: datetime
    # exit_time: Optional[datetime] = None # Có thể thêm nếu cần hiển thị cả session đã thoát
    # duration_minutes: Optional[int] = None # Có thể thêm nếu cần hiển thị

    user_session_owner: User # Thông tin chi tiết của user (được load qua quan hệ trong model)

    class Config:
        from_attributes = True

# --- Schema cho lịch sử chuyên cần đã hoàn thành ---
class CompletedAttendanceSession(BaseModel):
    id: int
    user_id: int
    entry_time: datetime
    exit_time: datetime
    duration_minutes: Optional[int] = None # Có thể null nếu tính duration ở frontend

    class Config:
         from_attributes = True

