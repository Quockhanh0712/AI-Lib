// src/App.jsx
import React from 'react';
// Ensure Outlet and useNavigate are imported from react-router-dom
import {
    BrowserRouter as Router,
    Routes,
    Route,
    NavLink,
    Navigate,
    Outlet,
    useNavigate // Ensure useNavigate is imported
} from 'react-router-dom';
import styles from './App.module.css'; // Your App specific styles
import { adminLogout } from './services/authService'; // Ensure this path is correct

// Page Imports
import LoginPage from './pages/LoginPage';
import MemberListPage from './pages/MemberListPage';
import AddMemberPage from './pages/AddMemberPage';
import EditMemberPage from './pages/EditMemberPage';
import AttendanceHistoryPage from './pages/AttendanceHistoryPage'; // <<< IMPORTED
// import RegistrationRequestPage from './pages/RegistrationRequestPage'; // Example for future

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/login" element={<LoginPage />} />

                <Route path="/admin" element={<AdminLayout />}>
                    <Route index element={<Navigate replace to="members" />} />
                    <Route path="members" element={<MemberListPage />} />
                    <Route path="members/add" element={<AddMemberPage />} />
                    <Route path="members/edit/:memberId" element={<EditMemberPage />} />
                    <Route path="attendance-history" element={<AttendanceHistoryPage />} /> {/* <<< ADDED ROUTE */}
                    {/* Example for future routes:
                    <Route path="requests" element={<RegistrationRequestPage />} />
                    */}
                </Route>

                <Route path="/" element={<Navigate replace to="/login" />} />
                {/* <Route path="*" element={<NotFoundPage />} /> // Optional 404 page */}
            </Routes>
        </Router>
    );
}

function AdminLayout() {
    const navigate = useNavigate();

    const handleLogout = async () => {
        console.log("[AdminLayout] Attempting logout...");
        try {
            await adminLogout();
            console.log("[AdminLayout] Logout service call successful.");
            alert("You have been successfully logged out.");
            navigate('/login');
        } catch (error) {
            console.error("[AdminLayout] Logout failed:", error);
            const errorMessage = (error.response && error.response.data && error.response.data.detail)
                               ? error.response.data.detail
                               : error.message || "An unknown error occurred during logout.";
            alert(`Logout failed: ${errorMessage}. Please try again.`);
        }
    };

    return (
        <div>
            <nav className={styles.mainNav}>
                <NavLink
                    to="/admin/members"
                    className={({ isActive }) => `${styles.navLink || ''} ${isActive ? styles.active : ''}`}
                >
                    Manage Members
                </NavLink>
                <NavLink // <<< ADDED NAVLINK FOR ATTENDANCE HISTORY
                    to="/admin/attendance-history"
                    className={({ isActive }) => `${styles.navLink || ''} ${isActive ? styles.active : ''}`}
                >
                    Attendance History
                </NavLink>
                {/* 
                <NavLink
                    to="/admin/requests" // Example
                    className={({ isActive }) => `${styles.navLink || ''} ${isActive ? styles.active : ''}`}
                >
                    Registration Requests
                </NavLink>
                */}
                <button
                    onClick={handleLogout}
                    className={styles.logoutButton || ''}
                    style={{ marginLeft: 'auto' }}
                >
                    Logout
                </button>
            </nav>
            <main className={styles.pageContent}>
                <Outlet />
            </main>
        </div>
    );
}

export default App;