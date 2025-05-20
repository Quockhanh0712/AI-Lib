# app/crud/crud_request.py
from sqlalchemy.orm import Session
from app.db import models
from app.schemas import request as request_schemas
from app.schemas import user as user_schemas # Cần để tạo user khi approve
from app.crud import crud_user # Cần để tạo user và kiểm tra trùng lặp
from typing import List, Optional
from datetime import datetime
import os # Để xử lý photo_path sau này

def create_registration_request(db: Session, request: request_schemas.RegistrationRequestCreate) -> models.RegistrationRequest:
    """Tạo một yêu cầu đăng ký mới."""
    # Kiểm tra xem requested_member_code đã được yêu cầu trước đó và đang pending không
    existing_pending_request = db.query(models.RegistrationRequest).filter(
        models.RegistrationRequest.requested_member_code == request.requested_member_code,
        models.RegistrationRequest.status == 'Pending'
    ).first()
    if existing_pending_request:
        raise ValueError(f"Member code {request.requested_member_code} already has a pending request.")

    # Kiểm tra xem requested_member_code đã tồn tại trong bảng users chưa
    if crud_user.get_user_by_member_code(db, request.requested_member_code):
        raise ValueError(f"Member code {request.requested_member_code} already exists as an active user.")

    db_request = models.RegistrationRequest(
        requested_member_code=request.requested_member_code,
        full_name=request.full_name,
        email=request.email,
        phone_number=request.phone_number,
        photo_path=request.photo_path # Backend sẽ cần xử lý lưu file ảnh từ UploadFile và lấy path thực tế
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

def get_pending_registration_requests(db: Session, skip: int = 0, limit: int = 100) -> List[models.RegistrationRequest]:
    """Lấy danh sách các yêu cầu đăng ký đang chờ xử lý."""
    return db.query(models.RegistrationRequest).filter(models.RegistrationRequest.status == 'Pending').order_by(models.RegistrationRequest.request_time.asc()).offset(skip).limit(limit).all()

def get_registration_request_by_id(db: Session, request_id: int) -> Optional[models.RegistrationRequest]:
    """Lấy một yêu cầu đăng ký theo ID."""
    return db.query(models.RegistrationRequest).filter(models.RegistrationRequest.id == request_id).first()

def process_approve_registration_request(db: Session, db_request: models.RegistrationRequest, admin_id: int) -> tuple[Optional[models.RegistrationRequest], Optional[str]]:
    """
    Xử lý việc phê duyệt một yêu cầu.
    Trả về (request đã cập nhật, None) nếu thành công, hoặc (None, "Thông báo lỗi") nếu thất bại.
    db_request là đối tượng RegistrationRequest đã được lấy từ DB.
    """
    if db_request.status != 'Pending':
        return None, "Request is not in pending state."

    # Kiểm tra lại member_code và email có bị trùng trong bảng users không
    # (Phòng trường hợp có request khác được approve trong lúc admin đang xem)
    if crud_user.get_user_by_member_code(db, db_request.requested_member_code):
        db_request.status = 'Rejected' # Tự động reject nếu code đã tồn tại
        db_request.processed_by_admin_id = admin_id
        db_request.processing_time = datetime.now()
        db.commit()
        db.refresh(db_request)
        return db_request, f"Member code {db_request.requested_member_code} already exists. Request auto-rejected."

    if db_request.email and crud_user.get_user_by_email(db, db_request.email):
        db_request.status = 'Rejected' # Tự động reject nếu email đã tồn tại
        db_request.processed_by_admin_id = admin_id
        db_request.processing_time = datetime.now()
        db.commit()
        db.refresh(db_request)
        return db_request, f"Email {db_request.email} already exists. Request auto-rejected."

    # Tạo user mới từ thông tin request
    new_user_schema = user_schemas.UserCreate(
        member_code=db_request.requested_member_code,
        full_name=db_request.full_name,
        email=db_request.email,
        phone_number=db_request.phone_number
    )
    created_user = crud_user.create_user(db, user=new_user_schema, status="Approved")

    # --- PHẦN TÍCH HỢP AI SẼ Ở ĐÂY ---
    # 1. Lấy ảnh từ db_request.photo_path
    # 2. Gọi DeepFace để trích xuất embedding
    # 3. Gọi crud_user.create_user_face_embedding(db, user_id=created_user.id, embedding_vector=...)
    # Nhớ xử lý lỗi nếu không trích xuất được embedding
    # Nếu lỗi AI, có thể không tạo user, hoặc tạo user nhưng đánh dấu là chưa có embedding
    # và cập nhật request.status là 'Pending_AI_Error' chẳng hạn.
    # Tạm thời bỏ qua bước này.
    # --- KẾT THÚC PHẦN AI ---

    # Cập nhật trạng thái của request
    db_request.status = 'Approved'
    db_request.processed_by_admin_id = admin_id
    db_request.processing_time = datetime.now()
    db.commit()
    db.refresh(db_request)

    # (Tùy chọn) Xóa file ảnh tạm từ db_request.photo_path ở đây
    # try:
    #     if os.path.exists(db_request.photo_path):
    #         os.remove(db_request.photo_path)
    # except OSError as e:
    #     print(f"Error deleting temp photo {db_request.photo_path}: {e}")

    return db_request, None # Thành công

def process_reject_registration_request(db: Session, db_request: models.RegistrationRequest, admin_id: int) -> Optional[models.RegistrationRequest]:
    """
    Xử lý việc từ chối một yêu cầu.
    db_request là đối tượng RegistrationRequest đã được lấy từ DB.
    """
    if db_request.status != 'Pending':
        return None # Chỉ reject được request đang pending

    db_request.status = 'Rejected'
    db_request.processed_by_admin_id = admin_id
    db_request.processing_time = datetime.now()
    db.commit()
    db.refresh(db_request)
    return db_request