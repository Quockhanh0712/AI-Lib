# frontend-admin/Dockerfile

# Stage 1: Build the React application
FROM node:18-alpine AS builder

WORKDIR /app

COPY package.json ./
COPY package-lock.json ./
# Hoặc yarn.lock nếu bạn dùng yarn
# COPY yarn.lock ./

RUN npm install --frozen-lockfile # Cài đặt dependencies

COPY . .

ENV VITE_BACKEND_API_URL=/api

RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:alpine

# Copy the Nginx configuration -- ĐẢM BẢO ĐƯỜNG DẪN NÀY ĐÚNG
COPY nginx.conf /etc/nginx/conf.d/default.conf 

# Copy the built React app from the builder stage -- ĐẢM BẢO ĐƯỜNG DẪN NÀY ĐÚNG
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]