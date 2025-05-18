# app/crud/crud_user.py
from sqlalchemy.orm import Session
from db import models
from schemas import user as user_schemas
from typing import List, Optional

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_member_code(db: Session, member_code: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.member_code == member_code).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: user_schemas.UserCreate, status: str = "Approved") -> models.User:
    """
    Tạo một user mới. Mặc định status là 'Approved' nếu Admin tạo trực tiếp.
    Khi phê duyệt request, status này sẽ được set là 'Approved' một cách tường minh.
    """
    db_user = models.User(
        member_code=user.member_code,
        full_name=user.full_name,
        email=user.email,
        phone_number=user.phone_number,
        status=status
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_profile(db: Session, db_user: models.User, user_update: user_schemas.UserUpdate) -> models.User:
    """Hàm này nhận đối tượng db_user đã được lấy từ DB để cập nhật."""
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_status_by_admin(db: Session, db_user: models.User, new_status: str) -> models.User:
    """Admin cập nhật trạng thái của user (ví dụ: 'Approved', 'Inactive')."""
    if new_status not in ["Approved", "Inactive"]: # Đảm bảo status hợp lệ
        raise ValueError("Invalid status for user")
    db_user.status = new_status
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> Optional[models.User]:
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user) # SQLAlchemy sẽ xử lý cascade delete cho face_embeddings và attendance_sessions
        db.commit()
    return db_user

# Các hàm cho FaceEmbedding sẽ được thêm sau khi tích hợp AI
# Ví dụ:
# def create_user_face_embedding(db: Session, user_id: int, embedding_vector: bytes) -> models.FaceEmbedding:
#     db_embedding = models.FaceEmbedding(user_id=user_id, embedding_vector=embedding_vector)
#     db.add(db_embedding)
#     db.commit()
#     db.refresh(db_embedding)
#     return db_embedding

# def get_user_face_embeddings(db: Session, user_id: int) -> List[models.FaceEmbedding]:
#     return db.query(models.FaceEmbedding).filter(models.FaceEmbedding.user_id == user_id).all()