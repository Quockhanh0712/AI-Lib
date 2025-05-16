# app/crud/crud_attendance.py
from sqlalchemy.orm import Session
from sqlalchemy import func # Để dùng hàm count
from app.db import models
# from app.schemas import attendance as attendance_schemas # Không cần trực tiếp ở đây
from typing import List, Optional
from datetime import datetime, timedelta # Thêm timedelta

def create_attendance_session(db: Session, user_id: int) -> models.AttendanceSession:
    """Tạo một phiên điểm danh mới khi user check-in."""
    db_session = models.AttendanceSession(user_id=user_id, entry_time=datetime.now())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_open_attendance_session_by_user_id(db: Session, user_id: int) -> Optional[models.AttendanceSession]:
    """Lấy phiên điểm danh đang mở (chưa checkout) của một user cụ thể."""
    return db.query(models.AttendanceSession).filter(
        models.AttendanceSession.user_id == user_id,
        models.AttendanceSession.exit_time == None # Trong SQLAlchemy, so sánh với None dùng ==
    ).first()

def get_all_open_attendance_sessions_with_user_info(db: Session) -> list:
    """
    Lấy tất cả các phiên đang mở cùng với thông tin user.
    Trả về list các tuple (AttendanceSession, User).
    """
    return db.query(models.AttendanceSession, models.User).\
        join(models.User, models.AttendanceSession.user_id == models.User.id).\
        filter(models.AttendanceSession.exit_time == None).\
        order_by(models.AttendanceSession.entry_time.desc()).all()

def checkout_attendance_session(db: Session, session_id: int, user_id_from_code: int) -> Optional[models.AttendanceSession]:
    """
    Checkout một phiên điểm danh.
    user_id_from_code là ID của user được xác minh qua việc nhập lại member_code.
    """
    db_session = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.id == session_id,
        models.AttendanceSession.exit_time == None # Chỉ checkout phiên đang mở
    ).first()

    if not db_session:
        return None # Phiên không tồn tại hoặc đã checkout

    # Kiểm tra xem user_id của phiên có khớp với user_id được xác minh qua member_code không
    if db_session.user_id != user_id_from_code:
        return "mismatch" # Trả về một giá trị đặc biệt để router biết là mã không khớp

    db_session.exit_time = datetime.now()
    # Tính toán thời lượng
    if db_session.entry_time and db_session.exit_time:
        duration = db_session.exit_time - db_session.entry_time
        db_session.duration_minutes = int(duration.total_seconds() / 60)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_user_completed_attendance_history(db: Session, user_id: int, skip: int = 0, limit: int = 20) -> List[models.AttendanceSession]:
    """Lấy lịch sử các phiên đã hoàn thành (đã checkout) của một user."""
    return db.query(models.AttendanceSession).filter(
        models.AttendanceSession.user_id == user_id,
        models.AttendanceSession.exit_time != None
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
    query = db.query(models.AttendanceSession).join(models.User).filter(models.AttendanceSession.exit_time != None)

    if filter_member_code:
        query = query.filter(models.User.member_code == filter_member_code)
    if start_date:
        query = query.filter(models.AttendanceSession.entry_time >= start_date)
    if end_date:
        # Để bao gồm cả ngày cuối cùng, ta sẽ lấy đến hết ngày đó
        query = query.filter(models.AttendanceSession.entry_time < (end_date + timedelta(days=1)))

    return query.order_by(models.AttendanceSession.entry_time.desc()).offset(skip).limit(limit).all()