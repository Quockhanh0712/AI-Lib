# backend/schemas/attendance.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from schemas.user import User as UserSchema


class AttendanceSessionBase(BaseModel):
    user_id: int
    entry_time: datetime
class AttendanceSessionCreate(AttendanceSessionBase):
    pass # Kế thừa entry_time là datetime từ Base

class AttendanceSession(BaseModel):
    id: int
    user_id: int
    entry_time: str
    exit_time: Optional[str] = None
    duration_minutes: Optional[int] = None

    class Config:
        from_attributes = True

class UserInLibraryResponse(BaseModel):
    id: int
    user_id: int
    entry_time: str
    user_session_owner: UserSchema
    class Config:
        from_attributes = True