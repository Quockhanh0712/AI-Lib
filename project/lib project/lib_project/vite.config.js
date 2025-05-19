// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173, // Your frontend port
    proxy: {
      // Proxy API requests from /api to your backend
      '/api': {
        target: 'http://127.0.0.1:8000', // Your backend server
        changeOrigin: true, // Needed for virtual hosted sites
        rewrite: (path) => path.replace(/^\/api/, '') // Remove /api prefix before forwarding
      }
    }
  }
})