# backend/crud/crud_attendance.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from db import models # <-- Sửa lại import models nếu cần, tùy thuộc vào cấu trúc dự án của bạn
from typing import List, Optional
from datetime import datetime, timedelta, timezone # <-- Đảm bảo import timezone từ datetime
# import pytz # Không cần pytz ở đây nếu chỉ dùng datetime.timezone.utc

def create_attendance_session(db: Session, user_id: int) -> models.AttendanceSession:
    """Tạo một bản ghi session mới khi user check-in."""
    db_session = models.AttendanceSession(user_id=user_id, entry_time=datetime.now(timezone.utc))
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_open_attendance_session_by_user_id(db: Session, user_id: int) -> Optional[models.AttendanceSession]:
    """Lấy bản ghi session đang mở (exit_time is NULL) của một user cụ thể."""
    return db.query(models.AttendanceSession).filter(
        models.AttendanceSession.user_id == user_id,
        models.AttendanceSession.exit_time.is_(None) # Kiểm tra exit_time is NULL
    ).first()

# DÙNG HÀM NÀY ĐỂ LẤY DANH SÁCH NGƯỜI ĐANG TRONG THƯ VIỆN
def get_all_open_attendance_sessions_with_user_info(db: Session) -> List[tuple[models.AttendanceSession, models.User]]:
    """
    Lấy tất cả các bản ghi session đang mở (exit_time is NULL) cùng với thông tin user.
    Đây là hàm dùng cho /machine/current-members/
    """
    return db.query(models.AttendanceSession, models.User).\
        join(models.User, models.AttendanceSession.user_id == models.User.id).\
        filter(models.AttendanceSession.exit_time.is_(None)).\
        order_by(models.AttendanceSession.entry_time.desc()).\
        options(joinedload(models.AttendanceSession.user_session_owner)).all()


def get_attendance_session(db: Session, session_id: int) -> Optional[models.AttendanceSession]:
    """Lấy một bản ghi session cụ thể theo ID."""
    return db.query(models.AttendanceSession).filter(models.AttendanceSession.id == session_id).first()

def checkout_attendance_session(db: Session, session_id: int, user_id_from_code: int) -> Optional[models.AttendanceSession]:
    """
    Checkout một bản ghi session bằng cách đặt exit_time và tính duration_minutes.
    session_id là ID của bản ghi session cần đóng.
    user_id_from_code là ID của user được xác minh qua member_code.
    """
    db_session = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.id == session_id,
        models.AttendanceSession.exit_time.is_(None) # Chỉ checkout bản ghi đang mở
    ).first()

    if not db_session:
        return None # Bản ghi không tồn tại hoặc đã checkout (nếu đã checkout thì exit_time không phải NULL)

    # VỊ TRÍ ĐÚNG CỦA ĐOẠN KIỂM TRA user_id_from_code
    if db_session.user_id != user_id_from_code:
        # Bạn có thể raise HTTPException ở router thay vì trả về "mismatch" string
        # nhưng nếu hàm này trả về string thì router phải xử lý nó.
        return "mismatch" # Trả về một giá trị đặc biệt nếu mã không khớp

    # Cập nhật exit_time cho session này.
    # Đây là một aware datetime object (UTC)
    db_session.exit_time = datetime.now(timezone.utc)

    # Tính duration_minutes
    # Đảm bảo entry_time là aware UTC trước khi trừ
    if db_session.entry_time: # Kiểm tra xem entry_time có tồn tại không
        entry_time_for_calc = db_session.entry_time
        
        # Nếu entry_time từ DB là naive (không có múi giờ), hãy gắn múi giờ UTC cho nó
        if entry_time_for_calc.tzinfo is None:
            entry_time_for_calc = entry_time_for_calc.replace(tzinfo=timezone.utc)
        
        # db_session.exit_time đã được gán và là aware UTC, nên không cần xử lý thêm cho nó
        
        time_difference = db_session.exit_time - entry_time_for_calc
        db_session.duration_minutes = int(time_difference.total_seconds() / 60)
    else:
        db_session.duration_minutes = 0 # Trường hợp entry_time không tồn tại, mặc định duration là 0

    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_user_completed_attendance_history(db: Session, user_id: int, skip: int = 0, limit: int = 20) -> List[models.AttendanceSession]:
    """Lấy lịch sử các bản ghi đã hoàn thành (exit_time is NOT NULL) của một user."""
    return db.query(models.AttendanceSession).filter(
        models.AttendanceSession.user_id == user_id,
        models.AttendanceSession.exit_time.isnot(None) # Kiểm tra exit_time is NOT NULL
    ).order_by(models.AttendanceSession.entry_time.desc()).offset(skip).limit(limit).all()

def get_admin_all_completed_attendance_history(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    filter_member_code: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[models.AttendanceSession]:
    """Admin xem lịch sử đã hoàn thành, có thể lọc."""
    query = db.query(models.AttendanceSession).join(models.User).filter(models.AttendanceSession.exit_time.isnot(None))

    if filter_member_code:
        query = query.filter(models.User.member_code == filter_member_code)
    if start_date:
        query = query.filter(models.AttendanceSession.entry_time >= start_date)
    if end_date:
        query = query.filter(models.AttendanceSession.entry_time < (end_date + timedelta(days=1)))

    return query.order_by(models.AttendanceSession.entry_time.desc()).offset(skip).limit(limit).all()