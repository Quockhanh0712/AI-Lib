# app/initial_data.py

import sys
import os
from datetime import datetime, timedelta # Import timedelta
from sqlalchemy.orm import Session

# Thêm thư mục gốc của ứng dụng vào sys.path để import các module khác
# Điều này cần thiết khi chạy script này độc lập
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import các module cần thiết từ ứng dụng của bạn
# Đảm bảo các import này đúng với cấu trúc thư mục của bạn
from db.database import SessionLocal, engine, Base # Import Base và engine để tạo bảng nếu cần
from db.models import AdminUser, User, RegistrationRequest, AttendanceSession, FaceEmbedding, UserStatus

# --- TẠO BẢNG NẾU CHƯA TỒN TẠI ---
# Mặc dù hàm create_database_tables() được gọi khi app khởi động,
# gọi lại ở đây đảm bảo script này có thể chạy độc lập để thiết lập DB ban đầu.
# Tuy nhiên, nếu bạn chắc chắn app đã chạy và tạo bảng, có thể bỏ qua phần này.
print("Ensuring database tables exist...")
# Base.metadata.create_all(bind=engine)
# print("Database tables checked/created.")


# --- DỮ LIỆU MẪU TỪ FILE SQL CỦA BẠN ---
# Chuyển đổi dữ liệu INSERT từ SQL sang cấu trúc Python

# Dữ liệu cho admin_users
# Lưu ý: password_hash ở đây vẫn là '123' như trong SQL,
# trong ứng dụng thực tế cần dùng thư viện băm mật khẩu.
admin_users_data = [
    {"username": "admin", "password_hash": "123", "full_name": "Quản Trị Viên Hệ Thống", "contact_info": "admin@example.com"},
]

# Dữ liệu cho registration_requests
# Sử dụng Enum UserStatus cho cột status
registration_requests_data = [
    {"requested_member_code": "SV001", "full_name": "Nguyễn Văn An", "email": "an.nv@example.com", "phone_number": "0901234567", "photo_path": "/path/to/temp/an_nv.jpg", "status": UserStatus.Pending},
    {"requested_member_code": "SV002", "full_name": "Trần Thị Bình", "email": "binh.tt@example.com", "phone_number": "0907654321", "photo_path": "/path/to/temp/binh_tt.jpg", "status": UserStatus.Pending},
    # Giả định admin_users.id của 'admin' là 1 sau khi chèn
    {"requested_member_code": "GV001", "full_name": "Lê Văn Cường", "email": "cuong.lv@example.com", "phone_number": "0912345678", "photo_path": "/path/to/temp/cuong_lv.jpg", "status": UserStatus.Approved, "processed_by_admin_id": 1, "processing_time": datetime.utcnow() - timedelta(days=1)}, # Sử dụng datetime và timedelta
    {"requested_member_code": "SV003", "full_name": "Phạm Thị Dung", "email": "dung.pt@example.com", "phone_number": "0987654321", "photo_path": "/path/to/temp/dung_pt.jpg", "status": UserStatus.Rejected, "processed_by_admin_id": 1, "processing_time": datetime.utcnow() - timedelta(days=2)}, # Sử dụng datetime và timedelta
]

# Dữ liệu cho users
# Sử dụng Enum UserStatus cho cột status
users_data = [
    # Giả sử GV001 từ registration_requests đã được phê duyệt và tạo user.id = 1
    {"member_code": "GV001", "full_name": "Lê Văn Cường", "email": "cuong.lv@example.com", "phone_number": "0912345678", "status": UserStatus.Approved},
    # Thêm một vài user khác đã được phê duyệt (giả sử Admin thêm trực tiếp)
    {"member_code": "SV100", "full_name": "Tran quoc khanh", "email": "nam.hv@example.com", "phone_number": "0911111111", "status": UserStatus.Approved},
    {"member_code": "SV101", "full_name": "Đỗ Thị Lan", "email": "lan.dt@example.com", "phone_number": "0922222222", "status": UserStatus.Approved},
    {"member_code": "SV102", "full_name": "Vũ Minh Hải", "email": "hai.vm@example.com", "phone_number": "0933333333", "status": UserStatus.Inactive}, # User bị vô hiệu hóa
    # Thêm user 123452 để test endpoint check
    {"member_code": "123452", "full_name": "Test User 123452", "email": "test123452@example.com", "phone_number": "0999999999", "status": UserStatus.Approved},
]

# Dữ liệu cho attendance_sessions
# Cần lấy user_id từ bảng users sau khi chèn
# Tạm thời lưu trữ dữ liệu thô và sẽ ánh xạ user_id sau khi chèn users
attendance_sessions_raw_data = [
    {"member_code": "GV001", "entry_time_offset": timedelta(hours=3), "exit_time_offset": timedelta(hours=1), "duration_minutes": 120}, # Vào 3 tiếng trước, ra 1 tiếng trước
    {"member_code": "SV100", "entry_time_offset": timedelta(minutes=30), "exit_time_offset": None, "duration_minutes": None}, # Vào 30 phút trước, chưa ra
    {"member_code": "SV101", "entry_time_offset": timedelta(days=5, hours=2), "exit_time_offset": timedelta(days=5), "duration_minutes": 120}, # 5 ngày trước
    {"member_code": "SV101", "entry_time_offset": timedelta(days=1, hours=1), "exit_time_offset": timedelta(days=1, minutes=30), "duration_minutes": 30}, # Hôm qua
    {"member_code": "SV100", "entry_time_offset": timedelta(days=2, hours=4), "exit_time_offset": timedelta(days=2, hours=1), "duration_minutes": 180}, # 2 ngày trước
]

