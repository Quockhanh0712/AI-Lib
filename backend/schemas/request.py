# app/schemas/request.py
from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime

class RegistrationRequestBase(BaseModel):
    requested_member_code: constr(max_length=50)
    full_name: constr(max_length=255)
    email: Optional[EmailStr] = None
    phone_number: Optional[constr(max_length=20)] = None

class RegistrationRequestCreate(RegistrationRequestBase):
    pass

class RegistrationRequestProcess(BaseModel):
    status: constr(pattern="^(Approved|Rejected)$")

class RegistrationRequest(RegistrationRequestBase):
    request_time: datetime
    status: str
    processed_by_admin_id: Optional[int] = None
    processing_time: Optional[datetime] = None

    class Config:
        from_attributes = True