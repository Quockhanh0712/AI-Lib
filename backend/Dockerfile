# D:\AI-Lib\backend\Dockerfile

# Sử dụng image Python làm base
FROM python:3.9-slim-buster

# Thiết lập thư mục làm việc bên trong container
WORKDIR /usr/src/app

# Copy file requirements.txt và cài đặt các thư viện
# Điều này giúp tận dụng cache của Docker layer nếu requirements.txt không thay đổi
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# MỚI: Cài đặt thư viện MySQL Connector
RUN pip install pymysql

# Copy toàn bộ mã nguồn ứng dụng vào thư mục làm việc
COPY . .

# Expose cổng mà ứng dụng FastAPI sẽ lắng nghe
EXPOSE 8000

# Lệnh để chạy ứng dụng FastAPI bằng Uvicorn
# Điều chỉnh 'main:app' nếu tên file và biến FastAPI của bạn khác
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
