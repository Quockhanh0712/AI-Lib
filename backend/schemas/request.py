# app/schemas/request.py
from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime

class RegistrationRequestBase(BaseModel):
    requested_member_code: constr(max_length=50)
    full_name: constr(max_length=255)
    email: Optional[EmailStr] = None
    phone_number: Optional[constr(max_length=20)] = None
    photo_path: constr(max_length=255) # Backend sẽ xử lý lưu ảnh và nhận path này từ frontend

class RegistrationRequestCreate(RegistrationRequestBase):
    pass

class RegistrationRequestProcess(BaseModel): # Dùng khi Admin xử lý yêu cầu
    status: constr(pattern="^(Approved|Rejected)$") # Chỉ chấp nhận 'Approved' hoặc 'Rejected'

class RegistrationRequest(RegistrationRequestBase): # Dùng để hiển thị
    id: int
    request_time: datetime
    status: str
    processed_by_admin_id: Optional[int] = None
    processing_time: Optional[datetime] = None

    class Config:
        from_attributes = True