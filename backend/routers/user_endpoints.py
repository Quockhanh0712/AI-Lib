# backend/routers/user_endpoints.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from datetime import datetime
import pytz

from db import database
from crud import crud_attendance, crud_user
from schemas import attendance as attendance_schemas
from schemas import user as user_schemas
from pydantic import BaseModel

router = APIRouter()

# Pydantic Model cho Request Body của Check-out (chỉ cần member_code)
class CheckoutRequest(BaseModel):
    member_code: str

# --- UC2: Xem Danh sách Người dùng Đang ở trong Thư viện ---
@router.get("/current-members/",
            response_model=List[attendance_schemas.UserInLibraryResponse],
            summary="Xem Danh sách Người dùng Đang ở trong Thư viện")
def get_users_in_library_endpoint(db: Session = Depends(database.get_db)):
    print(f"LOG: Received GET request for /machine/current-members/")

    # crud_attendance.get_all_open_attendance_sessions_with_user_info trả về list các tuple (AttendanceSession, User)
    active_attendance_sessions_with_users = crud_attendance.get_all_open_attendance_sessions_with_user_info(db)

    print("LOG: Debugging active_attendance_sessions_with_users content:")

    vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    utc_tz = pytz.utc

    users_in_library_data = []

    for session_record, user in active_attendance_sessions_with_users:
        print(f"   Session ID: {session_record.id}, User Full Name (from DB): {user.full_name}, Type: {type(user.full_name)}")
        print(f"   Entry Time (from DB): {session_record.entry_time}, Type: {type(session_record.entry_time)}")

        # Đảm bảo entry_time có múi giờ trước khi chuyển đổi
        if session_record.entry_time.tzinfo is None:
            utc_entry_time = utc_tz.localize(session_record.entry_time)
        else:
            utc_entry_time = session_record.entry_time.astimezone(utc_tz)

        vietnam_entry_time = vietnam_tz.normalize(utc_entry_time.astimezone(vietnam_tz))

        formatted_entry_time = vietnam_entry_time.strftime("%H:%M:%S %d/%m/%Y")
        print(f"   Formatted Entry Time (Vietnam Time): {formatted_entry_time}")

        user_owner_data = user_schemas.User.model_validate(user).model_dump(mode='json')

        users_in_library_data.append({
            "id": session_record.id, # Đây là ID của bản ghi attendance_session
            "user_id": session_record.user_id,
            "entry_time": formatted_entry_time, # Đổi tên key để khớp với schema và data
            "user_session_owner": user_owner_data # Vẫn giữ tên key này cho tiện ở frontend
        })

    print("LOG: End of active_attendance_sessions_with_users debug.")
    print(f"LOG: Found {len(active_attendance_sessions_with_users)} active attendance sessions.")

    return JSONResponse(
        content=users_in_library_data,
        media_type="application/json; charset=utf-8"
    )

# --- UC3: Điểm danh Ra khỏi Thư viện (Chỉ yêu cầu member_code) ---
@router.post("/attendance/check-out",
             summary="Điểm danh Ra khỏi Thư viện (Chỉ yêu cầu member_code)",
             response_model=dict)
async def check_out_with_member_code_only_endpoint(
    request: CheckoutRequest,
    db: Session = Depends(database.get_db)
):
    print(f"LOG: Received POST request for /machine/attendance/check-out with member_code: {request.member_code}")

    # 1. Tìm user_id từ member_code
    user_by_code = crud_user.get_user_by_member_code(db, request.member_code)
    if not user_by_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid member code. User not found."
        )

    target_user_id = user_by_code.id

    # 2. Tìm bản ghi điểm danh đang mở của user này (exit_time IS NULL)
    open_attendance_session = crud_attendance.get_open_attendance_session_by_user_id(db, target_user_id)

    if not open_attendance_session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User '{user_by_code.full_name}' (ID: {target_user_id}) is not currently checked in (no open session found)."
        )

    # 3. Gọi hàm checkout_attendance_session từ crud_attendance.py
    updated_session_record = crud_attendance.checkout_attendance_session(db, open_attendance_session.id, target_user_id)

    if updated_session_record == "mismatch":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error: User ID mismatch during attendance session checkout."
        )

    if not updated_session_record:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to close attendance session record."
        )

    print(f"LOG: User {user_by_code.full_name} (Member Code: {request.member_code}) successfully checked out. Session ID: {updated_session_record.id}.")
    return JSONResponse(
        content={"message": f"User {user_by_code.full_name} (Member Code: {request.member_code}) checked out successfully.", "session_id": updated_session_record.id},
        status_code=status.HTTP_200_OK
    )