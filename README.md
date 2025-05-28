# Hệ thống điểm danh thư viện thông minh bằng nhận diện khuôn mặt

## Thành viên nhóm
- Hoàng Ngọc Nam : MSV 23020403
- Trần Quốc Khánh : MSV 23020387
- Nguyễn Văn Huy : MSV 23020379
- Nguyễn Anh Kiệt : MSV 23020383
---

## Giới thiệu

Đây là một hệ thống điểm danh hiện đại sử dụng công nghệ nhận diện khuôn mặt để ghi nhận việc ra/vào của thành viên thư viện. Hệ thống được thiết kế nhằm tự động hóa quy trình điểm danh, nâng cao độ chính xác và cải thiện trải nghiệm người dùng cũng như khả năng quản lý của quản trị viên.

## Tính năng chính

- **Điểm danh tự động bằng khuôn mặt** (Check-in / Check-out).
- **Bảng điều khiển quản trị viên** với đầy đủ chức năng quản lý thành viên (thêm/sửa/xoá).
- **Quản lý dữ liệu khuôn mặt** phục vụ nhận diện.
- **Xem lịch sử điểm danh chi tiết**, có thể lọc theo mã thành viên hoặc thời gian.
- **Xác thực bảo mật** dành cho quản trị viên.
- **Hỗ trợ quy trình đăng ký thành viên mới**, yêu cầu phê duyệt bởi quản trị viên.

## Kiến trúc hệ thống

- **Frontend Quản trị viên:** React + Vite.
- **Frontend Kiosk người dùng:** React hoặc HTML/JS đơn giản.
- **Backend Quản trị viên:** FastAPI (Python) xử lý xác thực, quản lý dữ liệu, điểm danh.
- **Dịch vụ AI:** FastAPI + DeepFace/ArcFace nhận diện và ghi nhận khuôn mặt.
- **Cơ sở dữ liệu:** MySQL (sử dụng SQLAlchemy ORM).

## Luồng hoạt động chính

1. Thành viên tiến đến kiosk, quét khuôn mặt.
2. Hệ thống AI xác định thành viên, xác nhận mã.
3. Thời gian vào/ra được ghi nhận trong cơ sở dữ liệu.
4. Quản trị viên có thể theo dõi lịch sử và quản lý toàn bộ thành viên.

## Hướng dẫn sử dụng

**Đối với người dùng:**
- Quét mặt và nhập mã để Check-in.
- Nhập lại mã để Check-out.
- Xem danh sách thành viên đang trong thư viện.

**Đối với quản trị viên:**
- Đăng nhập hệ thống.
- Thêm, sửa, xoá thành viên.
- Xem và lọc lịch sử điểm danh.
- Đăng xuất khi kết thúc phiên làm việc.
---
Chi tiết hệ thống có thể xem trong 'báo cáo hệ thống.pdf'

---
