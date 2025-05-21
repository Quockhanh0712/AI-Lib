# app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings # Import đối tượng settings từ config.py

# Lấy chuỗi kết nối DB từ cấu hình
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Tạo SQLAlchemy engine
# ĐÃ SỬA: Thêm connect_args để đảm bảo mã hóa UTF-8 cho kết nối MySQL
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"charset": "utf8mb4"}, # RẤT QUAN TRỌNG: Đảm bảo kết nối dùng UTF-8
)

# Tạo một "nhà máy" (factory) để tạo ra các DB session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tạo một lớp Base mà tất cả các model (định nghĩa bảng) của SQLAlchemy sẽ kế thừa
Base = declarative_base()

# --- Import models *sau* khi Base được định nghĩa ---
# Điều này giúp Base.metadata nhận diện được tất cả các model khi create_all được gọi
from . import models


# --- Hàm tạo bảng database khi ứng dụng khởi động ---
# Đảm bảo hàm này được định nghĩa ở cấp cao nhất của file (không bị thụt lề)
def create_database_tables():
    """Tạo các bảng database dựa trên các model nếu chúng chưa tồn tại."""
    print("Attempting to create database tables...") # Thêm dòng print để debug
    try:
        # Base.metadata.create_all sẽ tạo các bảng cho tất cả các model kế thừa từ Base
        # Đảm bảo các model đã được import ở đâu đó để Base.metadata nhận diện được chúng
        Base.metadata.create_all(bind=engine)
        print("Database tables created/checked successfully.")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        # Có thể raise Exception ở đây nếu bạn muốn ứng dụng dừng lại khi tạo bảng lỗi
        # raise e


# Dependency Injection cho FastAPI: Hàm này sẽ được gọi để cung cấp một DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
