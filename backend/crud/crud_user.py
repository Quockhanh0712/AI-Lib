# app/crud/crud_user.py
from sqlalchemy.orm import Session
from db import models
from schemas import user as user_schemas # Vẫn cần vì UserCreate/UserUpdate có thể được dùng ở các hàm khác
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
    face_embedding_data: Optional[str] = None, # Vẫn là list of lists từ admin_endpoints
    photo_path: Optional[str] = None
) -> models.User:
    """
    Tạo một user mới, bao gồm cả thông tin embedding (dạng text thô) và đường dẫn ảnh.
    """
    # 1. Tạo đối tượng User
    db_user = models.User(
        member_code=user.member_code,
        full_name=user.full_name,
        email=user.email,
        phone_number=user.phone_number,
        status=status,
        # photo_path = photo_path # Nếu bạn đã thêm photo_path trực tiếp vào User model
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # 2. Nếu có dữ liệu embedding, tạo hoặc cập nhật FaceEmbedding
    if face_embedding_data is not None:
        # DEBUG HERE: Kiểm tra face_embedding_data ngay trước khi lưu
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
    user_update: user_schemas.UserUpdate, # Schema chứa các trường muốn update
    face_embedding_text: Optional[str] = None, # Tham số mới cho embedding
    photo_path: Optional[str] = None # Tham số mới cho photo path
) -> models.User:
    """
    Cập nhật thông tin profile của người dùng, bao gồm cả embedding và photo path.
    """
    # Lấy dữ liệu từ schema user_update, bỏ qua các trường không được set
    update_data = user_update.model_dump(exclude_unset=True) # Dùng .model_dump() cho Pydantic v2+

    for key, value in update_data.items():
        # Cập nhật các trường thông tin cơ bản
        setattr(db_user, key, value)

    # Cập nhật face_embedding nếu được cung cấp
    if face_embedding_text is not None: # Dùng 'is not None' để phân biệt với chuỗi rỗng
        db_user.face_embedding = face_embedding_text

    db.add(db_user) # Có thể không cần nếu db_user đã được theo dõi bởi session
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