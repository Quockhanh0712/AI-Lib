# app/routers/user_endpoints.py
from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated
from datetime import datetime
import shutil
import os
import json # Import json

# Import các module cần thiết
from db import database, models
from schemas import user as user_schemas
from schemas import attendance as attendance_schemas # Thêm import này
from schemas import request as request_schemas
from crud import crud_user, crud_attendance, crud_request # Thêm crud_attendance

# Thư mục để lưu ảnh tạm thời (giữ lại định nghĩa)
TEMP_PHOTO_DIR = "temp_photos"
os.makedirs(TEMP_PHOTO_DIR, exist_ok=True)

router = APIRouter(
    prefix="/machine",
    tags=["Machine UI Endpoints"]
)

# --- Endpoint Kiểm tra Mã Thành viên (Sử dụng DB) ---
@router.get("/users/{member_code}/check",
            response_model=user_schemas.UserCheckResponse, # Sử dụng schema phản hồi
            summary="Kiểm tra sự tồn tại và trạng thái của User (Using DB)")
def check_user_by_member_code_endpoint(
    member_code: str,
    db: Session = Depends(database.get_db) # Thêm dependency database session
):
    """
    Endpoint này kiểm tra mã thành viên bằng cách truy vấn database.
    Trả về thông tin user nếu tìm thấy và trạng thái Approved.
    Trả về 404 nếu không tìm thấy, 403 nếu không Approved.
    """
    print(f"LOG: Received GET request for /machine/users/{member_code}/check (Using DB)")
    print(f"LOG: Checking member code: {member_code}")

    # Sử dụng CRUD function để tìm user trong database
    db_user = crud_user.get_user_by_member_code(db, member_code=member_code)

    if not db_user:
        print(f"LOG: User with member code {member_code} not found in DB.")
        # Trả về mã lỗi 404 NOT FOUND nếu không tìm thấy user
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Member code '{member_code}' not found.")

    # Kiểm tra trạng thái người dùng (chỉ cho phép Approved)
    # So sánh với giá trị string của Enum
    if db_user.status != models.UserStatus.Approved.value:
         print(f"LOG: User with member code {member_code} found but status is '{db_user.status}'.")
         # Trả về mã lỗi 403 FORBIDDEN nếu user không Approved
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"User account with member code '{member_code}' is not approved or is inactive. Current status: {db_user.status}")


    print(f"LOG: Member code {member_code} found and is Approved.")

    # Trả về phản hồi thành công với thông tin user (sử dụng Pydantic schema để chuẩn hóa)
    # Frontend mong đợi cấu trúc này để hiển thị thông tin user
    return user_schemas.UserCheckResponse.model_validate(db_user)

# --- UC1: Điểm danh Vào Thư viện (Chỉ log) ---
# Endpoint này hiện tại không được sử dụng trực tiếp bởi frontend cho check-in,
# logic check-in (tạo AttendanceSession) được tích hợp trong recognize_face
@router.post("/attendance/check-in",
            summary="Điểm danh Vào Thư viện (Not Used Directly)")
async def check_in_user_endpoint(
    member_code: str = Form(...),
    db: Session = Depends(database.get_db)
):
    """
    Endpoint này hiện tại không được sử dụng trực tiếp cho check-in.
    Logic tạo AttendanceSession được tích hợp trong /recognize_face.
    """
    print(f"LOG: Received POST request for /machine/attendance/check-in (Not Used Directly)")
    return {"message": f"This endpoint is not used directly for check-in. Logic is in /recognize_face."}


# --- UC2: Xem Danh sách Người dùng Đang ở trong Thư viện (Sử dụng DB) ---
@router.get("/attendance/in-library",
            response_model=List[attendance_schemas.UserInLibraryResponse], # Sử dụng schema mới
            summary="Xem Danh sách Người dùng Đang ở trong Thư viện (Using DB)")
def get_users_in_library_endpoint(db: Session = Depends(database.get_db)):
    """
    Endpoint này truy vấn database để lấy danh sách người dùng đang ở trong thư viện.
    """
    print(f"LOG: Received GET request for /machine/attendance/in-library (Using DB)")

    # SỬA LỖI: Gọi đúng tên hàm từ crud_attendance
    active_sessions_with_users = crud_attendance.get_all_open_attendance_sessions_with_user_info(db)

    # Debugging: In ra số lượng và chi tiết session tìm được
    print(f"LOG: Found {len(active_sessions_with_users)} active attendance sessions.")
    # for session, user in active_sessions_with_users:
    #    print(f"  - Session ID: {session.id}, User: {user.full_name}, Entry Time: {session.entry_time}")


    # Chuyển đổi kết quả từ SQLAlchemy (list of tuples) thành Pydantic model
    # Dựa vào schema UserInLibraryResponse (cần đảm bảo schema này khớp với dữ liệu trả về)
    # Schema UserInLibraryResponse cần có các trường từ AttendanceSession VÀ User
    # Ví dụ: id (session id), user_id, entry_time, user_session_owner (User object)
    # Nếu schema UserInLibraryResponse của bạn khác, cần điều chỉnh mapping ở đây
    users_in_library = [
        attendance_schemas.UserInLibraryResponse(
            id=session.id,
            user_id=session.user_id,
            entry_time=session.entry_time,
            user_session_owner=user_schemas.User.model_validate(user) # Map User ORM model to User schema
        ) for session, user in active_sessions_with_users
    ]


    return users_in_library


