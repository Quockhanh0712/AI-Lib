import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    // Cổng mà frontend-admin sẽ chạy trên host, khớp với cổng đầu tiên trong "ports" của docker-compose.yml
    port: 8083, 
    proxy: {
      // Khi một request từ frontend bắt đầu bằng '/api'
      '/api': { 
        // Chuyển hướng request đến dịch vụ backend trong Docker network.
        // 'backend' là tên dịch vụ của bạn trong docker-compose.yml.
        target: 'http://backend:8000', 
        changeOrigin: true, // Quan trọng để thay đổi header Host của request thành target host
        // Xóa tiền tố '/api' khỏi đường dẫn trước khi chuyển tiếp đến backend.
        // Ví dụ: /api/admin/login sẽ trở thành /admin/login ở backend.
        rewrite: (path) => path.replace(/^\/api/, ''), 
        // Cấu hình để xử lý cookies, rất quan trọng cho xác thực session.
        // Đảm bảo cookie được thiết lập cho 'localhost' (domain của frontend)
        // thay vì domain nội bộ của Docker ('backend').
        cookieDomainRewrite: 'localhost', 
        // secure: false, // Chỉ dùng cho môi trường dev nếu backend không có HTTPS
        // ws: true, // Cho WebSocket proxy nếu bạn có dùng
      },
    },
  },
});
