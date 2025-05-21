# backend/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware # <<< THÊM IMPORT NÀY
from sqlalchemy.orm import Session
from db import database
from routers import user_endpoints, admin_endpoints # Import các router của bạn
import os # <<< THÊM IMPORT NÀY (nếu chưa có)

# Tạo ứng dụng FastAPI
app = FastAPI(
    title="AI Library System API",
    description="API cho hệ thống quản lý thư viện AI",
    version="1.0.0",
)

# Cấu hình CORS (nếu cần)
origins = [
    "http://localhost",
    "http://localhost:8082", # Frontend User
    "http://localhost:8083", # Frontend Admin
    # Thêm các origin khác nếu ứng dụng của bạn được deploy ở các domain khác
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, # Cho phép gửi cookies (quan trọng cho session)
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cấu hình Session Middleware
# SECRET_KEY phải là một chuỗi ngẫu nhiên, bí mật và dài.
# Trong môi trường production, bạn nên lấy nó từ biến môi trường.
# Ở đây dùng tạm một chuỗi cứng cho dev.
SECRET_KEY = os.environ.get("SESSION_SECRET_KEY", "your-super-secret-key-for-session-management-replace-this-in-production")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY) # <<< THÊM DÒNG NÀY

# Gọi hàm tạo bảng database khi ứng dụng khởi động
@app.on_event("startup")
def on_startup():
    """Hàm này chạy khi ứng dụng FastAPI khởi động."""
    print("Creating database tables if they don't exist...")
    database.create_database_tables() # Gọi hàm tạo bảng từ database.py
    print("Database tables checked/created successfully.")


# Đăng ký các router
app.include_router(user_endpoints.router)
app.include_router(admin_endpoints.router)

# Định nghĩa endpoint gốc (/) nếu bạn có
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Library Attendance System API (Simple Admin Auth)! Visit /docs."}

# Lưu ý: Endpoint /recognize_face đã được chuyển sang file user_endpoints.py
# và có prefix là /machine, nên bạn không cần định nghĩa lại ở đây.
