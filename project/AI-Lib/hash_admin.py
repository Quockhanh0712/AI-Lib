from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
plain_password_to_hash = "123" # Or your desired admin password
hashed_password_for_db = pwd_context.hash(plain_password_to_hash)
print(f"Hashed password for admin: {hashed_password_for_db}")