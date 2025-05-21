# app/db/models.py

from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean, ForeignKey, Text, LargeBinary # Bỏ import Enum ở đây
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Enum as SQLEnum # Import Enum từ sqlalchemy.types và đổi tên để tránh xung đột

# Import database module để Base được định nghĩa ở đó
# Sử dụng import tương đối
from .database import Base # Quan trọng: Import Base từ database module

import enum # Import enum module
from datetime import datetime # Import datetime

# Định nghĩa Enum cho trạng thái người dùng
class UserStatus(str, enum.Enum): # Kế thừa từ str và Enum để lưu giá trị string trong DB
    Pending = "Pending"
    Approved = "Approved"
    Rejected = "Rejected"
    Inactive = "Inactive"


# Định nghĩa model cho bảng AdminUser
class AdminUser(Base): # Kế thừa từ Base
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    # Đổi tên cột từ 'password' sang 'password_hash' để khớp với file .sql (dựa trên INSERT)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    contact_info = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    registration_requests_processed = relationship("RegistrationRequest", back_populates="processor")

# Định nghĩa model cho bảng User
class User(Base): # Kế thừa từ Base
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    member_code = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True, index=True)
    phone_number = Column(String(20), nullable=True)
    # Sử dụng sqlalchemy.types.Enum để ánh xạ Python Enum sang String trong DB
    # native_enum=False cần thiết cho SQLite để lưu dưới dạng VARCHAR thay vì kiểu Enum riêng của DB
    status = Column(SQLEnum(UserStatus, native_enum=False), nullable=False, default=UserStatus.Approved) # Sử dụng Enum object làm default
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    face_embeddings = relationship("FaceEmbedding", back_populates="owner", cascade="all, delete-orphan")
    attendance_sessions = relationship("AttendanceSession", back_populates="user_session_owner", cascade="all, delete-orphan")

# Định nghĩa model cho bảng FaceEmbedding
class FaceEmbedding(Base): # Kế thừa từ Base
    __tablename__ = "face_embeddings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # Thêm unique=True cho user_id để khớp với file .sql
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    # Thay đổi từ LargeBinary sang 3 cột Text để khớp với file .sql
    embedding1 = Column(Text, nullable=True) # Giả định có thể NULL nếu chưa có embedding
    embedding2 = Column(Text, nullable=True)
    embedding3 = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    # Thêm cột updated_at để khớp với file .sql
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


    owner = relationship("User", back_populates="face_embeddings")

# Định nghĩa model cho bảng AttendanceSession
class AttendanceSession(Base): # Kế thừa từ Base
    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    entry_time = Column(TIMESTAMP, nullable=False, server_default=func.now())
    exit_time = Column(TIMESTAMP, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    
    user_session_owner = relationship("User", back_populates="attendance_sessions")

# Định nghĩa model cho bảng RegistrationRequest
class RegistrationRequest(Base): # Kế thừa từ database.Base
    __tablename__ = "registration_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    requested_member_code = Column(String(50), nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    photo_path = Column(String(255), nullable=False)
    request_time = Column(TIMESTAMP, server_default=func.now())
    # Sử dụng sqlalchemy.types.Enum để ánh xạ Python Enum sang String trong DB
    status = Column(SQLEnum(UserStatus, native_enum=False), nullable=False, default=UserStatus.Pending) # Sử dụng Enum object làm default
    processed_by_admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
    processing_time = Column(TIMESTAMP, nullable=True)

    processor = relationship("AdminUser", back_populates="registration_requests_processed")

