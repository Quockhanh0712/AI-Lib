# Dockerfile for Frontend Admin (frontend-admin/)
# Đặt file này bên trong thư mục frontend-admin/

# --- Giai đoạn 1: Build ứng dụng React/Vite ---
# Sử dụng image Node.js làm base cho giai đoạn build
FROM node:20-alpine AS builder

# Thiết lập thư mục làm việc bên trong container
WORKDIR /app

# Copy package.json và package-lock.json (hoặc yarn.lock)
COPY package*.json ./

# Cài đặt dependencies
RUN npm install --force-immutable

# Copy toàn bộ mã nguồn ứng dụng vào thư mục làm việc
COPY . .

# Build ứng dụng Vite
# Lệnh build có thể khác tùy vào script trong package.json của bạn (thường là 'build')
RUN npm run build

# --- Giai đoạn 2: Phục vụ ứng dụng bằng Nginx ---
# Sử dụng image Nginx Alpine làm base cho giai đoạn chạy
FROM nginx:alpine

# Copy file cấu hình Nginx tùy chỉnh (nếu có)
COPY nginx.conf /etc/nginx/nginx.conf

# Copy các file tĩnh đã build từ giai đoạn builder vào thư mục phục vụ của Nginx
# Thư mục mặc định của Vite là /app/dist
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose cổng mà Nginx sẽ lắng nghe
EXPOSE 80

# Lệnh mặc định để khởi động Nginx
CMD ["nginx", "-g", "daemon off;"]

# Lưu ý:
# - Đảm bảo bạn có file .dockerignore trong thư mục frontend-admin/ để loại trừ node_modules và các file không cần thiết.
# - Kiểm tra lệnh build trong package.json của bạn và điều chỉnh RUN npm run build nếu cần.
# - Nếu thư mục output của lệnh build không phải là 'dist', hãy thay đổi đường dẫn trong lệnh COPY.
