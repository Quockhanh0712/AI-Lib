# app/routers/admin_endpoints.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm # Vẫn dùng để lấy username/password tiện lợi
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime # Vẫn cần datetime cho các logic khác
import shutil
import os
import httpx

from app.db import database, models
from app.schemas import admin as admin_schemas
from app.schemas import user as user_schemas
from app.schemas import request as request_schemas
from app.schemas import attendance as attendance_schemas
from app.crud import crud_admin, crud_user, crud_request, crud_attendance
# Bỏ: from app.core.config import settings (trừ khi bạn dùng cho việc khác ngoài JWT)
# Bỏ: from jose import JWTError, jwt
# Bỏ: from fastapi.security import OAuth2PasswordBearer
# Bỏ: from datetime import timedelta

USER_PHOTOS_DIR = "user_photos" # Giữ lại nếu dùng cho lưu ảnh user do Admin thêm
os.makedirs(USER_PHOTOS_DIR, exist_ok=True)

router = APIRouter(
    prefix="/admin",
    tags=["Admin Endpoints (Simple Session Auth)"]
)

# --- Dependency để kiểm tra Admin đã đăng nhập qua session ---
async def get_current_admin_from_session(request: Request, db: Session = Depends(database.get_db)) -> models.AdminUser:
    """
    Lấy thông tin admin từ session.
    Nếu chưa đăng nhập hoặc admin không tồn tại/không active, raise HTTPException.
    """
    admin_id = request.session.get("admin_id")
    # print(f"Session data in get_current_admin_from_session: {request.session}") # Debug
    if not admin_id:
        # print("Admin ID not in session") # Debug
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated (no session)",
        )
    
    try:
        admin_id_int = int(admin_id) # Đảm bảo admin_id là số nguyên
    except ValueError:
        # print(f"Invalid admin_id format in session: {admin_id}") # Debug
        request.session.clear() # Xóa session hỏng
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session data.",
        )

    admin = db.query(models.AdminUser).filter(models.AdminUser.id == admin_id_int).first()
    if not admin:
        # print(f"Admin with ID {admin_id_int} not found in DB") # Debug
        request.session.clear() # Xóa session nếu user không còn tồn tại
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated (admin not found)",
        )
    if not admin.is_active:
        # print(f"Admin {admin.username} is not active") # Debug
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated (inactive admin)",
        )
    # print(f"Authenticated admin from session: {admin.username}") # Debug
    return admin

# --- UC7: Đăng nhập Admin (Phiên bản đơn giản dùng Session) ---
@router.post("/login", response_model=admin_schemas.AdminUser)
async def login_admin_simple_session(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db)
):
    """Endpoint để Admin đăng nhập và tạo session cookie."""
    admin = crud_admin.authenticate_admin(db, username=form_data.username, password_input=form_data.password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password or inactive account",
        )
    request.session["admin_id"] = admin.id # Lưu ID vào session
    request.session["admin_username"] = admin.username # Có thể lưu thêm
    # print(f"Admin {admin.username} logged in. Session set: {request.session}") # Debug
    return admin

# --- Endpoint Đăng xuất Admin (Xóa session) ---
@router.post("/logout")
async def logout_admin_simple_session(request: Request):
    """Endpoint để Admin đăng xuất bằng cách xóa session."""
    admin_username = request.session.get("admin_username", "Unknown admin")
    request.session.clear() # Xóa toàn bộ session data
    # print(f"Admin {admin_username} logged out. Session cleared.") # Debug
    return {"message": f"Admin {admin_username} successfully logged out"}


# Endpoint để Admin kiểm tra thông tin của chính mình (cần session)
@router.get("/me", response_model=admin_schemas.AdminUser)
async def read_admin_me_endpoint_session(
    current_admin: models.AdminUser = Depends(get_current_admin_from_session)
):
    """Lấy thông tin của admin đang đăng nhập (qua session)."""
    return current_admin

