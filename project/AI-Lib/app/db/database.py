# app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings # Import đối tượng settings từ config.py

# Lấy chuỗi kết nối DB từ cấu hình
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Tạo SQLAlchemy engine: đây là "cổng" để SQLAlchemy nói chuyện với database driver (mysqlclient)
# pool_pre_ping=True: kiểm tra kết nối trước mỗi lần lấy từ pool (hữu ích cho kết nối dài hạn)
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# Tạo một "nhà máy" (factory) để tạo ra các DB session
# Mỗi instance của SessionLocal sẽ là một session (phiên làm việc) với database
# autocommit=False: Các thay đổi không tự động được lưu vào DB, bạn cần gọi db.commit()
# autoflush=False: Các thay đổi không tự động được gửi tạm thời vào DB trước khi commit
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tạo một lớp Base mà tất cả các model (định nghĩa bảng) của SQLAlchemy sẽ kế thừa
# Điều này giúp SQLAlchemy quản lý các model và ánh xạ chúng tới các bảng trong DB
Base = declarative_base()

# Dependency Injection cho FastAPI: Hàm này sẽ được gọi để cung cấp một DB session
# cho mỗi API endpoint cần tương tác với database.
def get_db():
    db = SessionLocal() # Tạo một session mới
    try:
        yield db # "Yield" session cho API endpoint sử dụng
                 # Code của API endpoint sẽ chạy ở đây
    finally:
        db.close() # Đóng session sau khi API endpoint hoàn thành (dù thành công hay lỗi)
                   # Điều này rất quan trọng để giải phóng tài nguyên DB.