from passlib.context import CryptContext

# Khởi tạo context giống như trong app/crud/crud_admin.py
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

plain_password_to_hash = "123"  # Mật khẩu bạn muốn dùng để đăng nhập
hashed_password_for_db = pwd_context.hash(plain_password_to_hash)

print(f"Mật khẩu gốc: {plain_password_to_hash}")
print(f"Mật khẩu đã băm (để lưu vào DB): {hashed_password_for_db}")