# app/routers/user_endpoints.py
from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated
from datetime import datetime
import shutil
import os

# Import các module cần thiết (giữ lại để code chạy)
from db import database, models
from schemas import user as user_schemas
from schemas import attendance as attendance_schemas
from schemas import request as request_schemas
from crud import crud_user, crud_attendance, crud_request

# Thư mục để lưu ảnh tạm thời (giữ lại định nghĩa)
TEMP_PHOTO_DIR = "temp_photos"
os.makedirs(TEMP_PHOTO_DIR, exist_ok=True)

router = APIRouter(
    prefix="/machine",
    tags=["Machine UI Endpoints"]
)

# --- Endpoint Kiểm tra Mã Thành viên (Chỉ log) ---
@router.get("/users/{member_code}/check",
            summary="Kiểm tra sự tồn tại và trạng thái của User (Chỉ log)")
def check_user_by_member_code_endpoint(member_code: str, db: Session = Depends(database.get_db)):
    """
    Endpoint này hiện tại chỉ log khi được gọi và trả về phản hồi tạm thời.
    Logic kiểm tra database thực tế đã được bỏ qua.
    """
    print(f"LOG: Received GET request for /machine/users/{member_code}/check")
    print(f"LOG: Checking member code: {member_code}")

    # Tạm thời trả về phản hồi thành công để frontend nhận được 200 OK
    # Trong thực tế, bạn sẽ gọi crud_user.get_user_by_member_code và xử lý phản hồi
    return {"message": f"Received check request for member code {member_code}", "member_code": member_code}


# --- UC1: Điểm danh Vào Thư viện (Chỉ log) ---
@router.post("/attendance/check-in",
            summary="Điểm danh Vào Thư viện (Chỉ log)")
async def check_in_user_endpoint(
    member_code: str = Form(...),
    # face_image: UploadFile = File(...), # Thêm tham số này khi tích hợp ảnh vào check-in
    db: Session = Depends(database.get_db)
):
    """
    Endpoint này hiện tại chỉ log khi được gọi và trả về phản hồi tạm thời.
    Logic điểm danh thực tế đã được bỏ qua.
    """
    print(f"LOG: Received POST request for /machine/attendance/check-in")
    print(f"LOG: Check-in request for member code: {member_code}")

    # Tạm thời trả về phản hồi thành công
    return {"message": f"Received check-in request for member code {member_code}", "member_code": member_code, "status": "received"}


# --- UC2: Xem Danh sách Người dùng Đang ở trong Thư viện (Chỉ log) ---
@router.get("/attendance/in-library",
            summary="Xem Danh sách Người dùng Đang ở trong Thư viện (Chỉ log)")
def get_users_in_library_endpoint(db: Session = Depends(database.get_db)):
    """
    Endpoint này hiện tại chỉ log khi được gọi và trả về danh sách rỗng tạm thời.
    Logic truy vấn database thực tế đã được bỏ qua.
    """
    print(f"LOG: Received GET request for /machine/attendance/in-library")
    print("LOG: Returning dummy empty list for users in library.")

    # Tạm thời trả về danh sách rỗng để frontend không gặp lỗi khi parse JSON
    return []


# --- UC3: Điểm danh Ra khỏi Thư viện (Chỉ log) ---
@router.post("/attendance/check-out",
            summary="Điểm danh Ra khỏi Thư viện (Chỉ log)")
async def check_out_user_endpoint(
    session_id_to_checkout: int = Form(...),
    member_code_confirmation: str = Form(...),
    db: Session = Depends(database.get_db)
):
    """
    Endpoint này hiện tại chỉ log khi được gọi và trả về phản hồi tạm thời.
    Logic checkout thực tế đã được bỏ qua.
    """
    print(f"LOG: Received POST request for /machine/attendance/check-out")
    print(f"LOG: Check-out request for session ID: {session_id_to_checkout}, member code: {member_code_confirmation}")

    # Tạm thời trả về phản hồi thành công
    return {"message": "Received check-out request", "session_id": session_id_to_checkout, "status": "received"}


# --- UC4: Gửi Yêu cầu Đăng ký Thành viên (Chỉ log, ảnh tùy chọn) ---
@router.post("/registration-requests/", status_code=status.HTTP_201_CREATED,
            summary="Gửi Yêu cầu Đăng ký Thành viên (Chỉ log)")
async def submit_registration_request_endpoint(
    requested_member_code: str = Form(...),
    full_name: str = Form(...),
    email: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    # SỬA LỖI: Đặt tham số không mặc định trước tham số có mặc định
    # Đồng thời, làm cho tham số ảnh TÙY CHỌN để tránh lỗi 422 nếu frontend không gửi ảnh
    photo: Annotated[Optional[UploadFile], File()] = None, # Ảnh là tùy chọn
    db: Session = Depends(database.get_db)
):
    """
    Endpoint này hiện tại chỉ log khi được gọi và trả về phản hồi tạm thời.
    Logic đăng ký thực tế (lưu ảnh, tạo request DB) đã được bỏ qua.
    """
    print(f"LOG: Received POST request for /machine/registration-requests/")
    print(f"LOG: Registration request - Code: {requested_member_code}, Name: {full_name}, Email: {email}, Phone: {phone_number}")
    if photo:
        print(f"LOG: Received photo file: {photo.filename}, size: {photo.size} bytes")
        # Bạn có thể đọc nội dung file ở đây nếu muốn log thêm thông tin về file
        # contents = await photo.read()
        # print(f"LOG: Photo content first 10 bytes: {contents[:10]}")
        # await photo.seek(0) # Quay lại đầu file nếu cần đọc lại sau này

    # Tạm thời trả về phản hồi thành công
    return {
        "message": "Received registration request",
        "requested_member_code": requested_member_code,
        "full_name": full_name,
        "photo_received": photo is not None
    }


