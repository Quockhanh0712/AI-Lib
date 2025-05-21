// D:\AI-Lib\frontend-user-react\src\pages\UserProfileScreen.jsx
import React, { useState, useEffect } from 'react';

function UserProfileScreen({ onNavigate, memberCode }) {
    const [userData, setUserData] = useState(null);
    const [editMode, setEditMode] = useState(false);
    const [formData, setFormData] = useState({ full_name: '', email: '', phone_number: '' });
    const [message, setMessage] = useState({ text: '', type: '' });
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);

        // Hàm lấy thông tin hồ sơ cá nhân của người dùng từ Backend
    const fetchUserProfile = async () => {
        if (!memberCode) {
            setMessage({ text: 'Không tìm thấy mã thành viên để hiển thị hồ sơ.', type: 'error' });
            setLoading(false);
            return;
        }
        try {
            setLoading(true);
            setMessage({ text: '', type: '' }); // Xóa thông báo cũ trước khi tải
            const BACKEND_API_URL = import.meta.env.VITE_BACKEND_API_URL;
            const PROFILE_ENDPOINT = `/users/${memberCode}/profile`;

            console.log(`[UserProfileScreen] Fetching user profile for ${memberCode} from: ${BACKEND_API_URL}${PROFILE_ENDPOINT}`);
            const response = await fetch(`${BACKEND_API_URL}${PROFILE_ENDPOINT}`);
            const profile = await response.json();

            if (!response.ok) {
                console.error(`[UserProfileScreen] HTTP Error fetching profile: ${response.status}`, profile);
                // Lấy thông báo lỗi chi tiết từ backend
                const errorMessage = profile.detail || profile.message || JSON.stringify(profile);
                setMessage({ text: `Lỗi khi tải hồ sơ: ${errorMessage}`, type: 'error' });
                setUserData(null); // Đảm bảo userData là null nếu có lỗi
            } else {
                setUserData(profile);
                // Đặt dữ liệu vào form để chỉnh sửa
                setFormData({
                    full_name: profile.full_name || '',
                    email: profile.email || '',
                    phone_number: profile.phone_number || '',
                });
                setMessage({ text: 'Tải hồ sơ thành công.', type: 'success' });
            }
        } catch (error) {
            console.error("[UserProfileScreen] Error fetching user profile:", error);
            setMessage({ text: `Lỗi khi tải hồ sơ: ${error.message || 'Không xác định'}`, type: 'error' });
            setUserData(null); // Đảm bảo userData là null nếu có lỗi mạng
        } finally {
            setLoading(false);
        }
    };

    // Gọi hàm fetchUserProfile khi component được mount hoặc memberCode thay đổi
    useEffect(() => {
        fetchUserProfile();
    }, [memberCode]);

    // Xử lý thay đổi input trong form chỉnh sửa
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({ ...formData, [name]: value });
    };

        // Xử lý gửi form cập nhật thông tin
    const handleUpdateSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        setMessage({ text: 'Đang cập nhật thông tin...', type: 'info' });

        try {
            const BACKEND_API_URL = import.meta.env.VITE_BACKEND_API_URL;
            const UPDATE_ENDPOINT = `/users/${memberCode}/profile`;

            console.log(`[UserProfileScreen] Updating user profile for ${memberCode} at: ${BACKEND_API_URL}${UPDATE_ENDPOINT}`);
            console.log("[UserProfileScreen] Data to update:", formData);

            const response = await fetch(`${BACKEND_API_URL}${UPDATE_ENDPOINT}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
            });
            const responseData = await response.json(); // Lấy toàn bộ dữ liệu phản hồi

            if (!response.ok) {
                console.error(`[UserProfileScreen] HTTP Error updating profile: ${response.status}`, responseData);
                // Lấy thông báo lỗi chi tiết từ backend (detail hoặc message)
                const errorMessage = responseData.detail || responseData.message || JSON.stringify(responseData);
                setMessage({ text: `Cập nhật thất bại: ${errorMessage}`, type: 'error' });
            } else {
                setUserData(responseData); // Cập nhật dữ liệu hiển thị bằng dữ liệu mới từ backend
                setEditMode(false); // Thoát chế độ chỉnh sửa
                setMessage({ text: 'Cập nhật thông tin thành công!', type: 'success' });
            }
        } catch (error) {
            console.error("Error updating user profile:", error);
            setMessage({ text: `Cập nhật thất bại: ${error.message || 'Không xác định'}`, type: 'error' });
        } finally {
            setSubmitting(false);
        }
    };

    // Xử lý nút "Quay lại"
    const handleBackToMain = () => {
        if (onNavigate) {
            onNavigate('mainMenuScreen'); // Quay về màn hình chính
        }
    };

    // Hiển thị trạng thái tải
    if (loading) {
        return (
            <section id="userProfileScreen" className="screen">
                <div className="container">
                    <h1><i className="fas fa-user-circle"></i> Hồ sơ Thành viên</h1>
                    <p>Đang tải thông tin hồ sơ...</p>
                    {message.text && <div className={`message ${message.type}`}>{message.text}</div>}
                </div>
            </section>
        );
    }

    // Hiển thị thông báo nếu không có dữ liệu người dùng
    if (!userData) {
        return (
            <section id="userProfileScreen" className="screen">
                <div className="container">
                    <h1><i className="fas fa-user-circle"></i> Hồ sơ Thành viên</h1>
                    <p>Không thể tải thông tin hồ sơ. Vui lòng thử lại.</p>
                    {message.text && <div className={`message ${message.type}`}>{message.text}</div>}
                    <button className="secondary-button" onClick={handleBackToMain}>
                        <i className="fas fa-arrow-left"></i> Quay lại
                    </button>
                </div>
            </section>
        );
    }

    return (
        <section id="userProfileScreen" className="screen">
            <div className="container">
                <h1><i className="fas fa-user-circle"></i> Hồ sơ Thành viên</h1>
                {message.text && <div className={`message ${message.type}`}>{message.text}</div>}

                {!editMode ? ( // Chế độ xem thông tin
                    <div className="profile-display">
                        <p><strong>Mã Thành viên:</strong> {userData.member_code}</p>
                        <p><strong>Họ và Tên:</strong> {userData.full_name}</p>
                        <p><strong>Email:</strong> {userData.email || 'Chưa cung cấp'}</p>
                        <p><strong>Số điện thoại:</strong> {userData.phone_number || 'Chưa cung cấp'}</p>
                        <p><strong>Trạng thái:</strong> {userData.status}</p>
                        <p><strong>Ngày tạo:</strong> {new Date(userData.created_at).toLocaleDateString()}</p>
                        <p><strong>Cập nhật cuối:</strong> {new Date(userData.updated_at).toLocaleDateString()}</p>
                        <button className="main-button" onClick={() => setEditMode(true)}>
                            <i className="fas fa-edit"></i> Chỉnh sửa Thông tin
                        </button>
                    </div>
                ) : ( // Chế độ chỉnh sửa thông tin
                    <form onSubmit={handleUpdateSubmit} className="profile-edit-form">
                        <div className="form-group">
                            <label htmlFor="full_name">Họ và Tên:</label>
                            <input
                                type="text"
                                id="full_name"
                                name="full_name"
                                value={formData.full_name}
                                onChange={handleInputChange}
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="email">Email:</label>
                            <input
                                type="email"
                                id="email"
                                name="email"
                                value={formData.email}
                                onChange={handleInputChange}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="phone_number">Số điện thoại:</label>
                            <input
                                type="tel"
                                id="phone_number"
                                name="phone_number"
                                value={formData.phone_number}
                                onChange={handleInputChange}
                            />
                        </div>
                        <button type="submit" className="main-button" disabled={submitting}>
                            <i className="fas fa-save"></i> {submitting ? 'Đang lưu...' : 'Lưu Thay đổi'}
                        </button>
                        <button type="button" className="secondary-button" onClick={() => setEditMode(false)} disabled={submitting}>
                            <i className="fas fa-times"></i> Hủy
                        </button>
                    </form>
                )}
                <button className="secondary-button" onClick={handleBackToMain} style={{ marginTop: '20px' }}>
                    <i className="fas fa-arrow-left"></i> Quay lại
                </button>
            </div>
        </section>
    );
}

export default UserProfileScreen;
