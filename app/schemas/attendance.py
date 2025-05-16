# app/schemas/attendance.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# --- Schemas cho việc tạo và cập nhật AttendanceSession ---
class AttendanceSessionBase(BaseModel):
    pass # user_id sẽ được lấy từ context hoặc DB

class AttendanceSessionCreate(AttendanceSessionBase):
    user_id: int # Cần user_id khi tạo mới
    # entry_time sẽ được set là NOW() ở backend

class AttendanceSessionCheckout(BaseModel): # Dùng khi checkout
    # session_id và member_code sẽ là path/form params
    pass

# --- Schema để hiển thị AttendanceSession ---
class AttendanceSession(BaseModel):
    id: int
    user_id: int
    entry_time: datetime
    exit_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None

    class Config:
        from_attributes = True

# --- Schema đặc biệt để hiển thị danh sách người đang ở trong thư viện ---
class UserInLibrary(BaseModel):
    session_id: int # ID của phiên điểm danh
    member_code: str
    full_name: str
    entry_time: datetime

    class Config:
        from_attributes = True # Để Pydantic có thể đọc từ kết quả JOIN của SQLAlchemy