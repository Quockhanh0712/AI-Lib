# D:\AI-Lib\frontend-user-react\Dockerfile

# --- Giai đoạn 1: Build ứng dụng React/Vite ---
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install --force-immutable

COPY . .

# MỚI: Nhận biến môi trường từ build-arg
ARG VITE_BACKEND_API_URL
ENV VITE_BACKEND_API_URL=$VITE_BACKEND_API_URL

# Build ứng dụng Vite
RUN npm run build

# --- Giai đoạn 2: Phục vụ ứng dụng bằng Nginx ---
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
