# app/main.py
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware # <<<< THÊM IMPORT
from app.db import database, models
from app.routers import user_endpoints, admin_endpoints
from app.core.config import settings # <<<< THÊM IMPORT NÀY ĐỂ LẤY SECRET_KEY

try:
    models.Base.metadata.create_all(bind=database.engine)
    print("Database tables checked/created successfully.")
except Exception as e:
    print(f"Error creating database tables: {e}")

app = FastAPI(
    title="Library Attendance System API (Simple Auth)",
    description="API for managing library attendance (simplified admin auth).",
    version="0.1.1"
)

# --- THÊM SESSION MIDDLEWARE ---
# secret_key này rất quan trọng cho việc mã hóa session cookie.
# Nên sử dụng settings.SECRET_KEY để nhất quán.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY, # <<<< SỬ DỤNG SECRET_KEY TỪ CONFIG
    # session_cookie="library_session", # Tên cookie (tùy chọn)
    # max_age=14 * 24 * 60 * 60  # Thời gian sống của cookie (ví dụ: 14 ngày, tùy chọn)
)
# --- KẾT THÚC THÊM SESSION MIDDLEWARE ---

app.include_router(user_endpoints.router)
app.include_router(admin_endpoints.router)

@app.get("/", tags=["Root (Simple Auth)"])
async def read_root():
    return {"message": "Welcome to the Library Attendance System API (Simple Admin Auth)! Visit /docs."}