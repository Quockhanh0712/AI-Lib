// D:\AI-Lib\frontend-user-react\src\App.jsx
import React, { useState } from 'react';
import MainMenuScreen from './pages/MainMenuScreen';
import MemberIdInputScreen from './pages/MemberIdInputScreen';
import FaceRecognitionScreen from './pages/FaceRecognitionScreen';
import ViewMembersScreen from './pages/ViewMembersScreen';
import UserProfileScreen from './pages/UserProfileScreen'; // Đảm bảo đã import

function App() {
  const [currentScreen, setCurrentScreen] = useState('mainMenuScreen');
  const [currentMemberId, setCurrentMemberId] = useState('');
  const [recognizedUser, setRecognizedUser] = useState(null);
  const [entryTime, setEntryTime] = useState('');

  const handleNavigate = (screenName, data = {}) => {
    console.log('Navigating to screen:', screenName, 'with data:', data);
    setCurrentScreen(screenName);

    // Cập nhật currentMemberId
    // Ưu tiên data.memberId nếu có (từ FaceRecognitionScreen)
    // Nếu không có data.memberId, và đang chuyển đến màn hình profile hoặc face recognition,
    // thì giữ nguyên currentMemberId hiện tại.
    // Nếu chuyển đến màn hình khác, reset currentMemberId.
    if (data.memberId) {
      setCurrentMemberId(data.memberId);
    } else if (screenName !== 'userProfileScreen' && screenName !== 'faceRecognitionScreen') {
      setCurrentMemberId(''); // Reset chỉ khi chuyển đến màn hình không liên quan đến memberId
    }

    // Cập nhật recognizedUser và entryTime
    if (data.user && data.entryTime) {
      setRecognizedUser(data.user);
      setEntryTime(data.entryTime);
    } else if (screenName === 'mainMenuScreen' && !data.user) {
      // Nếu quay về mainMenuScreen mà không có user mới, reset recognizedUser và entryTime
      setRecognizedUser(null);
      setEntryTime('');
    }
    // Giữ nguyên recognizedUser và entryTime khi chuyển đến các màn hình khác
    // như userProfileScreen hoặc viewMembersScreen, vì chúng vẫn cần thông tin này
    // hoặc không ảnh hưởng đến trạng thái chào mừng trên MainMenuScreen.
  };

  const renderScreen = () => {
    switch (currentScreen) {
      case 'mainMenuScreen':
        return <MainMenuScreen onNavigate={handleNavigate} user={recognizedUser} entryTime={entryTime} />;
      case 'memberIdInputScreen':
        return <MemberIdInputScreen onNavigate={handleNavigate} />;
      case 'userProfileScreen':
        // Truyền currentMemberId vào UserProfileScreen
        return <UserProfileScreen onNavigate={handleNavigate} memberCode={currentMemberId} />;
      case 'faceRecognitionScreen':
        return <FaceRecognitionScreen onNavigate={handleNavigate} memberIdToRecognize={currentMemberId} />;
      case 'viewMembersScreen':
        return <ViewMembersScreen onNavigate={handleNavigate} />;
      default:
        return <MainMenuScreen onNavigate={handleNavigate} />;
    }
  };

  return (
    <div className="App">
      {renderScreen()}
    </div>
  );
}

export default App;
