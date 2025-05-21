-- db/init.sql
-- File này sẽ được chạy tự động khi container database khởi động lần đầu
-- Chứa các lệnh SQL để tạo cấu trúc database (schema)
-- Đã xóa dòng: create database lib_ai; vì database đã được tạo tự động bởi Docker Compose
-- Đã giữ nguyên tên cột 'password_hash' theo yêu cầu

-- Bảng admin_users
CREATE TABLE admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- Đã khôi phục lại tên cột là password_hash
    full_name VARCHAR(255) NULL,
    contact_info VARCHAR(255) NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng users
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_code VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NULL,
    phone_number VARCHAR(20) NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Approved', -- ('Approved', 'Inactive')
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX idx_users_member_code ON users(member_code);

CREATE TABLE face_embeddings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    embedding1 TEXT,
    embedding2 TEXT,
    embedding3 TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


-- Bảng attendance_sessions
CREATE TABLE attendance_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    entry_time TIMESTAMP NOT NULL,
    exit_time TIMESTAMP NULL,
    duration_minutes INT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX idx_attendance_user_id ON attendance_sessions(user_id);
CREATE INDEX idx_attendance_exit_time ON attendance_sessions(exit_time);

-- Bảng registration_requests
CREATE TABLE registration_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    requested_member_code VARCHAR(50) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NULL,
    phone_number VARCHAR(20) NULL,
    photo_path VARCHAR(255) NOT NULL, -- Đường dẫn tới ảnh tạm
    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending', -- ('Pending', 'Approved', 'Rejected')
    processed_by_admin_id INT NULL,
    processing_time TIMESTAMP NULL,
    FOREIGN KEY (processed_by_admin_id) REFERENCES admin_users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX idx_registration_requests_status ON registration_requests(status);

-- Chèn dữ liệu ban đầu
INSERT INTO admin_users (username, password_hash, full_name, contact_info) VALUES
('admin', '$2b$12$.MeOZqkLA2QMQYZsIaRpzOwuc5kMtdGXQj6samvdcOAWjyqoc84gq', 'Quan Tri Vien He Thong', 'admin@example.com');
-- Lưu ý: password_hash là ví dụ, bạn cần dùng thư viện băm mật khẩu (bcrypt, argon2)
-- để tạo hash thực tế khi tạo tài khoản admin.

-- Giả sử admin_users.id của 'admin' là 1
INSERT INTO registration_requests (requested_member_code, full_name, email, phone_number, photo_path, status, processed_by_admin_id, processing_time) VALUES
('SV001', 'Nguyen Van An', 'an.nv@example.com', '0901234567', '/path/to/temp/an_nv.jpg', 'Pending', NULL, NULL),
('SV002', 'Tran Thi Binh', 'binh.tt@example.com', '0907654321', '/path/to/temp/binh_tt.jpg', 'Pending', NULL, NULL),
('GV001', 'Le Van Cuong', 'cuong.lv@example.com', '0912345678', 'https://placehold.co/150x150/FF0000/FFFFFF?text=GV001', 'Approved', 1, NOW() - INTERVAL 1 DAY), -- Đã được admin xử lý
('SV003', 'Pham Thi Dung', 'dung.pt@example.com', '0987654321', 'https://placehold.co/150x150/00FF00/000000?text=SV003', 'Rejected', 1, NOW() - INTERVAL 2 DAY); -- Đã bị từ chối

-- Giả sử GV001 (Lê Văn Cường) từ registration_requests đã được phê duyệt và tạo user.id = 1
INSERT INTO users (member_code, full_name, email, phone_number, status) VALUES
('GV001', 'Le Van Cuong', 'cuong.lv@example.com', '0912345678', 'Approved');

-- Thêm một vài user khác đã được phê duyệt (giả sử Admin thêm trực tiếp)
INSERT INTO users (member_code, full_name, email, phone_number, status) VALUES
('SV100', 'Tran Quoc Khanh', 'nam.hv@example.com', '0911111111', 'Approved'),
('SV101', 'Do Thi Lan', 'lan.dt@example.com', '0922222222', 'Approved'),
('SV102', 'Vu Minh Hai', 'hai.vm@example.com', '0933333333', 'Inactive'),
('SV103', 'Nguyen Van Huy', 'huy.vm@example.com', '0832232323', 'Approved')
; -- User bị vô hiệu hóa

-- GV001 đã vào và ra
INSERT INTO attendance_sessions (user_id, entry_time, exit_time, duration_minutes) VALUES
(1, NOW() - INTERVAL '3' HOUR, NOW() - INTERVAL '1' HOUR, 120); -- Vào 3 tiếng trước, ra 1 tiếng trước

-- SV100 đang ở trong thư viện
INSERT INTO attendance_sessions (user_id, entry_time, exit_time, duration_minutes) VALUES
(2, NOW() - INTERVAL '30' MINUTE, NULL, NULL); -- Vào 30 phút trước, chưa ra

-- SV101 đã vào và ra nhiều lần
INSERT INTO attendance_sessions (user_id, entry_time, exit_time, duration_minutes) VALUES
(3, NOW() - INTERVAL '5' DAY - INTERVAL '2' HOUR, NOW() - INTERVAL '5' DAY, 120), -- 5 ngày trước
(3, NOW() - INTERVAL '1' DAY - INTERVAL '1' HOUR, NOW() - INTERVAL '1' DAY - INTERVAL '30' MINUTE, 30); -- Hôm qua

-- SV100 có một phiên khác đã hoàn thành
INSERT INTO attendance_sessions (user_id, entry_time, exit_time, duration_minutes) VALUES
(2, NOW() - INTERVAL '2' DAY - INTERVAL '4' HOUR, NOW() - INTERVAL '2' DAY - INTERVAL '1' HOUR, 180);
