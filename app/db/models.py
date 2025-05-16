# app/db/models.py
from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean, ForeignKey, Text, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False) # <<<< ĐÃ THAY ĐỔI TỪ password_hash
    full_name = Column(String(255), nullable=True)
    contact_info = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    registration_requests_processed = relationship("RegistrationRequest", back_populates="processor")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    member_code = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True, index=True)
    phone_number = Column(String(20), nullable=True)
    status = Column(String(20), nullable=False, default='Approved')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    face_embeddings = relationship("FaceEmbedding", back_populates="owner", cascade="all, delete-orphan")
    attendance_sessions = relationship("AttendanceSession", back_populates="user_session_owner", cascade="all, delete-orphan")

class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    embedding_vector = Column(LargeBinary, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    owner = relationship("User", back_populates="face_embeddings")

class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    entry_time = Column(TIMESTAMP, nullable=False)
    exit_time = Column(TIMESTAMP, nullable=True)
    duration_minutes = Column(Integer, nullable=True)

    user_session_owner = relationship("User", back_populates="attendance_sessions")

class RegistrationRequest(Base):
    __tablename__ = "registration_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    requested_member_code = Column(String(50), nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    photo_path = Column(String(255), nullable=False)
    request_time = Column(TIMESTAMP, server_default=func.now())
    status = Column(String(20), nullable=False, default='Pending')
    processed_by_admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
    processing_time = Column(TIMESTAMP, nullable=True)

    processor = relationship("AdminUser", back_populates="registration_requests_processed")