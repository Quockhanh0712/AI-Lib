# app/routers/admin_endpoints.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm 
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import shutil
import httpx
import os
from db import database, models
from schemas import admin as admin_schemas
from schemas import user as user_schemas
from schemas import request as request_schemas
from schemas import attendance as attendance_schemas
from crud import crud_admin, crud_user, crud_request, crud_attendance
import json
from pytz import timezone, utc
USER_PHOTOS_DIR = "user_photos" # Giữ lại nếu dùng cho lưu ảnh user do Admin thêm
os.makedirs(USER_PHOTOS_DIR, exist_ok=True)
VIETNAM_TIMEZONE = timezone('Asia/Ho_Chi_Minh')

AI_SERVICE_URL = os.environ.get("AI_SERVICE_URL", "http://backend-ai:8000")
router = APIRouter(
    # prefix="/admin",
    tags=["Admin Endpoints (Simple Session Auth)"]
)

async def get_current_admin_from_session(request: Request, db: Session = Depends(database.get_db)) -> models.AdminUser:
    """
    Lấy thông tin admin từ session.
    Nếu chưa đăng nhập hoặc admin không tồn tại/không active, raise HTTPException.
    """
    admin_id = request.session.get("admin_id")
    if not admin_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated (no session)",
        )
    
    try:
        admin_id_int = int(admin_id)
    except ValueError:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session data.",
        )

    admin = db.query(models.AdminUser).filter(models.AdminUser.id == admin_id_int).first()
    if not admin:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated (admin not found)",
        )
    if not admin.is_active:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated (inactive admin)",
        )
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
    request.session["admin_id"] = admin.id
    request.session["admin_username"] = admin.username
    return admin

# --- Endpoint Đăng xuất Admin (Xóa session) ---
@router.post("/logout")
async def logout_admin_simple_session(request: Request):
    """Endpoint để Admin đăng xuất bằng cách xóa session."""
    admin_username = request.session.get("admin_username", "Unknown admin")
    request.session.clear()
    return {"message": f"Admin {admin_username} successfully logged out"}


# Endpoint để Admin kiểm tra thông tin của chính mình (cần session)
@router.get("/me", response_model=admin_schemas.AdminUser)
async def read_admin_me_endpoint_session(
    current_admin: models.AdminUser = Depends(get_current_admin_from_session)
):
    """Lấy thông tin của admin đang đăng nhập (qua session)."""
    return current_admin

