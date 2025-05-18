# app/db/models.py

from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean, ForeignKey, Text, LargeBinary, Enum # Import Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# SỬA LỖI: Import database module thay vì Base trực tiếp để tránh circular import
from . import database # Import the database module

import enum # Import enum module
from datetime import datetime # Import datetime

# Định nghĩa Enum cho trạng thái người dùng (Sử dụng lại cho cả User và RegistrationRequest)
class UserStatus(enum.Enum):
    Pending = "Pending"
    Approved = "Approved"
    Rejected = "Rejected"
    Inactive = "Inactive"

# Định nghĩa model cho bảng AdminUser
class AdminUser(database.Base): # Kế thừa từ database.Base
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    contact_info = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    registration_requests_processed = relationship("RegistrationRequest", back_populates="processor")

# Định nghĩa model cho bảng User
class User(database.Base): # Kế thừa từ database.Base
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    member_code = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True, index=True)
    phone_number = Column(String(20), nullable=True)
    # Sử dụng Enum cho status
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.Pending)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    face_embeddings = relationship("FaceEmbedding", back_populates="owner", cascade="all, delete-orphan")
    attendance_sessions = relationship("AttendanceSession", back_populates="user_session_owner", cascade="all, delete-orphan")

# Định nghĩa model cho bảng FaceEmbedding
class FaceEmbedding(database.Base): # Kế thừa từ database.Base
    __tablename__ = "face_embeddings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    embedding_vector = Column(LargeBinary, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    owner = relationship("User", back_populates="face_embeddings")

# Định nghĩa model cho bảng AttendanceSession
class AttendanceSession(database.Base): # Kế thừa từ database.Base
    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    entry_time = Column(TIMESTAMP, nullable=False, server_default=func.now()) # Thêm server_default
    exit_time = Column(TIMESTAMP, nullable=True)
    duration_minutes = Column(Integer, nullable=True)

    user_session_owner = relationship("User", back_populates="attendance_sessions")

# Định nghĩa model cho bảng RegistrationRequest
class RegistrationRequest(database.Base): # Kế thừa từ database.Base
    __tablename__ = "registration_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    requested_member_code = Column(String(50), nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    photo_path = Column(String(255), nullable=False)
    request_time = Column(TIMESTAMP, server_default=func.now())
    # Sử dụng Enum cho status
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.Pending)
    processed_by_admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
    processing_time = Column(TIMESTAMP, nullable=True)

    processor = relationship("AdminUser", back_populates="registration_requests_processed")