# --- UC3: Điểm danh Ra khỏi Thư viện (Chỉ log) ---
# Endpoint này sẽ cần được sửa để cập nhật AttendanceSession trong DB sau này
@router.post("/attendance/check-out",
            summary="Điểm danh Ra khỏi Thư viện (Needs DB Integration)")
async def check_out_user_endpoint(
    session_id_to_checkout: int = Form(...),
    member_code_confirmation: str = Form(...),
    db: Session = Depends(database.get_db)
):
    """Endpoint này hiện tại chỉ log khi được gọi và trả về phản hồi tạm thời."""
    print(f"LOG: Received POST request for /machine/attendance/check-out (Needs DB Integration)")
    print(f"LOG: Check-out request for session ID: {session_id_to_checkout}, member code: {member_code_confirmation}")

    # Tạm thời trả về phản hồi thành công
    return {"message": "Received check-out request", "session_id": session_id_to_checkout, "status": "received"}


# --- UC4: Gửi Yêu cầu Đăng ký Thành viên (Chỉ log) ---
# Endpoint này sẽ cần được sửa để tạo RegistrationRequest trong DB sau này
@router.post("/registration-requests/", status_code=status.HTTP_201_CREATED,
            summary="Gửi Yêu cầu Đăng ký Thành viên (Needs DB Integration)")
async def submit_registration_request_endpoint(
    requested_member_code: str = Form(...),
    full_name: str = Form(...),
    email: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    photo: Annotated[Optional[UploadFile], File()] = None,
    db: Session = Depends(database.get_db)
):
    """Endpoint này hiện tại chỉ log khi được gọi và trả về phản hồi tạm thời."""
    print(f"LOG: Received POST request for /machine/registration-requests/ (Needs DB Integration)")
    print(f"LOG: Registration request - Code: {requested_member_code}, Name: {full_name}, Email: {email}, Phone: {phone_number}")
    if photo:
        print(f"LOG: Received photo file: {photo.filename}, size: {photo.size} bytes")
        # Có thể lưu ảnh tạm thời ở đây nếu muốn
        # with open(os.path.join(TEMP_PHOTO_DIR, photo.filename), "wb") as buffer:
        #     shutil.copyfileobj(photo.file, buffer)

    return {
        "message": "Received registration request",
        "requested_member_code": requested_member_code,
        "full_name": full_name,
        "photo_received": photo is not None
    }


# --- UC5: Xem Lịch sử Chuyên cần Cá nhân (Chỉ log) ---
# Endpoint này sẽ cần được sửa để truy vấn User và AttendanceSession trong DB sau này
@router.get("/users/{member_code}/profile",
            summary="Lấy thông tin cá nhân của User (Needs DB Integration)")
