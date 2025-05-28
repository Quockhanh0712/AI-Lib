import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Import các Components từ thư mục components
import HomePage from './components/HomePages.jsx'; // Đảm bảo import đúng đường dẫn
import Recognition from './components/Recognition.jsx'; // Đảm bảo import đúng đường dẫn
import StudentsInLibrary from './components/StudentsInLibrary.jsx'; // Đảm bảo import đúng đường dẫn

function App() {
    return (
        <Router>
            <Routes>
                {/* Route cho trang Home Page (đường dẫn gốc) */}
                <Route path="/" element={<HomePage />} />
                
                {/* Route cho trang Điểm danh */}
                <Route path="/recognition" element={<Recognition />} />

                {/* Route cho trang Xem sinh viên trong thư viện */}
                <Route path="/students-in-library" element={<StudentsInLibrary />} />

                {/* Các routes khác nếu có */}
            </Routes>
        </Router>
    );
}

export default App;