# --- Các API Admin khác (UC8, UC9, UC10) sẽ dùng Depends(get_current_admin_from_session) ---
# Ví dụ:
# Configuration for the AI Service URL
AI_SERVICE_BASE_URL = "http://localhost:8001" # <<< PORT FOR YOUR SEPARATE AI SERVICE



@router.get("/users/", response_model=List[user_schemas.User])
def read_all_users_endpoint(
    skip: int = 0, limit: int = 100,
    status_filter: Optional[str] = None,
    current_admin: models.AdminUser = Depends(get_current_admin_from_session), # <<<< SỬ DỤNG DEPENDENCY MỚI
    db: Session = Depends(database.get_db)
):
    query = db.query(models.User)
    if status_filter:
        if status_filter not in ["Approved", "Inactive"]:
            raise HTTPException(status_code=400, detail="Invalid status_filter. Use 'Approved' or 'Inactive'.")
        query = query.filter(models.User.status == status_filter)
    users = query.order_by(models.User.id.asc()).offset(skip).limit(limit).all()
    return users

@router.get("/users/{user_id_or_code}", response_model=user_schemas.User)
def read_user_by_id_or_code_endpoint(
    user_id_or_code: str,
    current_admin: models.AdminUser = Depends(get_current_admin_from_session), # <<<< SỬ DỤNG DEPENDENCY MỚI
    db: Session = Depends(database.get_db)
):
    db_user = None
    if user_id_or_code.isdigit():
        db_user = crud_user.get_user(db, user_id=int(user_id_or_code))
    if not db_user:
        db_user = crud_user.get_user_by_member_code(db, member_code=user_id_or_code)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return db_user


