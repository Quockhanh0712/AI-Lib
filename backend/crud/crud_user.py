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

def create_user(
    db: Session,
    user: user_schemas.UserCreate,
    status: str = "Approved",
    face_embedding_data: Optional[str] = None,
) -> models.User:
    """
    Tạo một user mới, bao gồm cả thông tin embedding (dạng text thô) và đường dẫn ảnh.
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
        print(f"DEBUG CRUD: face_embedding_data received for saving: {face_embedding_data[:200]}...")

        db_face_embedding = db.query(models.FaceEmbedding).filter(models.FaceEmbedding.user_id == db_user.id).first()

        if db_face_embedding:
            db_face_embedding.embedding = face_embedding_data
            print(f"DEBUG CRUD: Updating existing embedding for user {db_user.id}: {db_face_embedding.embedding[:200]}...")
        else:
            db_face_embedding = models.FaceEmbedding(
                user_id=db_user.id,
                embedding=face_embedding_data
            )
            db.add(db_face_embedding)
            print(f"DEBUG CRUD: Adding new embedding for user {db_user.id}: {db_face_embedding.embedding[:200]}...")

        db.commit()
        db.refresh(db_face_embedding)

    return db_user

def update_user_profile(
    db: Session, 
    db_user: models.User, 
    user_update: user_schemas.UserUpdate,
    face_embedding_text: Optional[str] = None,
) -> models.User:
    """
    Cập nhật thông tin profile của người dùng, bao gồm cả embedding.
    """
    update_data = user_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_user, key, value)

    if face_embedding_text is not None:
        db_user.face_embedding = face_embedding_text

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
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