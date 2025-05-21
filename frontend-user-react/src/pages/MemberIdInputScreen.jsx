// D:\AI-Lib\frontend-user-react\src\pages\MemberIdInputScreen.jsx

import React, { useState } from 'react';
// style.css đã được link trong index.html, không cần import ở đây

function MemberIdInputScreen({ onNavigate }) {
  const [memberId, setMemberId] = useState('');
  const [message, setMessage] = useState({ text: '', type: '' });

  // Hàm xử lý khi giá trị input thay đổi
  const handleInputChange = (event) => {
    setMemberId(event.target.value);
    setMessage({ text: '', type: '' }); // Xóa thông báo khi người dùng bắt đầu nhập
  };

  // Hàm xử lý khi nút "Tiếp tục" được nhấn
  const handleContinue = async () => {
    console.log('Continue button clicked.');
    if (!memberId.trim()) {
      setMessage({ text: 'Vui lòng nhập mã thành viên.', type: 'error' });
      return;
    }

    setMessage({ text: 'Đang kiểm tra mã thành viên...', type: 'info' });
    console.log('Checking member ID:', memberId);

    try {
      // Sử dụng biến môi trường VITE_BACKEND_API_URL
      const BACKEND_API_URL = import.meta.env.VITE_BACKEND_API_URL;
      const CHECK_MEMBER_ENDPOINT = `/check-member/${memberId.trim()}`;

      console.log(`Calling API: GET ${BACKEND_API_URL}${CHECK_MEMBER_ENDPOINT}`);
      const response = await fetch(`${BACKEND_API_URL}${CHECK_MEMBER_ENDPOINT}`);
      const result = await response.json();
      console.log('Response from Backend:', response.status, result);

      if (!response.ok) {
        console.error('HTTP Error from Backend:', response.status, result);
        // Backend có thể trả về lỗi 404 (Not Found) hoặc 403 (Forbidden)
        // Chúng ta sẽ hiển thị detail message từ backend nếu có
        setMessage({ text: `Lỗi: ${result.detail || result.message || JSON.stringify(result)}`, type: 'error' });
      } else {
        // ĐÃ SỬA LOGIC: Kiểm tra trực tiếp nếu có đối tượng user hợp lệ
        // Backend trả về trực tiếp đối tượng user nếu thành công
        if (result && result.member_code && result.status === 'Approved') { // Kiểm tra các trường cần thiết
          setMessage({ text: 'Mã thành viên hợp lệ. Đang chuyển đến xác thực khuôn mặt...', type: 'success' });
          // Chuyển sang màn hình xác thực khuôn mặt và truyền mã thành viên
          if (onNavigate) {
            onNavigate('faceRecognitionScreen', { memberId: memberId.trim() });
          }
        } else {
          // Trường hợp này có thể xảy ra nếu backend trả về 200 OK nhưng dữ liệu không như mong đợi
          // (ví dụ: user không có status 'Approved' hoặc thiếu trường)
          setMessage({ text: 'Mã thành viên không hợp lệ hoặc chưa được phê duyệt. Vui lòng kiểm tra lại.', type: 'error' });
        }
      }
    } catch (error) {
      console.error('Error checking member ID:', error);
      setMessage({ text: 'Đã xảy ra lỗi khi kiểm tra mã thành viên.', type: 'error' });
    }
  };

  // Hàm xử lý khi nút "Quay lại" được nhấn
  const handleBackToMain = () => {
    console.log('Button "Quay lại" clicked from Member ID Input');
    if (onNavigate) {
      onNavigate('mainMenuScreen'); // Quay về màn hình chính
    }
  };

  return (
    <section id="memberIdInputScreen" className="screen"> {/* Sử dụng class "screen" */}
      <div className="container"> {/* Sử dụng class "container" */}
        <h1><i className="fas fa-id-card"></i> Nhập Mã Thành viên</h1>
        <p>Vui lòng nhập mã thành viên của bạn để tiếp tục.</p>
        <div className="input-group"> {/* Sử dụng class "input-group" */}
          <input
            type="text"
            id="memberIdInput"
            placeholder="Ví dụ: SV123, GV001"
            value={memberId}
            onChange={handleInputChange}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleContinue();
              }
            }}
          />
          <button id="continueButton" className="main-button" onClick={handleContinue}> {/* Sử dụng class "main-button" */}
            <i className="fas fa-arrow-right"></i> Tiếp tục
          </button>
        </div>
        {message.text && (
          <div id="memberIdMessage" className={`message ${message.type}`}> {/* Sử dụng class "message" */}
            {message.text}
          </div>
        )}
        <button id="backToMainFromMemberId" className="secondary-button" onClick={handleBackToMain}> {/* Sử dụng class "secondary-button" */}
          <i className="fas fa-arrow-left"></i> Quay lại
        </button>
      </div>
    </section>
  );
}

export default MemberIdInputScreen;