@router.post("/users/", response_model=user_schemas.User, status_code=status.HTTP_201_CREATED)
async def create_new_user_by_admin_endpoint(
    member_code: str = Form(...),
    full_name: str = Form(...),
    email: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    photo: UploadFile = File(...), # Expecting a single photo
    current_admin: models.AdminUser = Depends(get_current_admin_from_session),
    db: Session = Depends(database.get_db)
):
    print(f"[AdminEP] Create User: mc='{member_code}', fn='{full_name}', em='{email}', pn='{phone_number}', photo='{photo.filename if photo else None}'")

    if crud_user.get_user_by_member_code(db, member_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Member code already registered.")
    if email and crud_user.get_user_by_email(db, email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered.")

    # Construct data for Pydantic model explicitly
    user_data_for_schema = {
        "member_code": member_code,
        "full_name": full_name,
    }
    if email is not None: # Pydantic V2 handles Optional[str]=None correctly when key is absent or value is None
        user_data_for_schema["email"] = email
    if phone_number is not None:
        user_data_for_schema["phone_number"] = phone_number
    
    print(f"[AdminEP] Data for UserCreate schema: {user_data_for_schema}")

    try:
        user_pydantic_schema = user_schemas.UserCreate(**user_data_for_schema)
    except Exception as e_pydantic: # Catch Pydantic validation errors specifically if needed
        print(f"[AdminEP] Pydantic UserCreate instantiation error: {e_pydantic}")
        # FastAPI will likely catch Pydantic ValidationErrors and return 422 automatically,
        # but this explicit catch can help debug if the error is unexpected.
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid user data provided: {e_pydantic}")

    db_user = crud_user.create_user(db=db, user=user_pydantic_schema, status="Approved")
    print(f"[AdminEP] User {db_user.member_code} created in DB with ID {db_user.id}.")

    # Forward the single photo to the AI service
    if photo and db_user:
        ai_service_add_face_url = f"{AI_SERVICE_BASE_URL}/add-face"
        
        # AI service's /add-face expects a 'files' field (which is a List[UploadFile])
        # We send our single 'photo' as a list containing one item for the 'files' field name.
        files_for_ai = [('files', (photo.filename, await photo.read(), photo.content_type))]
        # We need to await photo.read() to get the contents before httpx sends it,
        # OR pass the photo.file object if httpx handles async file-like objects well for 'files'.
        # Simpler is to read it first. Make sure to reset pointer if needed or pass the file object.
        # For httpx, passing the file object directly is usually better:
        await photo.seek(0) # Reset file pointer in case it was read before
        files_for_ai_httpx = [('files', (photo.filename, photo.file, photo.content_type))]

        payload_for_ai = {'member_code': db_user.member_code}

        print(f"[AdminEP] Forwarding 1 photo for member {db_user.member_code} to AI service...")
        async with httpx.AsyncClient() as client:
            try:
                ai_response = await client.post(ai_service_add_face_url, data=payload_for_ai, files=files_for_ai_httpx)
                ai_response.raise_for_status()
                print(f"[AdminEP] AI service response for {db_user.member_code}: {ai_response.json()}")
            except httpx.HTTPStatusError as e:
                print(f"[AdminEP] Error calling AI service for {db_user.member_code}: {e.response.status_code} - {e.response.text}")
                # Add more robust error handling: maybe delete db_user or flag enrollment failure
            except httpx.RequestError as e:
                print(f"[AdminEP] Request error calling AI service for {db_user.member_code}: {str(e)}")
    else:
        print(f"[AdminEP] No photo provided or user creation failed, skipping AI service call for member_code: {member_code}")


    return db_user


@router.put("/users/{user_id}", response_model=user_schemas.User)
async def update_existing_user_by_admin_endpoint(
    user_id: int,
    full_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    status_update: Optional[str] = Form(None, pattern="^(Approved|Inactive)$"),
    photo: Optional[UploadFile] = File(None), # <<< CHANGED: Expect single OPTIONAL 'photo'
    current_admin: models.AdminUser = Depends(get_current_admin_from_session),
    db: Session = Depends(database.get_db)
):
    db_user = crud_user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found to update.")

    # ... (logic to update textual data: full_name, email, phone_number, status_update - remains same) ...
    # ... (updated_user_model = crud_user.update_user_profile(...), etc.)
    update_data_dict = {}
    if full_name is not None: update_data_dict["full_name"] = full_name
    # ... (handle email and phone_number updates) ...
    updated_user_model = db_user
    if update_data_dict:
        user_update_schema_data = {k: v for k, v in update_data_dict.items() if v is not None}
        if user_update_schema_data:
             user_update_for_crud = user_schemas.UserUpdate(**user_update_schema_data)
             updated_user_model = crud_user.update_user_profile(db, db_user=updated_user_model, user_update=user_update_for_crud)
    if status_update and status_update != updated_user_model.status:
        updated_user_model = crud_user.update_user_status_by_admin(db, db_user=updated_user_model, new_status=status_update)


    # Handle NEW photo upload and forward to AI service
    if photo and updated_user_model: # If a new photo was provided
        member_code_for_ai = updated_user_model.member_code
        ai_service_add_face_url = f"{AI_SERVICE_BASE_URL}/add-face"
        
        # AI service's /add-face expects a 'files' field (list of files)
        # We send our single 'photo' as a list containing one item for the 'files' field
        files_for_ai_update = [('files', (photo.filename, photo.file, photo.content_type))]
        payload_for_ai = {'member_code': member_code_for_ai}

        print(f"Forwarding 1 NEW photo for member {member_code_for_ai} to AI service at {ai_service_add_face_url}")
        async with httpx.AsyncClient() as client:
            try:
                ai_response = await client.post(ai_service_add_face_url, data=payload_for_ai, files=files_for_ai_update)
                ai_response.raise_for_status()
                print(f"AI service response for adding new face to {member_code_for_ai}: {ai_response.json()}")
            # ... (error handling as in create_new_user_by_admin_endpoint) ...
            except httpx.HTTPStatusError as e:
                print(f"Error calling AI service for adding new face to {member_code_for_ai}: {e.response.status_code} - {e.response.text}")
            except httpx.RequestError as e:
                print(f"Request error calling AI service for adding new face to {member_code_for_ai}: {str(e)}")
                
    db.refresh(updated_user_model)
    return updated_user_model

@router.delete("/users/{user_id}", response_model=user_schemas.User)
def delete_existing_user_by_admin_endpoint(
    user_id: int,
    current_admin: models.AdminUser = Depends(get_current_admin_from_session), # <<<< SỬ DỤNG DEPENDENCY MỚI
    db: Session = Depends(database.get_db)
):
    deleted_user = crud_user.delete_user(db, user_id=user_id)
    if deleted_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found to delete.")
    return deleted_user

@router.get("/registration-requests/pending", response_model=List[request_schemas.RegistrationRequest])
def get_all_pending_requests_endpoint(
    skip: int = 0, limit: int = 100,
    current_admin: models.AdminUser = Depends(get_current_admin_from_session), # <<<< SỬ DỤNG DEPENDENCY MỚI
    db: Session = Depends(database.get_db)
):
    requests = crud_request.get_pending_registration_requests(db, skip=skip, limit=limit)
    return requests

@router.get("/registration-requests/{request_id}", response_model=request_schemas.RegistrationRequest)
def get_single_request_endpoint(
    request_id: int,
    current_admin: models.AdminUser = Depends(get_current_admin_from_session), # <<<< SỬ DỤNG DEPENDENCY MỚI
    db: Session = Depends(database.get_db)
):
    db_request = crud_request.get_registration_request_by_id(db, request_id=request_id)
    if not db_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration request not found.")
    return db_request


@router.put("/registration-requests/{request_id}/process", response_model=request_schemas.RegistrationRequest)
async def process_registration_request_endpoint(
    request_id: int,
    action: request_schemas.RegistrationRequestProcess,
    current_admin: models.AdminUser = Depends(get_current_admin_from_session), # <<<< SỬ DỤNG DEPENDENCY MỚI
    db: Session = Depends(database.get_db)
):
    db_request = crud_request.get_registration_request_by_id(db, request_id=request_id)
    if not db_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration request not found.")
    if db_request.status != 'Pending':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Request is already '{db_request.status}'.")

    processed_request = None
    error_message = None

    if action.status == "Approved":
        processed_request, error_message = crud_request.process_approve_registration_request(
            db, db_request=db_request, admin_id=current_admin.id
        )
    elif action.status == "Rejected":
        processed_request = crud_request.process_reject_registration_request(
            db, db_request=db_request, admin_id=current_admin.id
        )
    
    if error_message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
    if not processed_request: # Trường hợp này không nên xảy ra nếu error_message được xử lý đúng
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error processing request.")
        
    return processed_request


@router.get("/attendance-history/completed", response_model=List[attendance_schemas.AttendanceSession])
def get_admin_all_completed_history_endpoint(
    skip: int = 0, limit: int = 100,
    member_code_filter: Optional[str] = None,
    start_date_filter: Optional[str] = None,
    end_date_filter: Optional[str] = None,
    current_admin: models.AdminUser = Depends(get_current_admin_from_session), # <<<< SỬ DỤNG DEPENDENCY MỚI
    db: Session = Depends(database.get_db)
):
    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None
    if start_date_filter:
        try: start_dt = datetime.strptime(start_date_filter, "%Y-%m-%d")
        except ValueError: raise HTTPException(status_code=400, detail="Invalid start_date_filter format. Use YYYY-MM-DD")
    if end_date_filter:
        try: end_dt = datetime.strptime(end_date_filter, "%Y-%m-%d")
        except ValueError: raise HTTPException(status_code=400, detail="Invalid end_date_filter format. Use YYYY-MM-DD")

    history = crud_attendance.get_admin_all_completed_attendance_history(
        db, skip=skip, limit=limit,
        filter_member_code=member_code_filter,
        start_date=start_dt,
        end_date=end_dt
    )
    return history