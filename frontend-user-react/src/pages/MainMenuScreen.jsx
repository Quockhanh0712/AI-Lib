// D:\AI-Lib\frontend-user-react\src\pages\MainMenuScreen.jsx

import React from 'react';

function MainMenuScreen({ onNavigate, user, entryTime }) {
  const handleAttendance = () => {
    console.log('Button "Điểm danh Khuôn mặt" clicked from Main Menu');
    onNavigate('memberIdInputScreen');
  };

  const handleViewMembers = () => {
    console.log('Button "Xem Người đang ở Thư viện" clicked from Main Menu');
    onNavigate('viewMembersScreen');
  };

  const handleUserProfile = () => {
    console.log('Button "Hồ sơ cá nhân" clicked from Main Menu');
    if (user && user.member_code) {
      onNavigate('userProfileScreen', { memberCode: user.member_code });
    } else {
      alert("Bạn cần điểm danh thành công để xem hồ sơ cá nhân!");
    }
  };

  // ĐÃ SỬA: Hàm này giờ là "Quay lại Màn hình Chính" và reset trạng thái
  const handleBackToMainMenuAndReset = () => {
    console.log('Button "Quay lại Màn hình Chính" clicked from Main Menu (after recognition)');
    // Điều hướng về mainMenuScreen và truyền user: null, entryTime: '' để reset trạng thái
    onNavigate('mainMenuScreen', { user: null, entryTime: '' });
  };

  return (
    <section id="mainMenuScreen" className="screen">
      <div className="container">
                {user && entryTime ? ( // Nếu có thông tin người dùng đã điểm danh
          <>
            <h1>Chào mừng, {user.full_name}!</h1>
            <p className="message success">Bạn đã điểm danh vào lúc: {entryTime}</p>
            <div className="button-group">
              <button className="main-button" onClick={handleUserProfile}>
                <i className="fas fa-user-circle"></i> Xem/Chỉnh sửa Hồ sơ
              </button>
              {/* ĐÃ SỬA: Chỉ giữ lại nút "Quay lại Màn hình Chính" */}
              <button className="secondary-button" onClick={handleBackToMainMenuAndReset} style={{ marginTop: '10px' }}>
                <i className="fas fa-arrow-left"></i> Quay lại Màn hình Chính
              </button>
            </div>
          </>
        ) : ( // Nếu chưa có thông tin người dùng điểm danh
          <>
            <h1><i className="fas fa-home"></i> Màn hình Chính</h1>
            <p>Chào mừng bạn đến với hệ thống điểm danh!</p>
            <div className="button-group">
              <button id="attendanceButton" className="main-button" onClick={handleAttendance}>
                <i className="fas fa-user-check"></i> Điểm danh Khuôn mặt
              </button>
              <button id="viewMembersButton" className="main-button" onClick={handleViewMembers}>
                <i className="fas fa-users"></i> Xem Danh sách Người đang ở TT
              </button>
            </div>
          </>
        )}
      </div>
    </section>
  );
}

export default MainMenuScreen;
