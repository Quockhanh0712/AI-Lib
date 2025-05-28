# Hệ thống điểm danh thư viện áp dụng AI nhận diện khuôn mặt

## Thành viên nhóm
Hoàng Ngọc Nam : MSV 23020403

Trần Quốc Khánh : MSV 23020387

Nguyễn Văn Huy : MSV 23020379

Nguyễn Anh Kiệt : MSV 23020383

---

## 1. Mục tiêu dự án

Mục tiêu của dự án là xây dựng một hệ thống điểm danh tự động và hiện đại cho thư viện, tích hợp công nghệ nhận diện khuôn mặt bằng AI để ghi nhận việc vào/ra của thành viên. Đồng thời hệ thống cũng cung cấp cho quản trị viên một công cụ hữu ích để quản lý và theo dõi hoạt động của các thành viên.

### Mục tiêu cốt lõi của hệ thống:
- Triển khai nhận diện khuôn mặt để điểm danh vào, và có thể cả điểm danh ra.
- Cung cấp giao diện quản trị để thực hiện đầy đủ thao tác quản lý dữ liệu thành viên.
- Cho phép quản trị viên quản lý dữ liệu khuôn mặt phục vụ cho nhận diện.
- Hiển thị lịch sử điểm danh chi tiết, cả ở mức tổng thể và từng thành viên.
- Hỗ trợ quy trình đăng ký tài khoản mới.
- Đảm bảo truy cập và thao tác của quản trị viên được bảo mật.

---

## 2. Tổng quan kiến trúc hệ thống

Hệ thống gồm các thành phần chính sau:

### Frontend Quản trị viên (React, Vite)
Giao diện web cho quản trị viên thư viện để quản lý thành viên, đăng ký thành viên, xem lịch sử điểm danh và quản lý dữ liệu khuôn mặt.

### Frontend cho người dùng
Giao diện cho phép người dùng thực hiện điểm danh vào/ra thông qua camera và nhập mã thành viên.

### Backend Quản trị viên (FastAPI)
Cung cấp API bảo mật để thực hiện các chức năng quản trị: quản lý thành viên, truy xuất lịch sử điểm danh. Backend này cũng chịu trách nhiệm tạo tài khoản người dùng và gọi dịch vụ AI để trich xuất khuôn mặt.

### Dịch vụ AI (FastAPI)
Dịch vụ backend chuyên xử lý:
- **Ghi nhận khuôn mặt:** Nhận ảnh, trích xuất embedding khuôn mặt và lưu trữ lại.
- **Nhận diện khuôn mặt:** Nhận ảnh thời gian thực, so sánh với dữ liệu đã lưu và trả kết quả nhận dạng.

### Cơ sở dữ liệu (MySQL)
CSDL trung tâm lưu trữ:
- `admin_users`: Tài khoản quản trị
- `users`: Thông tin thành viên thư viện
- `face_embeddings`: Embedding khuôn mặt gắn với thành viên
- `attendance_sessions`: Phiên điểm danh

---

## 3. Các trường hợp sử dụng và chức năng chính

### A. Phía người dùng

#### UC1: Điểm danh vào bằng nhận diện khuôn mặt
- Người dùng tiến đến đối diện camera.
- Dịch vụ AI xử lý ảnh, xác định thành viên từ embedding đã lưu.
- Nếu nhận diện thành công và đã được phê duyệt, tạo phiên điểm danh (ghi nhận thời gian vào).

#### UC2: Hiển thị danh sách thành viên đang trong thư viện
- Hệ thống hiển thị danh sách các thành viên hiện đang có mặt.

#### UC3: Điểm danh ra
- Người dùng chọn tùy chọn checkout.
- Hệ thống xác minh và ghi nhận thời gian rời đi.

#### UC4: Xem lịch sử chuyên cần cá nhân
- Người dùng vừa điểm danh vào thành công (đang ở màn hình sau UC1).
- Người dùng có thể xem lại danh sách các lần đã vào và ra thư viện của mình.

---

### B. Phía quản trị viên (Frontend & Backend)

#### UC5: Đăng nhập quản trị viên
- Đăng nhập bảo mật để truy cập giao diện quản trị.

#### UC6: Quản lý thành viên
- **Tạo mới:** Quản trị viên thêm thành viên mới với thông tin và ảnh. Backend gọi dịch vụ AI để ghi nhận khuôn mặt.
- **Xem danh sách:** Xem danh sách thành viên với chức năng tìm kiếm/lọc.
- **Chỉnh sửa:** Sửa thông tin thành viên; có thể thêm ảnh khuôn mặt mới.
- **Xoá:** Xoá tài khoản thành viên khỏi hệ thống.

#### UC7: Xem lịch sử điểm danh (tổng thể)
- Xem danh sách tất cả phiên điểm danh đã hoàn tất.
- Lọc theo mã thành viên, khoảng thời gian, v.v.
- @router.post("/login", response_model=admin_schemas.AdminUser)

#### UC8: Xem lịch sử điểm danh của một thành viên cụ thể
- Chọn một thành viên và xem lịch sử điểm danh riêng của họ.

#### UC9: Đăng xuất quản trị viên
- Đăng xuất khỏi giao diện quản trị.



## 4. Yêu cầu hệ thống:
 - đã cài đặt docker 
 - Kiểm tra bằng lệnh: docker --version docker compose version


## 5. Cách sử dụng: 
 - gõ lệnh : docker pull 
    + docker pull huy332005/frontend-admin-app:1.0
    + docker pull huy332005/frontend-user-react-app:1.0
    + docker pull huy332005/backend-api-service:1.0
    + docker pull huy332005/backend-ai-service:1.0
 - rồi lệnh : docker compose up -d
 - Giao diện Admin: http://localhost:8083
 - Giao diện Người dùng: http://localhost:8082
## 6. Link docker-hub : https://hub.docker.com/repositories/huy332005

## 7. Kết quả kỳ vọng
 - Người dùng có thể nhanh chóng nhận diện và đăng nhập từ webcam.
 - Giao diện admin trực quan, dễ quản lý.
 - Backend phản hồi nhanh, hỗ trợ tải lớn và dễ mở rộng.
 - Dễ dàng deploy, scale khi cần thiết.
---
### Chi tiết hệ thống xem tại 'báo cáo hệ thống.pdf'
