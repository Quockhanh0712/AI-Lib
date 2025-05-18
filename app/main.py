from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import các module khác của bạn (db, routers, core, v.v.)
from db import database, models # Ví dụ
from routers import user_endpoints, admin_endpoints # Đảm bảo import user_endpoints và admin_endpoints
from core.config import settings # Ví dụ

# Khởi tạo ứng dụng FastAPI
app = FastAPI()

# Cấu hình CORS
# Định nghĩa các nguồn gốc (origins) được phép truy cập backend của bạn
# Trong trường hợp này, cho phép frontend chạy ở http://localhost:8082
origins = [
    "http://localhost",
    "http://localhost:8082", # Cho phép frontend truy cập
    # Thêm các nguồn gốc khác nếu cần (ví dụ: địa chỉ IP của máy host)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Danh sách các nguồn gốc được phép
    allow_credentials=True, # Cho phép gửi cookie/credentials trong yêu cầu
    allow_methods=["*"], # Cho phép tất cả các phương thức HTTP (GET, POST, PUT, DELETE, OPTIONS, ...)
    allow_headers=["*"], # Cho phép tất cả các header trong yêu cầu
)

# Include các routers của bạn
# Bỏ comment các dòng này để ứng dụng FastAPI nhận biết các endpoints trong routers
app.include_router(user_endpoints.router)
app.include_router(admin_endpoints.router)


# Định nghĩa endpoint gốc (/) nếu bạn có
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Library Attendance System API (Simple Admin Auth)! Visit /docs."}

# Định nghĩa endpoint nhận diện khuôn mặt (/recognize_face)
# Đảm bảo endpoint này tồn tại và xử lý đúng logic nhận diện
# Đây chỉ là ví dụ về cấu trúc, bạn cần đảm bảo logic xử lý file/dữ liệu form ở đây là đúng
# from fastapi import File, UploadFile, Form
#
# @app.post("/recognize_face")
# async def recognize_face_endpoint(member_id: int = Form(...), file: UploadFile = File(...)):
#     # Logic xử lý nhận diện khuôn mặt với member_id và file ảnh
#     print(f"Received request for member ID: {member_id}")
#     print(f"Received file: {file.filename}")
#     # ... (thêm code xử lý nhận diện)
#     return {"message": "Recognition process started"} # Trả về phản hồi thành công

# Lưu ý: Endpoint /recognize_face đã được chuyển sang file user_endpoints.py
# và có prefix là /machine, nên bạn không cần định nghĩa lại ở đây.