def get_user_profile_endpoint(
    member_code: str,
    db: Session = Depends(database.get_db)
):
    """
    Endpoint này hiện tại chỉ log khi được gọi và trả về phản hồi tạm thời.
    Logic truy vấn database thực tế sẽ được thêm vào sau.
    """
    print(f"LOG: Received GET request for /machine/users/{member_code}/profile (Needs DB Integration)")
    print(f"LOG: Profile request for member code: {member_code}")

    # Tạm thời trả về phản hồi mô phỏng
    return {
        "id": 999,
        "member_code": member_code,
        "full_name": "Dummy User",
        "email": "dummy@example.com",
        "phone_number": "0123456789",
        "status": "Approved",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


# --- UC6: Chỉnh sửa Thông tin Cá nhân (Chỉ log) ---
# Endpoint này sẽ cần được sửa để cập nhật User trong DB sau này
@router.put("/users/{member_code}/profile",
            summary="Cập nhật thông tin cá nhân của User (Needs DB Integration)")
async def update_user_profile_endpoint(
    member_code: str,
    user_update_data: user_schemas.UserUpdate,
    db: Session = Depends(database.get_db)
):
    """Endpoint này hiện tại chỉ log khi được gọi và trả về phản hồi tạm thời."""
    print(f"LOG: Received PUT request for /machine/users/{member_code}/profile (Needs DB Integration)")
    print(f"LOG: Update profile request for member code: {member_code}")
    print(f"LOG: Received update data: {user_update_data.model_dump_json()}")

    # Tạm thời trả về phản hồi mô phỏng
    return {
        "id": 999,
        "member_code": member_code,
        "full_name": user_update_data.full_name or "Dummy User",
        "email": user_update_data.email or "dummy@example.com",
        "phone_number": user_update_data.phone_number or "0123456789",
        "status": "Approved",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@router.get("/users/{member_code}/attendance-history/completed",
            summary="Xem lịch sử các ca đã hoàn thành của User (Needs DB Integration)")
def get_user_completed_history_endpoint(
    member_code: str,
    skip: int = 0, limit: int = 20,
    db: Session = Depends(database.get_db)
):
    """Endpoint này hiện tại chỉ log khi được gọi và trả về danh sách rỗng tạm thời."""
    print(f"LOG: Received GET request for /machine/users/{member_code}/attendance-history/completed (Needs DB Integration)")
    print(f"LOG: History request for member code: {member_code}, skip: {skip}, limit: {limit}")

    # Tạm thời trả về danh sách rỗng
    return []

# --- Endpoint nhận diện hoặc xác minh khuôn mặt (Simulated 1:1 Check & Check-in) ---
@router.post("/recognize_face",
             response_model=user_schemas.FaceRecognitionResponse, # Sử dụng schema phản hồi
             summary="Nhận diện hoặc xác minh khuôn mặt (Simulated 1:1 Check & Check-in)")
async def recognize_face_endpoint(
    file: Annotated[UploadFile, File()],
    member_id: Annotated[Optional[str], Form()] = None, # member_id là string
    db: Session = Depends(database.get_db)
):
    """
    Endpoint để nhận diện hoặc xác minh khuôn mặt.
    Nhận file ảnh và tùy chọn mã thành viên, xử lý và trả về kết quả.
    Sau khi xác minh thành công (mô phỏng), tạo một AttendanceSession trong DB.
    """
    try:
        print(f"LOG: Received POST request for /machine/recognize_face (Simulated 1:1 Check & Check-in)")
        print(f"LOG: Recognition/Verification request - Member ID: {member_id}, Filename: {file.filename}")

        # ... (phần đọc file, có thể giữ nguyên hoặc bỏ qua nếu chỉ mô phỏng) ...

        if not member_id:
            print("LOG: Member ID is missing in recognition request.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Member ID is required for verification.")

        # Bước 1: Tìm người dùng trong database bằng member_id
        print(f"LOG: Attempting to find user with member_code: {member_id}")
        db_user = crud_user.get_user_by_member_code(db, member_code=member_id)

        # Bước 2: Kiểm tra kết quả tìm kiếm
        if not db_user:
            print(f"LOG: User with member code {member_id} not found.")
            return user_schemas.FaceRecognitionResponse(
                success=False,
                message=f"Member code '{member_id}' not found.",
                user=None
            )

        # Bước 3: Kiểm tra trạng thái người dùng (chỉ cho phép Approved)
        # So sánh với giá trị string của Enum
        if db_user.status != models.UserStatus.Approved.value:
             print(f"LOG: User with member code {member_id} found but status is '{db_user.status}'.")
             return user_schemas.FaceRecognitionResponse(
                success=False,
                message=f"User account with member code '{member_id}' is not approved or is inactive. Current status: {db_user.status}",
                user=None
            )


        # --- PHẦN TÍCH HỢP AI NHẬN DIỆN THỰC TẾ SẼ Ở ĐÂY SAU NÀY ---
        # - Hiện tại vẫn là mô phỏng, nhưng chúng ta sẽ tạo AttendanceSession THẬT
        print(f"LOG: User found and is Approved. Simulating successful verification for {db_user.full_name}.")

        # Bước 4: Tạo một AttendanceSession mới cho user này
        # Đây là phần quan trọng để tích hợp check-in vào DB
        try:
            # Kiểm tra xem user đã có session đang mở chưa
            active_session = crud_attendance.get_open_attendance_session_by_user_id(db, user_id=db_user.id)


            if active_session:
                print(f"LOG: User {db_user.full_name} already has an active session (ID: {active_session.id}). Skipping new session creation.")
                 # Trả về phản hồi thành công nhưng với thông báo khác
                return user_schemas.FaceRecognitionResponse(
                    success=True,
                    message=f"Chào mừng trở lại, {db_user.full_name}! Bạn đã điểm danh vào rồi.",
                    user=user_schemas.UserCheckResponse.model_validate(db_user)
                )
            else:
                # Nếu chưa có session đang mở, tạo session mới
                new_session = crud_attendance.create_attendance_session(db=db, user_id=db_user.id)
                print(f"LOG: Created new attendance session for user {db_user.full_name} (ID: {new_session.id})")
                 # Trả về phản hồi thành công thông thường
                return user_schemas.FaceRecognitionResponse(
                    success=True,
                    message=f"Xác minh thành công! Chào mừng, {db_user.full_name}!",
                    user=user_schemas.UserCheckResponse.model_validate(db_user)
                )

        except Exception as e:
            print(f"ERROR: Failed to create attendance session: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create attendance session: {e}")


    except HTTPException as http_exc:
        print(f"ERROR: HTTP Exception in recognize_face: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        print(f"ERROR: Uncaught error processing recognition/verification request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {e}")

