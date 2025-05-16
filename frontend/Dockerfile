# frontend/Dockerfile
# Sử dụng image Nginx phiên bản alpine (nhỏ gọn)
FROM nginx:alpine

# Xóa cấu hình Nginx mặc định
RUN rm /etc/nginx/conf.d/default.conf

# Sao chép file cấu hình Nginx tùy chỉnh của bạn vào container
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Sao chép các file frontend (HTML, CSS, JS) vào thư mục mà Nginx sẽ phục vụ
# Các file này sẽ nằm trong thư mục 'public' trên máy tính của bạn
COPY public/ /usr/share/nginx/html

# Mở cổng 80 (cổng HTTP mặc định của Nginx)
EXPOSE 80

# Lệnh mặc định để Nginx chạy ở chế độ nền
CMD ["nginx", "-g", "daemon off;"]