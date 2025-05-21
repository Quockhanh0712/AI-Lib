# app/crud/crud_admin.py
from sqlalchemy.orm import Session
from db import models
from schemas import admin as admin_schemas
from typing import Optional
from passlib.context import CryptContext # Thêm import này

# Khởi tạo context cho việc băm mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_admin_by_username(db: Session, username: str) -> Optional[models.AdminUser]:
    return db.query(models.AdminUser).filter(models.AdminUser.username == username).first()

def create_admin_user(db: Session, admin: admin_schemas.AdminUserCreate) -> models.AdminUser:
    """Tạo admin user mới, băm mật khẩu trước khi lưu."""
    db_admin = models.AdminUser(
        username=admin.username,
        # ĐÃ SỬA: Băm mật khẩu và lưu vào password_hash
        password_hash=pwd_context.hash(admin.password), 
        full_name=admin.full_name,
        contact_info=admin.contact_info
    )
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin

def authenticate_admin(db: Session, username: str, password_input: str) -> Optional[models.AdminUser]:
    """Xác thực admin bằng cách so sánh password đầu vào với password_hash đã băm."""
    admin = get_admin_by_username(db, username)
    if not admin:
        return None
    
    # ĐÃ SỬA: Sử dụng pwd_context.verify để so sánh mật khẩu đầu vào với hash đã lưu
    if not pwd_context.verify(password_input, admin.password_hash): 
        return None
        
    if not admin.is_active:
        return None
        
    return admin
