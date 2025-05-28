# app/crud/crud_user.py
from sqlalchemy.orm import Session
from db import models
from schemas import user as user_schemas
from typing import List, Optional
import json
import numpy as np # THÊM DÒNG NÀY ĐỂ SỬ DỤNG NUMPY

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_member_code(db: Session, member_code: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.member_code == member_code).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(
    db: Session,
    user: user_schemas.UserCreate,
    status: str = "Approved",
    face_embedding_data: Optional[str] = None, # <-- Mong đợi một CHUỖI JSON
) -> models.User:
    """
    Tạo một user mới, bao gồm cả thông tin embedding (dạng chuỗi JSON).
    """
    db_user = models.User(
        member_code=user.member_code,
        full_name=user.full_name,
        email=user.email,
        phone_number=user.phone_number,
        status=status,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    if face_embedding_data is not None:
        # Loại bỏ toàn bộ khối kiểm tra isinstance() và chuyển đổi
        # Chỉ cần gán trực tiếp chuỗi JSON đã nhận
        print(f"DEBUG CRUD: face_embedding_data received for saving (JSON): {face_embedding_data[:200]}...")

        db_face_embedding = db.query(models.FaceEmbedding).filter(models.FaceEmbedding.user_id == db_user.id).first()

        if db_face_embedding:
            db_face_embedding.embedding = face_embedding_data # Gán trực tiếp chuỗi JSON
            print(f"DEBUG CRUD: Updating existing embedding for user {db_user.id} (JSON): {db_face_embedding.embedding[:200]}...")
        else:
            db_face_embedding = models.FaceEmbedding(
                user_id=db_user.id,
                embedding=face_embedding_data # Gán trực tiếp chuỗi JSON
            )
            db.add(db_face_embedding)
            print(f"DEBUG CRUD: Adding new embedding for user {db_user.id} (JSON): {db_face_embedding.embedding[:200]}...")

        db.commit()
        db.refresh(db_face_embedding)

    return db_user

# Làm tương tự cho update_user_profile
def update_user_profile(
    db: Session,
    db_user: models.User,
    user_update: user_schemas.UserUpdate,
    face_embedding_text: Optional[str] = None, # <-- Mong đợi một CHUỖI JSON
) -> models.User:
    """
    Cập nhật thông tin profile của người dùng, bao gồm cả embedding (dạng chuỗi JSON).
    """
    update_data = user_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_user, key, value)

    if face_embedding_text is not None:
        # Loại bỏ toàn bộ khối kiểm tra isinstance() và chuyển đổi
        existing_face_embedding = db.query(models.FaceEmbedding).filter(
            models.FaceEmbedding.user_id == db_user.id
        ).first()

        if existing_face_embedding:
            existing_face_embedding.embedding = face_embedding_text # Gán trực tiếp chuỗi JSON
        else:
            new_face_embedding = models.FaceEmbedding(
                user_id=db_user.id,
                embedding=face_embedding_text # Gán trực tiếp chuỗi JSON
            )
            db.add(new_face_embedding)

    try:
        db.commit()
        db.refresh(db_user)
        if existing_face_embedding:
            db.refresh(existing_face_embedding)
        elif 'new_face_embedding' in locals():
            db.refresh(new_face_embedding)

    except Exception as e:
        db.rollback()
        print(f"Lỗi khi cập nhật profile hoặc embedding: {e}")
        raise

    return db_user

def update_user_status_by_admin(db: Session, db_user: models.User, new_status: str) -> models.User:
    """Admin cập nhật trạng thái của user (ví dụ: 'Approved', 'Inactive')."""
    if new_status not in ["Approved", "Inactive"]:
        raise ValueError("Invalid status for user")
    db_user.status = new_status
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> Optional[models.User]:
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user