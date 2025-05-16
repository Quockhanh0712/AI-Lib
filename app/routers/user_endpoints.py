# app/routers/user_endpoints.py
from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import shutil # Để xử lý lưu file ảnh tạm
import os # Để làm việc với đường dẫn file

from app.db import database, models
from app.schemas import user as user_schemas
from app.schemas import attendance as attendance_schemas
from app.schemas import request as request_schemas
from app.crud import crud_user, crud_attendance, crud_request

# Thư mục để lưu ảnh tạm thời cho các yêu cầu đăng ký
TEMP_PHOTO_DIR = "temp_photos"
os.makedirs(TEMP_PHOTO_DIR, exist_ok=True) # Tạo thư mục nếu chưa có

router = APIRouter(
    prefix="/machine", # Tiền tố chung cho các API của Machine UI
    tags=["Machine UI Endpoints"] # Gom nhóm trong API docs
)

# --- UC1: Điểm danh Vào Thư viện ---
@router.post("/attendance/check-in", response_model=attendance_schemas.AttendanceSession)
async def check_in_user_endpoint(
    member_code: str = Form(...),
    # Sau này khi tích hợp AI, sẽ nhận file ảnh ở đây:
    # face_image: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    """
    Endpoint cho người dùng điểm danh vào.
    Yêu cầu Mã Thành viên. Sau này sẽ yêu cầu cả ảnh khuôn mặt.
    """
    # 1. Kiểm tra Mã Thành viên
    db_user = crud_user.get_user_by_member_code(db, member_code=member_code)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Member code '{member_code}' not found.")
    if db_user.status != "Approved":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is not approved or is inactive.")

    # 2. Kiểm tra xem user đã có phiên nào đang mở chưa
    open_session = crud_attendance.get_open_attendance_session_by_user_id(db, user_id=db_user.id)
    if open_session:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has already checked in and not checked out.")

    # --- PHẦN XÁC MINH KHUÔN MẶT (SẼ THÊM SAU) ---
    # Giả sử ở đây khuôn mặt đã được xác minh thành công với db_user.id
    # Ví dụ:
    # if not await verify_face_with_stored_embedding(db, db_user.id, face_image):
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Face verification failed.")
    # --- KẾT THÚC PHẦN KHUÔN MẶT ---

    # 3. Tạo phiên điểm danh mới
    created_session = crud_attendance.create_attendance_session(db, user_id=db_user.id)

    # Có thể trả về thêm thông tin user nếu Frontend cần
    # return {"session": created_session, "user_full_name": db_user.full_name}
    return created_session

# --- UC2: Xem Danh sách Người dùng Đang ở trong Thư viện ---
@router.get("/attendance/in-library", response_model=List[attendance_schemas.UserInLibrary])
def get_users_in_library_endpoint(db: Session = Depends(database.get_db)):
    """Lấy danh sách tất cả người dùng hiện đang có phiên điểm danh mở (chưa checkout)."""
    sessions_with_users = crud_attendance.get_all_open_attendance_sessions_with_user_info(db)
    
    # Chuyển đổi kết quả từ SQLAlchemy (tuple) sang Pydantic model
    users_in_library = [
        attendance_schemas.UserInLibrary(
            session_id=session.id,
            member_code=user.member_code,
            full_name=user.full_name,
            entry_time=session.entry_time
        ) for session, user in sessions_with_users
    ]
    return users_in_library

# --- UC3: Điểm danh Ra khỏi Thư viện ---
@router.post("/attendance/check-out", response_model=attendance_schemas.AttendanceSession)
async def check_out_user_endpoint(
    session_id_to_checkout: int = Form(...), # ID của phiên điểm danh muốn checkout
    member_code_confirmation: str = Form(...), # Mã thành viên để xác nhận
    db: Session = Depends(database.get_db)
):
    """Endpoint cho người dùng điểm danh ra."""
    # 1. Xác minh member_code_confirmation
    db_user_confirming = crud_user.get_user_by_member_code(db, member_code=member_code_confirmation)
    if not db_user_confirming:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Member code '{member_code_confirmation}' for confirmation not found.")

    # 2. Thực hiện checkout
    # Hàm crud_attendance.checkout_attendance_session đã bao gồm kiểm tra user_id của phiên có khớp không
    updated_session_or_error = crud_attendance.checkout_attendance_session(
        db,
        session_id=session_id_to_checkout,
        user_id_from_code=db_user_confirming.id
    )

    if updated_session_or_error is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance session not found or already checked out.")
    if updated_session_or_error == "mismatch":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Member code does not match the user of the selected session.")
    
    return updated_session_or_error # Đây là đối tượng AttendanceSession đã cập nhật

# --- UC4: Gửi Yêu cầu Đăng ký Thành viên ---
@router.post("/registration-requests/", response_model=request_schemas.RegistrationRequest, status_code=status.HTTP_201_CREATED)
async def submit_registration_request_endpoint(
    requested_member_code: str = Form(...),
    full_name: str = Form(...),
    email: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    photo: UploadFile = File(...), # Nhận file ảnh từ người dùng
    db: Session = Depends(database.get_db)
):
    """Endpoint để người dùng gửi yêu cầu đăng ký thành viên mới, kèm ảnh."""
    # 1. Xử lý lưu file ảnh tạm
    # Tạo tên file duy nhất để tránh trùng lặp, ví dụ: member_code + timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{requested_member_code}_{timestamp}_{photo.filename}"
    file_path = os.path.join(TEMP_PHOTO_DIR, filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
    except Exception as e:
        # Xử lý lỗi nếu không lưu được file
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save photo: {e}")
    finally:
        photo.file.close() # Luôn đóng file sau khi xử lý

    # 2. Tạo Pydantic model cho request
    request_data = request_schemas.RegistrationRequestCreate(
        requested_member_code=requested_member_code,
        full_name=full_name,
        email=email,
        phone_number=phone_number,
        photo_path=file_path # Lưu đường dẫn đến file ảnh đã lưu tạm
    )

    # 3. Gọi CRUD để tạo request trong DB
    try:
        created_request = crud_request.create_registration_request(db=db, request=request_data)
    except ValueError as ve: # Bắt lỗi từ CRUD nếu member_code đã tồn tại/pending
        # Xóa file ảnh tạm nếu tạo request thất bại
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e: # Lỗi chung khác
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred: {e}")

    return created_request

# --- UC5: Xem Lịch sử Chuyên cần Cá nhân (Sau khi Điểm danh Vào) ---
# --- UC6: Chỉnh sửa Thông tin Cá nhân (Sau khi Điểm danh Vào) ---
# Hai UC này được kích hoạt sau khi UC1 (Điểm danh Vào) thành công.
# Thông thường, Frontend sẽ nhận được member_code hoặc user_id sau UC1,
# sau đó dùng nó để gọi các API riêng biệt.

@router.get("/users/{member_code}/profile", response_model=user_schemas.User,
            summary="Lấy thông tin cá nhân của User (Sau khi check-in)")
def get_user_profile_endpoint(member_code: str, db: Session = Depends(database.get_db)):
    """
    Lấy thông tin cá nhân của user dựa trên member_code.
    Thường được gọi sau khi user check-in thành công và muốn xem/sửa thông tin.
    """
    db_user = crud_user.get_user_by_member_code(db, member_code)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found.")
    if db_user.status != "Approved": # Chỉ user active mới xem/sửa được
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is not active.")
    return db_user

@router.put("/users/{member_code}/profile", response_model=user_schemas.User,
            summary="Cập nhật thông tin cá nhân của User (Sau khi check-in)")
def update_user_profile_endpoint(
    member_code: str,
    user_update_data: user_schemas.UserUpdate, # Dữ liệu cần cập nhật
    db: Session = Depends(database.get_db)
):
    """
    Cập nhật thông tin cá nhân (không bao gồm ảnh) cho user.
    User tự thực hiện sau khi check-in.
    """
    db_user = crud_user.get_user_by_member_code(db, member_code)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found to update.")
    if db_user.status != "Approved":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot update profile of an inactive user.")

    # Kiểm tra email mới (nếu có) có bị trùng với user khác không
    if user_update_data.email and user_update_data.email != db_user.email:
        existing_user_with_email = crud_user.get_user_by_email(db, email=user_update_data.email)
        if existing_user_with_email and existing_user_with_email.id != db_user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered by another user.")

    updated_user = crud_user.update_user_profile(db, db_user=db_user, user_update=user_update_data)
    return updated_user

@router.get("/users/{member_code}/attendance-history/completed",
            response_model=List[attendance_schemas.AttendanceSession],
            summary="Xem lịch sử các ca đã hoàn thành của User (Sau khi check-in)")
def get_user_completed_history_endpoint(
    member_code: str,
    skip: int = 0, limit: int = 20, # Phân trang
    db: Session = Depends(database.get_db)
):
    """Lấy lịch sử các phiên điểm danh đã checkout của một user cụ thể."""
    db_user = crud_user.get_user_by_member_code(db, member_code)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found to get history.")

    history = crud_attendance.get_user_completed_attendance_history(db, user_id=db_user.id, skip=skip, limit=limit)
    return history