# Dữ liệu cho face_embeddings (Nếu có dữ liệu embedding mẫu, thêm vào đây)
# Giả định cấu trúc là { "member_code": "...", "embedding1": "...", "embedding2": "...", "embedding3": "..." }
face_embeddings_raw_data = [
    # Ví dụ:
    # {"member_code": "GV001", "embedding1": "...", "embedding2": "...", "embedding3": "..."},
]


# --- HÀM CHÈN DỮ LIỆU ---
def insert_initial_data():
    db: Session = SessionLocal()
    try:
        print("Inserting initial data...")

        # Chèn Admin Users
        print("Inserting Admin Users...")
        for admin_data in admin_users_data:
            # Kiểm tra xem admin đã tồn tại chưa để tránh chèn trùng
            existing_admin = db.query(AdminUser).filter(AdminUser.username == admin_data["username"]).first()
            if not existing_admin:
                db_admin = AdminUser(**admin_data)
                db.add(db_admin)
                print(f" - Added admin: {admin_data['username']}")
            else:
                print(f" - Admin already exists: {admin_data['username']}")
        db.commit()
        # Lấy admin_id sau khi chèn (giả định admin 'admin' có id 1)
        admin_user = db.query(AdminUser).filter(AdminUser.username == "admin").first()
        admin_id = admin_user.id if admin_user else None


        # Chèn Registration Requests
        print("Inserting Registration Requests...")
        for req_data in registration_requests_data:
             # Cập nhật processed_by_admin_id nếu admin_id tồn tại
            if req_data.get("processed_by_admin_id") == 1 and admin_id is not None:
                 req_data["processed_by_admin_id"] = admin_id

            # Kiểm tra xem yêu cầu đã tồn tại chưa
            existing_req = db.query(RegistrationRequest).filter(
                RegistrationRequest.requested_member_code == req_data["requested_member_code"],
                RegistrationRequest.full_name == req_data["full_name"] # Có thể thêm điều kiện khác để kiểm tra trùng lặp
            ).first()
            if not existing_req:
                db_req = RegistrationRequest(**req_data)
                db.add(db_req)
                print(f" - Added registration request for: {req_data['requested_member_code']}")
            else:
                 print(f" - Registration request already exists for: {req_data['requested_member_code']}")
        db.commit()


        # Chèn Users
        print("Inserting Users...")
        # Lưu trữ ánh xạ member_code -> user_id để dùng cho attendance_sessions và face_embeddings
        user_id_map = {}
        for user_data in users_data:
             # Kiểm tra xem user đã tồn tại chưa
            existing_user = db.query(User).filter(User.member_code == user_data["member_code"]).first()
            if not existing_user:
                db_user = User(**user_data)
                db.add(db_user)
                db.flush() # Flush để có user.id trước khi commit
                user_id_map[db_user.member_code] = db_user.id
                print(f" - Added user: {user_data['member_code']} - {user_data['full_name']}")
            else:
                user_id_map[existing_user.member_code] = existing_user.id
                print(f" - User already exists: {user_data['member_code']}")
        db.commit() # Commit sau khi thêm tất cả users


        # Chèn Attendance Sessions
        print("Inserting Attendance Sessions...")
        for session_data in attendance_sessions_raw_data:
            member_code = session_data["member_code"]
            user_id = user_id_map.get(member_code) # Lấy user_id từ map

            if user_id is not None:
                entry_time = datetime.utcnow() - session_data["entry_time_offset"]
                exit_time = datetime.utcnow() - session_data["exit_time_offset"] if session_data["exit_time_offset"] is not None else None
                duration_minutes = session_data["duration_minutes"]

                # Kiểm tra xem session đã tồn tại chưa (có thể phức tạp hơn tùy logic)
                # Tạm thời bỏ qua kiểm tra trùng lặp session để đơn giản
                db_session = AttendanceSession(
                    user_id=user_id,
                    entry_time=entry_time,
                    exit_time=exit_time,
                    duration_minutes=duration_minutes
                )
                db.add(db_session)
                print(f" - Added attendance session for user_id {user_id} ({member_code})")
            else:
                print(f" - Skipping attendance session for unknown member_code: {member_code}")
        db.commit()


        # Chèn Face Embeddings
        print("Inserting Face Embeddings...")
        for embedding_data in face_embeddings_raw_data:
            member_code = embedding_data["member_code"]
            user_id = user_id_map.get(member_code) # Lấy user_id từ map

            if user_id is not None:
                 # Kiểm tra xem embedding cho user này đã tồn tại chưa (unique=True trên user_id)
                existing_embedding = db.query(FaceEmbedding).filter(FaceEmbedding.user_id == user_id).first()
                if not existing_embedding:
                    db_embedding = FaceEmbedding(
                        user_id=user_id,
                        embedding1=embedding_data.get("embedding1"),
                        embedding2=embedding_data.get("embedding2"),
                        embedding3=embedding_data.get("embedding3")
                    )
                    db.add(db_embedding)
                    print(f" - Added face embedding for user_id {user_id} ({member_code})")
                else:
                    print(f" - Face embedding already exists for user_id {user_id} ({member_code})")
            else:
                print(f" - Skipping face embedding for unknown member_code: {member_code}")
        db.commit()


        print("Initial data insertion complete.")

    except Exception as e:
        db.rollback() # Rollback nếu có lỗi
        print(f"An error occurred during initial data insertion: {e}")
        import traceback
        traceback.print_exc() # In ra traceback chi tiết

    finally:
        db.close()


# --- Chạy hàm chèn dữ liệu khi script được thực thi ---
if __name__ == "__main__":
    insert_initial_data()

