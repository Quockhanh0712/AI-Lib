// frontend-admin/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173, // Frontend port
    proxy: {
      '/api': { // Khi request bắt đầu với /api
        target: 'http://localhost:8000', // Chuyển hướng đến backend đang chạy trên máy host
        changeOrigin: true, // Cần cho tên miền ảo (virtual hosted sites)
        rewrite: (path) => path.replace(/^\/api/, '') // Xóa /api khỏi path trước khi gửi đến backend
      }
    }
  }
})