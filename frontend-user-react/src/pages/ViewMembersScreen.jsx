// D:\AI-Lib\frontend-user-react\src\pages\ViewMembersScreen.jsx

import React, { useState, useEffect } from 'react';

function ViewMembersScreen({ onNavigate }) {
  const [membersInLibrary, setMembersInLibrary] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [checkoutMessage, setCheckoutMessage] = useState({ text: '', type: '' }); // MỚI: Thông báo cho quá trình check-out
  const [showCheckoutModal, setShowCheckoutModal] = useState(false); // MỚI: Điều khiển hiển thị modal check-out
  const [selectedSession, setSelectedSession] = useState(null); // MỚI: Lưu phiên đang được chọn để check-out
  const [checkoutMemberCode, setCheckoutMemberCode] = useState(''); // MỚI: Mã thành viên nhập để xác nhận check-out
  const [isCheckingOut, setIsCheckingOut] = useState(false); // MỚI: Trạng thái đang xử lý check-out

  const fetchMembers = async () => {
    setLoading(true);
    setError(null);
    setCheckoutMessage({ text: '', type: '' }); // Xóa thông báo check-out cũ
    try {
      const BACKEND_API_URL = import.meta.env.VITE_BACKEND_API_URL;
      const CURRENT_MEMBERS_ENDPOINT = '/current-members/';

      console.log(`Calling API: GET ${BACKEND_API_URL}${CURRENT_MEMBERS_ENDPOINT}`);
      const response = await fetch(`${BACKEND_API_URL}${CURRENT_MEMBERS_ENDPOINT}`);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch members in library.');
      }

      const data = await response.json();
      setMembersInLibrary(data);
      console.log('Members in library:', data);
    } catch (err) {
      console.error('Error fetching members:', err);
      setError(err.message || 'Không thể tải danh sách người dùng đang ở thư viện.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMembers();
  }, []); // Chạy một lần khi component được render

  // MỚI: Hàm xử lý khi nhấn nút "Điểm danh Ra"
  const handleInitiateCheckout = (session) => {
    setSelectedSession(session);
    setCheckoutMemberCode(''); // Reset mã xác nhận
    setCheckoutMessage({ text: '', type: '' }); // Reset thông báo
    setShowCheckoutModal(true); // Hiển thị modal
  };

  // MỚI: Hàm xử lý khi gửi yêu cầu điểm danh ra
  const handleCheckoutSubmit = async () => {
    if (!selectedSession || !checkoutMemberCode.trim()) {
      setCheckoutMessage({ text: 'Vui lòng nhập mã thành viên xác nhận.', type: 'error' });
      return;
    }

    setIsCheckingOut(true);
    setCheckoutMessage({ text: 'Đang xử lý điểm danh ra...', type: 'info' });

    try {
      const BACKEND_API_URL = import.meta.env.VITE_BACKEND_API_URL;
      const CHECKOUT_ENDPOINT = '/attendance/check-out';

      const formData = new FormData();
      formData.append('session_id_to_checkout', selectedSession.id);
      formData.append('member_code_confirmation', checkoutMemberCode.trim());

      console.log(`[ViewMembersScreen] Calling API: POST ${BACKEND_API_URL}${CHECKOUT_ENDPOINT}`);
      const response = await fetch(`${BACKEND_API_URL}${CHECKOUT_ENDPOINT}`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();
      console.log('Response from Backend (Check-out):', response.status, result);

      if (!response.ok) {
        console.error('HTTP Error from Backend (Check-out):', response.status, result);
        setCheckoutMessage({ text: `Điểm danh ra thất bại: ${result.detail || result.message || JSON.stringify(result)}`, type: 'error' });
      } else {
        setCheckoutMessage({ text: 'Điểm danh ra thành công!', type: 'success' });
        setShowCheckoutModal(false); // Đóng modal
        setSelectedSession(null); // Xóa phiên đã chọn
        fetchMembers(); // Tải lại danh sách để cập nhật
      }
    } catch (error) {
      console.error('Lỗi khi gửi yêu cầu điểm danh ra:', error);
      setCheckoutMessage({ text: `Đã xảy ra lỗi khi điểm danh ra: ${error.message || 'Không xác định'}`, type: 'error' });
    } finally {
      setIsCheckingOut(false);
    }
  };

  const handleBackToMain = () => {
    console.log('Button "Quay lại" clicked from View Members');
    if (onNavigate) {
      onNavigate('mainMenuScreen');
    }
  };

  return (
    <section id="viewMembersScreen" className="screen">
      <div className="container">
        <h1><i className="fas fa-users"></i> Người đang ở Thư viện</h1>
        <p>Danh sách các thành viên đang có mặt trong thư viện:</p>

        <div className="member-list-placeholder">
          {loading && <p>Đang tải danh sách...</p>}
          {error && <p className="error">Lỗi: {error}</p>}
          {!loading && !error && (
            membersInLibrary.length > 0 ? (
              <ul className="member-list"> {/* THÊM CLASS CHO LIST */}
                {membersInLibrary.map((member) => (
                  <li key={member.id} className="member-item"> {/* THÊM CLASS CHO ITEM */}
                    <div className="member-info">
                      <i className="fas fa-user-circle"></i>
                      <span>
                        <strong>{member.user_session_owner?.full_name || 'Không rõ tên'}</strong> <br />
                        Vào lúc: {member.entry_time}
                      </span>
                    </div>
                    <button
                      className="secondary-button small-button" // THÊM CLASS CHO NÚT
                      onClick={() => handleInitiateCheckout(member)}
                      disabled={isCheckingOut}
                    >
                      <i className="fas fa-sign-out-alt"></i> Điểm danh Ra
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p>Không có người dùng nào đang ở trong thư viện.</p>
            )
          )}
        </div>

        {/* MỚI: Modal xác nhận điểm danh ra */}
        {showCheckoutModal && selectedSession && (
          <div className="modal-overlay">
            <div className="modal-content">
              <h2>Xác nhận Điểm danh Ra</h2>
              <p>Bạn muốn điểm danh ra cho <strong>{selectedSession.user_session_owner?.full_name}</strong> </p>
              <p>Vui lòng nhập lại Mã Thành viên để xác nhận:</p>
              <input
                type="text"
                placeholder="Nhập Mã Thành viên"
                value={checkoutMemberCode}
                onChange={(e) => setCheckoutMemberCode(e.target.value)}
                disabled={isCheckingOut}
              />
              {checkoutMessage.text && (
                <div className={`message ${checkoutMessage.type}`}>
                  {checkoutMessage.text}
                </div>
              )}
              <div className="modal-actions">
                <button className="main-button" onClick={handleCheckoutSubmit} disabled={isCheckingOut}>
                  <i className="fas fa-check-circle"></i> {isCheckingOut ? 'Đang xử lý...' : 'Xác nhận Điểm danh Ra'}
                </button>
                <button className="secondary-button" onClick={() => setShowCheckoutModal(false)} disabled={isCheckingOut}>
                  <i className="fas fa-times-circle"></i> Hủy
                </button>
              </div>
            </div>
          </div>
        )}

        <button id="backToMainFromViewMembers" className="secondary-button" onClick={handleBackToMain} style={{ marginTop: '20px' }}>
          <i className="fas fa-arrow-left"></i> Quay lại
        </button>
      </div>
    </section>
  );
}

export default ViewMembersScreen;
