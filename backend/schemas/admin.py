# app/schemas/admin.py
from pydantic import BaseModel, constr
from typing import Optional

class AdminUserBase(BaseModel):
    username: constr(max_length=100)
    full_name: Optional[constr(max_length=255)] = None
    contact_info: Optional[constr(max_length=255)] = None

class AdminUserCreate(AdminUserBase):
    password: str # Mật khẩu gốc khi tạo

class AdminUserLogin(BaseModel): # Schema này vẫn được OAuth2PasswordRequestForm sử dụng để lấy username/password
    username: str
    password: str

class AdminUser(AdminUserBase): # Dùng để hiển thị thông tin Admin (không có password)
    id: int
    is_active: bool

    class Config:
        from_attributes = True

# Bỏ Token và TokenData vì không dùng JWT nữa
# class Token(BaseModel):
#     access_token: str
#     token_type: str

# class TokenData(BaseModel):
#     username: Optional[str] = None