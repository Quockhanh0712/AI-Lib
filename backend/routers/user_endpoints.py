# D:\AI-Lib\backend\routers\user_endpoints.py

from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from fastapi.responses import JSONResponse # Thêm dòng này
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated
from datetime import datetime
import shutil
import os
import json # Import json
import pytz

# Import các module cần thiết
from db import database, models
from schemas import user as user_schemas
from schemas import attendance as attendance_schemas
from schemas import request as request_schemas
from crud import crud_user, crud_attendance, crud_request

# Thư mục để lưu ảnh tạm thời (giữ lại định nghĩa)
TEMP_PHOTO_DIR = "temp_photos"
os.makedirs(TEMP_PHOTO_DIR, exist_ok=True)

router = APIRouter(
    prefix="/machine", # Prefix này là đúng và sẽ được giữ nguyên
    tags=["Machine UI Endpoints"]
)

# --- Endpoint Kiểm tra Mã Thành viên (SỬA ĐƯỜNG DẪN) ---
@router.get("/check-member/{member_code}", # ĐÃ SỬA: Đường dẫn khớp với frontend
            response_model=user_schemas.UserCheckResponse,
            summary="Kiểm tra sự tồn tại và trạng thái của User")
def check_user_by_member_code_endpoint(
    member_code: str,
    db: Session = Depends(database.get_db)
):
    print(f"LOG: Received GET request for /machine/check-member/{member_code}")
    print(f"LOG: Checking member code: {member_code}")

    db_user = crud_user.get_user_by_member_code(db, member_code=member_code)

    if not db_user:
        print(f"LOG: User with member code {member_code} not found in DB.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Member code '{member_code}' not found.")

    if db_user.status != models.UserStatus.Approved.value:
        print(f"LOG: User with member code {member_code} found but status is '{db_user.status}'.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"User account with member code '{member_code}' is not approved or is inactive. Current status: {db_user.status}")

    print(f"LOG: Member code {member_code} found and is Approved.")
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
    print(f"LOG: Received POST request for /machine/attendance/check-in (Not Used Directly)")
    return {"message": f"This endpoint is not used directly for check-in. Logic is in /recognize_face."}


# --- UC2: Xem Danh sách Người dùng Đang ở trong Thư viện (SỬA ĐƯỜNG DẪN) ---
@router.get("/current-members/",
            response_model=List[attendance_schemas.UserInLibraryResponse],
            summary="Xem Danh sách Người dùng Đang ở trong Thư viện")
def get_users_in_library_endpoint(db: Session = Depends(database.get_db)):
    print(f"LOG: Received GET request for /machine/current-members/")

    active_sessions_with_users = crud_attendance.get_all_open_attendance_sessions_with_user_info(db)

    print("LOG: Debugging active_sessions_with_users content:")
    
    # Định nghĩa múi giờ Việt Nam
    vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    utc_tz = pytz.utc # Múi giờ UTC

    users_in_library_data = [] # Danh sách để chứa dữ liệu đã định dạng

    for session, user in active_sessions_with_users:
        # Debugging: In ra tên người dùng ngay sau khi lấy từ DB
        print(f"  Session ID: {session.id}, User Full Name (from DB): {user.full_name}, Type: {type(user.full_name)}")
        print(f"  Entry Time (from DB): {session.entry_time}, Type: {type(session.entry_time)}")

        # Chuyển đổi entry_time sang múi giờ Việt Nam
        # Giả định session.entry_time là datetime object không có múi giờ (naive) và là UTC
        if session.entry_time.tzinfo is None: # Nếu là naive datetime
            utc_entry_time = utc_tz.localize(session.entry_time) # Gán múi giờ UTC
        else: # Nếu đã có múi giờ (ví dụ: từ DB đã là timezone-aware)
            utc_entry_time = session.entry_time.astimezone(utc_tz) # Chuyển về UTC

        vietnam_entry_time = utc_entry_time.astimezone(vietnam_tz)

        # Định dạng thời gian theo yêu cầu: "HH:MM:SS DD/MM/YYYY"
        formatted_entry_time = vietnam_entry_time.strftime("%H:%M:%S %d/%m/%Y")
        print(f"  Formatted Entry Time (Vietnam Time): {formatted_entry_time}") # In ra thời gian đã định dạng

        # Chuyển đổi Pydantic model User thành dictionary
        user_owner_data = user_schemas.User.model_validate(user).model_dump(mode='json')

        # Thêm dữ liệu vào danh sách
        users_in_library_data.append({
            "id": session.id,
            "user_id": session.user_id,
            "entry_time": formatted_entry_time, # Sử dụng chuỗi thời gian đã định dạng
            "user_session_owner": user_owner_data
        })

    print("LOG: End of active_sessions_with_users debug.")
    print(f"LOG: Found {len(active_sessions_with_users)} active attendance sessions.")

    return JSONResponse(
        content=users_in_library_data, # Trả về danh sách các dictionary
        media_type="application/json; charset=utf-8"
    )

# --- UC3: Điểm danh Ra khỏi Thư viện ---
@router.post("/attendance/check-out",
             summary="Điểm danh Ra khỏi Thư viện")
async def check_out_user_endpoint(
    session_id_to_checkout: int = Form(...),
    member_code_confirmation: str = Form(...),
    db: Session = Depends(database.get_db)
):
    print(f"LOG: Received POST request for /machine/attendance/check-out")
    print(f"LOG: Check-out request for session ID: {session_id_to_checkout}, member code: {member_code_confirmation}")

    # 1. Lấy thông tin người dùng từ mã xác nhận
    user_by_confirmation_code = crud_user.get_user_by_member_code(db, member_code=member_code_confirmation)
    if not user_by_confirmation_code:
        print(f"LOG: Member code confirmation '{member_code_confirmation}' not found.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Mã thành viên xác nhận không tồn tại.")

    # 2. Gọi hàm checkout_attendance_session từ CRUD
    # Hàm này sẽ kiểm tra session_id, user_id và cập nhật trạng thái
    updated_session = crud_attendance.checkout_attendance_session(
        db=db,
        session_id=session_id_to_checkout,
        user_id_from_code=user_by_confirmation_code.id # Truyền ID của user đã xác nhận
    )

    if updated_session is None:
        print(f"LOG: Session ID {session_id_to_checkout} not found, already checked out, or user ID mismatch.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phiên điểm danh không tồn tại hoặc đã kết thúc.")
    elif updated_session == "mismatch": # Giá trị đặc biệt từ CRUD nếu user_id không khớp
        print(f"LOG: User ID mismatch for session {session_id_to_checkout}. Provided code: {member_code_confirmation}.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Mã thành viên không khớp với ca đã chọn.")

    print(f"LOG: Successfully checked out session {updated_session.id} for user {user_by_confirmation_code.full_name}.")
    return {"message": "Điểm danh ra thành công!", "session_id": updated_session.id, "status": "checked_out"}

# --- UC5: Xem Lịch sử Chuyên cần Cá nhân (ĐƯỜNG DẪN ĐÚNG) ---
# Endpoint này đã đúng với frontend, giữ nguyên
@router.get("/users/{member_code}/profile",
             response_model=user_schemas.UserProfileResponse, # ĐÃ SỬA: Sử dụng UserProfileResponse
             summary="Lấy thông tin cá nhân của User")
def get_user_profile_endpoint(
    member_code: str,
    db: Session = Depends(database.get_db)
):
    print(f"LOG: Received GET request for /machine/users/{member_code}/profile")
    print(f"LOG: Profile request for member code: {member_code}")
    # Lấy dữ liệu thực từ DB
    db_user = crud_user.get_user_by_member_code(db, member_code=member_code)
    if not db_user:
        print(f"LOG: User with member code {member_code} not found for profile.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Người dùng không tồn tại.")
    # Trả về Pydantic model đã được validate từ đối tượng DB
    # ĐÃ SỬA: Trả về UserProfileResponse
    return user_schemas.UserProfileResponse.model_validate(db_user)


# --- UC6: Chỉnh sửa Thông tin Cá nhân (ĐƯỜNG DẪN ĐÚNG) ---
@router.put("/users/{member_code}/profile",
             summary="Cập nhật thông tin cá nhân của User (Chỉ cho phép sửa tên, email, SĐT và kiểm tra trùng lặp)")
async def update_user_profile_endpoint(
    member_code: str,
    user_update_data: user_schemas.UserUpdate, # Vẫn nhận UserUpdate schema
    db: Session = Depends(database.get_db)
):
    print(f"LOG: Received PUT request for /machine/users/{member_code}/profile")
    print(f"LOG: Update profile request for member code: {member_code}")
    print(f"LOG: Received update data: {user_update_data.model_dump_json()}")

    # 1. Tìm người dùng trong DB
    db_user = crud_user.get_user_by_member_code(db, member_code=member_code)
    if not db_user:
        print(f"LOG: User with member code {member_code} not found for update.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Người dùng không tồn tại.")
    
    # 2. Kiểm tra trùng lặp cho email nếu email được cung cấp và khác với email hiện tại của người dùng
    if user_update_data.email is not None and user_update_data.email != db_user.email:
        existing_user_with_email = db.query(models.User).filter(
            models.User.email == user_update_data.email,
            models.User.id != db_user.id # Loại trừ chính người dùng đang được cập nhật
        ).first()
        if existing_user_with_email:
            print(f"LOG: Duplicate email '{user_update_data.email}' found for another user.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email này đã được sử dụng bởi người dùng khác.")

    # 3. Kiểm tra trùng lặp cho số điện thoại nếu số điện thoại được cung cấp và khác với số điện thoại hiện tại của người dùng
    if user_update_data.phone_number is not None and user_update_data.phone_number != db_user.phone_number:
        existing_user_with_phone = db.query(models.User).filter(
            models.User.phone_number == user_update_data.phone_number,
            models.User.id != db_user.id # Loại trừ chính người dùng đang được cập nhật
        ).first()
        if existing_user_with_phone:
            print(f"LOG: Duplicate phone number '{user_update_data.phone_number}' found for another user.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Số điện thoại này đã được sử dụng bởi người dùng khác.")

    # 4. Tạo một đối tượng UserUpdate mới chỉ với các trường được phép cập nhật
    # Điều này đảm bảo người dùng không thể thay đổi 'status' hay 'member_code'
    # ngay cả khi chúng được gửi từ frontend.
    allowed_update_data = user_schemas.UserUpdate(
        full_name=user_update_data.full_name,
        email=user_update_data.email,
        phone_number=user_update_data.phone_number
        # Không bao gồm 'status' ở đây để ngăn người dùng tự thay đổi trạng thái
    )

    # 5. Cập nhật thông tin người dùng bằng hàm CRUD
    # crud_user.update_user sẽ chỉ cập nhật các trường có trong allowed_update_data
    updated_user = crud_user.update_user(db, db_user=db_user, user_in=allowed_update_data)
    
    print(f"LOG: Successfully updated profile for user {member_code}.")
    # Trả về thông tin người dùng đã được cập nhật
    return user_schemas.UserCheckResponse.model_validate(updated_user)


# --- Endpoint nhận diện hoặc xác minh khuôn mặt (SỬA ĐƯỜNG DẪN) ---
@router.post("/recognize-face/", # ĐÃ SỬA: Đường dẫn khớp với frontend (thêm gạch ngang và dấu / cuối)
             response_model=user_schemas.FaceRecognitionResponse,
             summary="Nhận diện hoặc xác minh khuôn mặt (Simulated 1:1 Check & Check-in)")
async def recognize_face_endpoint(
    file: Annotated[UploadFile, File()],
    member_id: Annotated[Optional[str], Form()] = None,
    db: Session = Depends(database.get_db)
):
    try:
        print(f"LOG: Received POST request for /machine/recognize-face/ (Simulated 1:1 Check & Check-in)")
        print(f"LOG: Recognition/Verification request - Member ID: {member_id}, Filename: {file.filename}")

        if not member_id:
            print("LOG: Member ID is missing in recognition request.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Member ID is required for verification.")

        print(f"LOG: Attempting to find user with member_code: {member_id}")
        db_user = crud_user.get_user_by_member_code(db, member_code=member_id)

        if not db_user:
            print(f"LOG: User with member code {member_id} not found.")
            return user_schemas.FaceRecognitionResponse(
                success=False,
                message=f"Member code '{member_id}' not found.",
                user=None
            )

        if db_user.status != models.UserStatus.Approved.value:
            print(f"LOG: User with member code {member_id} found but status is '{db_user.status}'.")
            return user_schemas.FaceRecognitionResponse(
                success=False,
                message=f"User account with member code '{member_id}' is not approved or is inactive. Current status: {db_user.status}",
                user=None
            )

        print(f"LOG: User found and is Approved. Simulating successful verification for {db_user.full_name}.")

        try:
            active_session = crud_attendance.get_open_attendance_session_by_user_id(db, user_id=db_user.id)

            if active_session:
                print(f"LOG: User {db_user.full_name} already has an active session (ID: {active_session.id}). Skipping new session creation.")
                return user_schemas.FaceRecognitionResponse(
                    success=True,
                    message=f"Chào mừng trở lại, {db_user.full_name}! Bạn đã điểm danh vào rồi.",
                    user=user_schemas.UserCheckResponse.model_validate(db_user)
                )
            else:
                new_session = crud_attendance.create_attendance_session(db=db, user_id=db_user.id)
                print(f"LOG: Created new attendance session for user {db_user.full_name} (ID: {new_session.id})")
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