# --- Các API Admin khác (UC8, UC9, UC10) sẽ dùng Depends(get_current_admin_from_session) ---
@router.post("/users/", response_model=user_schemas.User, status_code=status.HTTP_201_CREATED)
async def create_new_user_by_admin_endpoint(
    member_code: str = Form(...),
    full_name: str = Form(...),
    email: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    photo: UploadFile = File(...),
    current_admin: models.AdminUser = Depends(get_current_admin_from_session),
    db: Session = Depends(database.get_db)
):
    """Endpoint để Admin tạo người dùng mới và xử lý ảnh khuôn mặt, lưu embedding dạng TEXT."""
    if crud_user.get_user_by_member_code(db, member_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Member code already registered.")
    if email and crud_user.get_user_by_email(db, email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered.")

    photo_content = await photo.read()
    print(f"DEBUG CREATE: Kích thước photo_content đọc được: {len(photo_content)} bytes")
    print(f"DEBUG CREATE: Content-Type của ảnh: {photo.content_type}")

    embedding_list = None
    face_embedding_text = None

    try:
        async with httpx.AsyncClient(timeout = 30.0) as client:
            ai_response = await client.post(
                f"{AI_SERVICE_URL}/face-embeddings/extract",
                files={"image_file": (photo.filename, photo_content, photo.content_type)}
            )
            ai_response.raise_for_status()
            ai_result = ai_response.json()

            print(f"DEBUG CREATE: Toàn bộ ai_result nhận được từ AI service: {ai_result}") # <--- Dòng RẤT QUAN TRỌNG

            embedding_list = ai_result.get("embedding")
            print(f"DEBUG CREATE: embedding_list sau khi .get('embedding'): {embedding_list}")

            if not embedding_list:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="AI service did not return embedding.")

            face_embedding_text = json.dumps([embedding_list])
            print(f"DEBUG CREATE: face_embedding_text cuối cùng trước khi lưu: {face_embedding_text[:200]}...") # In 200 ký tự đầu

    except httpx.HTTPStatusError as e:
        print(f"DEBUG CREATE: Lỗi HTTPStatusError từ AI service: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code,
                            detail=f"Lỗi từ AI service khi xử lý ảnh: {e.response.text}")
    except httpx.RequestError as e:
        print(f"DEBUG CREATE: Lỗi RequestError khi kết nối AI service: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=f"Không thể kết nối đến AI service: {e}")
    except Exception as e:
        print(f"DEBUG CREATE: Lỗi không xác định khi gọi AI service: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Lỗi không xác định khi gọi AI service: {str(e)}")

    user_data = user_schemas.UserCreate(
        member_code=member_code,
        full_name=full_name,
        email=email,
        phone_number=phone_number,
    )
    
    db_user = crud_user.create_user(
        db=db, 
        user=user_data, 
        status="Approved",
        face_embedding_data=face_embedding_text,
    )
    # --- BẮT ĐẦU PHẦN CẦN THÊM VÀO ---
    try:
        async with httpx.AsyncClient(timeout=5.0) as client: # Tăng timeout nếu AI Service quá chậm
            ai_reload_response = await client.post(
                f"{AI_SERVICE_URL}/reload-embedding-cache"
            )
            ai_reload_response.raise_for_status() # Kiểm tra lỗi HTTP status (4xx, 5xx)
            print(f"DEBUG (Backend Admin): Yêu cầu AI Service tải lại cache thành công: {ai_reload_response.json()}")
    except httpx.RequestError as e:
        print(f"Cảnh báo (Backend Admin): Không thể yêu cầu AI Service tải lại cache: {e}. AI Service có thể cần khởi động lại để cập nhật thủ công.")
    except httpx.HTTPStatusError as e:
        print(f"Cảnh báo (Backend Admin): AI Service trả về lỗi khi tải lại cache: {e.response.text}")
    # --- KẾT THÚC PHẦN CẦN THÊM VÀO ---

    return db_user

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


@router.put("/users/{user_id}", response_model=user_schemas.User)
async def update_existing_user_by_admin_endpoint(
    user_id: int,
    full_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    status_update: Optional[str] = Form(None, pattern="^(Approved|Inactive)$"),
    photo: Optional[UploadFile] = File(None),
    current_admin: models.AdminUser = Depends(get_current_admin_from_session),
    db: Session = Depends(database.get_db)
):
    db_user = crud_user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found to update.")

    update_data = {}
    if full_name is not None: update_data["full_name"] = full_name
    if email is not None:
        if email != db_user.email:
            existing_user_with_email = crud_user.get_user_by_email(db, email=email)
            if existing_user_with_email and existing_user_with_email.id != user_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New email already registered by another user.")
        update_data["email"] = email
    if phone_number is not None: update_data["phone_number"] = phone_number
    
    final_face_embedding_json_string = None # Biến này sẽ chứa chuỗi JSON cuối cùng để cập nhật vào DB

    if photo:
        photo_content = await photo.read()
        new_embedding_from_ai = None # Sẽ chứa embedding mới từ AI (dạng list phẳng)
        try:
            async with httpx.AsyncClient(timeout = 30.0) as client:
                ai_response = await client.post(
                    f"{AI_SERVICE_URL}/face-embeddings/extract",
                    files={"image_file": (photo.filename, photo_content, photo.content_type)}
                )
                ai_response.raise_for_status()
                ai_result = ai_response.json()
                
                new_embedding_from_ai = ai_result.get("embedding")
                print(f"DEBUG (Admin Update): embedding_list received from AI: {new_embedding_from_ai}")
                if not new_embedding_from_ai:
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                        detail="AI service did not return embedding.")
                
                # --- BẮT ĐẦU LOGIC CHUẨN HÓA VÀ CỘNG DỒN EMBEDDING (ĐÃ SỬA ĐỔI) ---
                
                # Lấy bản ghi FaceEmbedding hiện có của user
                db_face_embedding_record = db.query(models.FaceEmbedding).filter(models.FaceEmbedding.user_id == user_id).first()
                
                processed_embeddings_for_db = [] 

                if db_face_embedding_record and db_face_embedding_record.embedding:
                    original_embedding_str_from_db = db_face_embedding_record.embedding
                    try:
                        parsed_db_data = json.loads(original_embedding_str_from_db)

                        if isinstance(parsed_db_data, list):
                            if all(isinstance(x, (int, float)) for x in parsed_db_data):
                                # Đây là trường hợp cũ (list phẳng), chuyển về list of lists
                                if len(parsed_db_data) > 0:
                                    processed_embeddings_for_db.append(parsed_db_data)
                                print(f"DEBUG (Admin Update): Dữ liệu cũ là list phẳng, đang chuẩn hóa.")
                            elif all(isinstance(x, list) and all(isinstance(y, (int, float)) for y in x) for x in parsed_db_data):
                                # Đây là trường hợp đã đúng định dạng list of lists
                                processed_embeddings_for_db = parsed_db_data
                                print(f"DEBUG (Admin Update): Dữ liệu cũ đã đúng định dạng.")
                            else:
                                print(f"Cảnh báo (Admin Update): Dữ liệu cũ có định dạng list hỗn tạp. Bỏ qua.")
                        elif isinstance(parsed_db_data, (int, float)):
                            print(f"Cảnh báo (Admin Update): Dữ liệu cũ là số float đơn. Bỏ qua.")
                        else:
                            print(f"Cảnh báo (Admin Update): Dữ liệu cũ có kiểu không mong muốn. Bỏ qua.")

                    except json.JSONDecodeError:
                        print(f"Lỗi (Admin Update): Chuỗi JSON embedding cũ không hợp lệ. Cố gắng sửa. Dữ liệu: '{original_embedding_str_from_db}'")
                        try:
                            # Cố gắng sửa lỗi chuỗi chỉ là float thô (ví dụ: "0.1,0.2,...")
                            temp_fixed_str = f"[{original_embedding_str_from_db}]"
                            temp_parsed_data = json.loads(temp_fixed_str)
                            if isinstance(temp_parsed_data, list) and all(isinstance(x, (int, float)) for x in temp_parsed_data):
                                if len(temp_parsed_data) > 0:
                                    processed_embeddings_for_db.append(temp_parsed_data)
                                print(f"DEBUG (Admin Update): Đã sửa chữa chuỗi float thô cũ thành list of list.")
                            else:
                                print(f"Cảnh báo (Admin Update): Không thể sửa chữa chuỗi float thô cũ. Bỏ qua.")
                        except Exception as ex:
                            print(f"Lỗi không xác định khi cố gắng sửa chuỗi float thô cũ: {ex}. Bỏ qua.")
                    except Exception as e:
                        print(f"Lỗi không xác định khi xử lý embedding cũ: {e}. Bỏ qua.")
                
                # Thêm embedding MỚI (list phẳng) vào list đã chuẩn hóa
                if new_embedding_from_ai: # Đảm bảo có embedding mới để thêm
                    processed_embeddings_for_db.append(new_embedding_from_ai)
                
                # Chuyển đổi list of lists cuối cùng thành chuỗi JSON để lưu vào DB
                final_face_embedding_json_string = json.dumps(processed_embeddings_for_db)
                print(f"DEBUG (Admin Update): final_face_embedding_json_string: {final_face_embedding_json_string[:200]}...")

                # Gán kết quả cuối cùng vào biến mà crud_user.update_user_profile sẽ nhận
                face_embedding_text_to_update = final_face_embedding_json_string

                # --- KẾT THÚC LOGIC CHUẨN HÓA VÀ CỘNG DỒN EMBEDDING ---

        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, 
                                detail=f"Lỗi từ AI service khi xử lý ảnh mới: {e.response.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                                detail=f"Không thể kết nối đến AI service để xử lý ảnh mới: {e}")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                detail=f"Lỗi không xác định khi xử lý ảnh mới: {str(e)}")
        
    user_update_schema = user_schemas.UserUpdate(**{k: v for k, v in update_data.items() if v is not None})
    
    updated_user = db_user
    if update_data or photo:
        updated_user = crud_user.update_user_profile(
            db, 
            db_user=db_user, 
            user_update=user_update_schema,
            face_embedding_text=face_embedding_text_to_update, # Đã được gán giá trị đúng ở trên
        )

    if status_update and status_update != updated_user.status:
        updated_user = crud_user.update_user_status_by_admin(db, db_user=updated_user, new_status=status_update)
    
    # --- PHẦN GỌI TẢI LẠI CACHE (GIỮ NGUYÊN) ---
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            ai_reload_response = await client.post(
                f"{AI_SERVICE_URL}/reload-embedding-cache"
            )
            ai_reload_response.raise_for_status()
            print(f"DEBUG (Backend Admin): Yêu cầu AI Service tải lại cache thành công: {ai_reload_response.json()}")
    except httpx.RequestError as e:
        print(f"Cảnh báo (Backend Admin): Không thể yêu cầu AI Service tải lại cache: {e}. AI Service có thể cần khởi động lại để cập nhật thủ công.")
    except httpx.HTTPStatusError as e:
        print(f"Cảnh báo (Backend Admin): AI Service trả về lỗi khi tải lại cache: {e.response.text}")
    # --- KẾT THÚC PHẦN GỌI TẢI LẠI CACHE ---

    return updated_user


@router.delete("/users/{user_id}", response_model=user_schemas.User)
async def delete_existing_user_by_admin_endpoint( # <--- XÁC NHẬN CÓ TỪ KHÓA `async` Ở ĐÂY
    user_id: int,
    current_admin: models.AdminUser = Depends(get_current_admin_from_session),
    db: Session = Depends(database.get_db)
):
    deleted_user = crud_user.delete_user(db, user_id=user_id)
    if deleted_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found to delete.")
    
    # Phần code này sẽ hoạt động ổn sau khi hàm được khai báo là async
    try:
        async with httpx.AsyncClient(timeout=5.0) as client: 
            ai_reload_response = await client.post(
                f"{AI_SERVICE_URL}/reload-embedding-cache"
            )
            ai_reload_response.raise_for_status() 
            print(f"DEBUG (Backend Admin): Yêu cầu AI Service tải lại cache thành công sau khi xóa user: {ai_reload_response.json()}")
    except httpx.RequestError as e:
        print(f"Cảnh báo (Backend Admin): Không thể yêu cầu AI Service tải lại cache sau khi xóa user: {e}. AI Service có thể cần khởi động lại để cập nhật thủ công.")
    except httpx.HTTPStatusError as e:
        print(f"Cảnh báo (Backend Admin): AI Service trả về lỗi khi tải lại cache sau khi xóa user: {e.response.text}")
    
    return deleted_user

@router.get("/registration-requests/pending", response_model=List[request_schemas.RegistrationRequest])
def get_all_pending_requests_endpoint(
    skip: int = 0, limit: int = 100,
    current_admin: models.AdminUser = Depends(get_current_admin_from_session),
    db: Session = Depends(database.get_db)
):
    requests = crud_request.get_pending_registration_requests(db, skip=skip, limit=limit)
    return requests

@router.get("/registration-requests/{request_id}", response_model=request_schemas.RegistrationRequest)
def get_single_request_endpoint(
    request_id: int,
    current_admin: models.AdminUser = Depends(get_current_admin_from_session),
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
    current_admin: models.AdminUser = Depends(get_current_admin_from_session),
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
    if not processed_request:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error processing request.")
        
    return processed_request


@router.get("/attendance-history/completed", response_model=List[attendance_schemas.AttendanceSession])
def get_admin_all_completed_history_endpoint(
    skip: int = 0, limit: int = 100,
    member_code_filter: Optional[str] = None,
    start_date_filter: Optional[str] = None,
    end_date_filter: Optional[str] = None,
    current_admin: models.AdminUser = Depends(get_current_admin_from_session),
    db: Session = Depends(database.get_db)
):
    final_start_datetime: Optional[datetime] = None
    final_end_datetime: Optional[datetime] = None

    # Xử lý start_date_filter
    if start_date_filter:
        try:
            # Chuyển đổi chuỗi ngày sang đối tượng date, sau đó kết hợp với thời gian 00:00:00 (đầu ngày)
            # để tạo datetime object.
            parsed_date = datetime.strptime(start_date_filter, "%Y-%m-%d").date()
            final_start_datetime = datetime.combine(parsed_date, datetime.min.time())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date_filter format. Use YYYY-MM-DD")
    
    # Xử lý end_date_filter
    if end_date_filter:
        try:
            # Chuyển đổi chuỗi ngày sang đối tượng date, sau đó kết hợp với thời gian 23:59:59 (cuối ngày)
            # để tạo datetime object.
            parsed_date = datetime.strptime(end_date_filter, "%Y-%m-%d").date()
            final_end_datetime = datetime.combine(parsed_date, datetime.max.time())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date_filter format. Use YYYY-MM-DD")

    # Xử lý member_code_filter để lấy user_id
    user_id_to_filter: Optional[int] = None
    if member_code_filter:
        # Giả định crud_user.get_user_by_member_code là hàm đúng để lấy user từ member_code
        user_by_member_code = crud_user.get_user_by_member_code(db, member_code=member_code_filter)
        if user_by_member_code:
            user_id_to_filter = user_by_member_code.id
        else:
            return []

    history_from_db = crud_attendance.get_admin_all_completed_attendance_history(
        db,
        skip=skip,
        limit=limit,
        filter_member_code=member_code_filter,
        start_date=final_start_datetime,
        end_date=final_end_datetime
    )

    formatted_history = []
    for session in history_from_db:
        entry_time_vietnam: Optional[str] = None
        exit_time_vietnam: Optional[str] = None

        if session.entry_time:
            # Bước 1: Gắn múi giờ UTC cho đối tượng datetime (giả định nó là naive UTC từ DB)
            entry_time_utc_aware = session.entry_time.replace(tzinfo=utc)
            # Bước 2: Chuyển đổi sang múi giờ Việt Nam
            entry_time_vietnam_aware = entry_time_utc_aware.astimezone(VIETNAM_TIMEZONE)
            # Bước 3: Định dạng thành chuỗi theo kiểu "MM/DD/YYYY, HH:MM:SS AM/PM"
            entry_time_vietnam = entry_time_vietnam_aware.strftime("%m/%d/%Y, %I:%M:%S %p")

        if session.exit_time:
            exit_time_utc_aware = session.exit_time.replace(tzinfo=utc)
            exit_time_vietnam_aware = exit_time_utc_aware.astimezone(VIETNAM_TIMEZONE)
            exit_time_vietnam = exit_time_vietnam_aware.strftime("%m/%d/%Y, %I:%M:%S %p")
        
        formatted_history.append(
            attendance_schemas.AttendanceSession(
                id=session.id,
                user_id=session.user_id,
                entry_time=entry_time_vietnam,
                exit_time=exit_time_vietnam,
                duration_minutes=session.duration_minutes
            )
        )
    return formatted_history