# D:\AI-Lib\app\Dockerfile

# Sử dụng một image Python cơ bản
FROM python:3.9-slim-buster

# Cài đặt các gói hệ thống cần thiết cho việc biên dịch mysqlclient
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libmariadb-dev && \
    rm -rf /var/lib/apt/lists/*

# Đặt thư mục làm việc bên trong container
WORKDIR /usr/src/app

# Sao chép file requirements.txt vào thư mục làm việc
COPY requirements.txt .

# Cài đặt các thư viện Python
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn từ thư mục hiện tại trên host (D:\AI-Lib\app)
# vào thư mục làm việc trong container (/usr/src/app)
# Dựa trên cấu trúc file của bạn, code nguồn (main.py, __init__.py, các thư mục con)
# nằm trực tiếp trong D:\AI-Lib\app
COPY . .

# Mở cổng 8000 (cổng mà FastAPI/Uvicorn lắng nghe)
EXPOSE 8000

# Lệnh để chạy ứng dụng FastAPI
# Vì main.py và __init__.py nằm trực tiếp trong WORKDIR (/usr/src/app),
# Python sẽ coi /usr/src/app là package gốc.
# Do đó, lệnh import đúng là main:app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
