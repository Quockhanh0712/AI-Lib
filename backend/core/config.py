# app/core/config.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    """
    Lớp này định nghĩa các cài đặt cho ứng dụng.
    Pydantic sẽ tự động đọc các giá trị từ biến môi trường
    có tên trùng với tên thuộc tính.
    """
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./default_test.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "8f4b3e2a9c1d6f7e0b2a4c8d9e3f5a7b1c9d2e4f6a8b0c3d5e7f")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

settings = Settings()