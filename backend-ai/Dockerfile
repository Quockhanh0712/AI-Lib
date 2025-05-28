# Sử dụng một base image Python
FROM python:3.11-slim-buster 

# Cài đặt các thư viện hệ thống cần thiết cho OpenCV
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libxext6 \
    libsm6 \
    libxrender1 \
    libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Sao chép tệp requirements.txt vào thư mục làm việc
# Điều này quan trọng để ensure requirements.txt có trong container TRƯỚC KHI cài đặt
COPY requirements.txt .

# Cài đặt các phụ thuộc Python
# --no-cache-dir giúp giảm kích thước image
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn ứng dụng vào thư mục làm việc
COPY . .

# Định nghĩa cổng mà ứng dụng FastAPI sẽ lắng nghe
EXPOSE 8000

# Lệnh để chạy ứng dụng bằng Uvicorn
# Đảm bảo lệnh này khớp với cách bạn muốn chạy ứng dụng của mình
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]