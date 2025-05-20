# app/crud/crud_admin.py
from sqlalchemy.orm import Session
from app.db import models
from app.schemas import admin as admin_schemas
from typing import Optional
# Bỏ các import liên quan đến passlib, datetime cho JWT, jose, settings cho JWT

def get_admin_by_username(db: Session, username: str) -> Optional[models.AdminUser]:
    return db.query(models.AdminUser).filter(models.AdminUser.username == username).first()

def create_admin_user(db: Session, admin: admin_schemas.AdminUserCreate) -> models.AdminUser:
    """Tạo admin user mới, lưu mật khẩu gốc (KHÔNG AN TOÀN)."""
    db_admin = models.AdminUser(
        username=admin.username,
        password=admin.password, # <<<< LƯU MẬT KHẨU GỐC
        full_name=admin.full_name,
        contact_info=admin.contact_info
    )
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin

def authenticate_admin(db: Session, username: str, password_input: str) -> Optional[models.AdminUser]:
    """Xác thực admin bằng cách so sánh password gốc (KHÔNG AN TOÀN)."""
    admin = get_admin_by_username(db, username)
    if not admin:
        return None
    # So sánh trực tiếp mật khẩu gốc
    if admin.password != password_input: # <<<< SO SÁNH MẬT KHẨU GỐC
        return None
    if not admin.is_active:
        return None
    return admin