# --- UC5: Xem Lịch sử Chuyên cần Cá nhân (Chỉ log) ---
@router.get("/users/{member_code}/profile",
            summary="Lấy thông tin cá nhân của User (Chỉ log)")
def get_user_profile_endpoint(member_code: str, db: Session = Depends(database.get_db)):
    """
    Endpoint này hiện tại chỉ log khi được gọi và trả về phản hồi tạm thời.
    Logic truy vấn database thực tế đã được bỏ qua.
    """
    print(f"LOG: Received GET request for /machine/users/{member_code}/profile")
    print(f"LOG: Profile request for member code: {member_code}")

    # Tạm thời trả về phản hồi thành công (dummy user info)
    return {
        "id": 999, # Dummy ID
        "member_code": member_code,
        "full_name": "Dummy User",
        "email": "dummy@example.com",
        "phone_number": "0123456789",
        "status": "Approved",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


# --- UC6: Chỉnh sửa Thông tin Cá nhân (Chỉ log) ---
@router.put("/users/{member_code}/profile",
            summary="Cập nhật thông tin cá nhân của User (Chỉ log)")
def update_user_profile_endpoint(
    member_code: str,
    user_update_data: user_schemas.UserUpdate,
    db: Session = Depends(database.get_db)
):
    """
    Endpoint này hiện tại chỉ log khi được gọi và trả về phản hồi tạm thời.
    Logic cập nhật database thực tế đã được bỏ qua.
    """
    print(f"LOG: Received PUT request for /machine/users/{member_code}/profile")
    print(f"LOG: Update profile request for member code: {member_code}")
    print(f"LOG: Received update data: {user_update_data.model_dump_json()}") # Sử dụng model_dump_json() cho Pydantic v2+

    # Tạm thời trả về phản hồi thành công (dummy updated user info)
    return {
        "id": 999, # Dummy ID
        "member_code": member_code,
        "full_name": user_update_data.full_name or "Dummy User",
        "email": user_update_data.email or "dummy@example.com",
        "phone_number": user_update_data.phone_number or "0123456789",
        "status": "Approved",
        "created_at": datetime.utcnow(), # Cần lấy từ DB thật
        "updated_at": datetime.utcnow() # Cần lấy từ DB thật
    }


@router.get("/users/{member_code}/attendance-history/completed",
            summary="Xem lịch sử các ca đã hoàn thành của User (Chỉ log)")
def get_user_completed_history_endpoint(
    member_code: str,
    skip: int = 0, limit: int = 20,
    db: Session = Depends(database.get_db)
):
    """
    Endpoint này hiện tại chỉ log khi được gọi và trả về danh sách rỗng tạm thời.
    Logic truy vấn database thực tế đã được bỏ qua.
    """
    print(f"LOG: Received GET request for /machine/users/{member_code}/attendance-history/completed")
    print(f"LOG: History request for member code: {member_code}, skip: {skip}, limit: {limit}")

    # Tạm thời trả về danh sách rỗng
    return []


# --- Endpoint nhận diện hoặc xác minh khuôn mặt ---
# Giữ nguyên logic print đã có
@router.post("/recognize_face",
            summary="Nhận diện hoặc xác minh khuôn mặt (Đã có log)")
async def recognize_face_endpoint(
    file: Annotated[UploadFile, File()],
    member_id: Annotated[Optional[int], Form()] = None,
    db: Session = Depends(database.get_db)
):
    """
    Endpoint để nhận diện hoặc xác minh khuôn mặt.
    Nhận file ảnh và tùy chọn mã thành viên, xử lý và trả về kết quả.
    """
    try:
        print(f"LOG: Received POST request for /machine/recognize_face")
        print(f"LOG: Recognition/Verification request - Member ID: {member_id}, Filename: {file.filename}")

        # Đọc nội dung file ảnh (có thể bỏ qua để đơn giản hóa)
        # contents = await file.read()

        # --- THÊM LOGIC XỬ LÝ NHẬN DIỆN HOẶC XÁC MINH KHUÔN MẶT Ở ĐÂY ---
        # ... (code gọi hàm xử lý AI, truy cập DB nếu cần) ...

        # Tạm thời trả về phản hồi thành công để kiểm tra kết nối
        return {"message": "Recognition/Verification process received", "member_id": member_id, "filename": file.filename}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"ERROR: Error processing recognition/verification request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {e}")

