# Stage 1: Build the React application
FROM node:20-alpine as build-stage
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . .
RUN npm run build # Lệnh build của Vite sẽ tạo ra các file tĩnh trong thư mục 'dist'

# Stage 2: Serve the built application with Nginx
FROM nginx:alpine
# Xóa cấu hình Nginx mặc định để tránh xung đột
RUN rm /etc/nginx/conf.d/default.conf
# Sao chép cấu hình tùy chỉnh của bạn vào vị trí cấu hình Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf 
# Sao chép các file đã build từ build-stage vào thư mục phục vụ của Nginx
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Expose cổng 80 (cổng HTTP mặc định cho máy chủ web)
EXPOSE 80

# Lệnh để khởi động Nginx ở foreground (để Docker container chạy liên tục)
CMD ["nginx", "-g", "daemon off;"]