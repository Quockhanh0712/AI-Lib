# generate_hash.py
from passlib.context import CryptContext

# Ensure this is the same context setup as your backend uses for verifying
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# CHOOSE A SIMPLE, MEMORABLE PLAIN-TEXT PASSWORD FOR TESTING
plain_password = "adminpassword" # Or "test123" or "login123" - something you'll remember

hashed_password = pwd_context.hash(plain_password)

print(f"Plain password: {plain_password}")
print(f"Use this BCRYPT HASHED password for the 'admin' user in the database: {hashed_password}")