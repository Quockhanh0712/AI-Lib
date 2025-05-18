from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import các module khác của bạn (db, routers, core, v.v.)
from db import database, models # Import database module để gọi create_database_tables
from routers import user_endpoints, admin_endpoints
from core.config import settings # Ví dụ

# Khởi tạo ứng dụng FastAPI
app = FastAPI()

# Cấu hình CORS
origins = [
    "http://localhost",
    "http://localhost:8082",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include các routers của bạn
app.include_router(user_endpoints.router)
app.include_router(admin_endpoints.router)

# --- Gọi hàm tạo bảng database khi ứng dụng khởi động ---
# Điều này đảm bảo các bảng được tạo nếu chúng chưa tồn tại
@app.on_event("startup")
def on_startup():
    """Hàm này chạy khi ứng dụng FastAPI khởi động."""
    print("Creating database tables if they don't exist...")
    database.create_database_tables() # Gọi hàm tạo bảng từ database.py
    print("Database tables checked/created successfully.")


# Định nghĩa endpoint gốc (/) nếu bạn có
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Library Attendance System API (Simple Admin Auth)! Visit /docs."}

# Lưu ý: Endpoint /recognize_face đã được chuyển sang file user_endpoints.py
# và có prefix là /machine, nên bạn không cần định nghĩa lại ở đây.
