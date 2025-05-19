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
    useNavigate // <<< IMPORT useNavigate
} from 'react-router-dom';
import styles from './App.module.css'; // Your App specific styles
import { adminLogout } from './services/authService'; // <<< IMPORT adminLogout service

// Page Imports
import LoginPage from './pages/LoginPage';
import MemberListPage from './pages/MemberListPage';
import AddMemberPage from './pages/AddMemberPage';
import EditMemberPage from './pages/EditMemberPage';
// import RegistrationRequestPage from './pages/RegistrationRequestPage'; // Example for future
// import AttendanceHistoryPage from './pages/AttendanceHistoryPage';   // Example for future

// Placeholder for ProtectedRoute component if you add one
// import ProtectedRoute from './components/ProtectedRoute';

function App() {
    // For now, we don't have global auth state management here.
    // We'll assume routes under /admin should ideally be protected.
    // A proper ProtectedRoute component would handle checking auth status.

    return (
        <Router>
            <Routes>
                <Route path="/login" element={<LoginPage />} />

                {/* Admin Routes - these will use the AdminLayout */}
                {/* Consider wrapping this Route with a ProtectedRoute component later */}
                <Route path="/admin" element={<AdminLayout />}>
                    <Route index element={<Navigate replace to="members" />} />
                    <Route path="members" element={<MemberListPage />} />
                    <Route path="members/add" element={<AddMemberPage />} />
                    <Route path="members/edit/:memberId" element={<EditMemberPage />} />
                    {/* Example for future routes:
                    <Route path="requests" element={<RegistrationRequestPage />} />
                    <Route path="history" element={<AttendanceHistoryPage />} />
                    */}
                </Route>

                {/* Default route if no other route matches, redirect to login */}
                <Route path="/" element={<Navigate replace to="/login" />} />
                {/* <Route path="*" element={<NotFoundPage />} /> // Optional 404 page */}
            </Routes>
        </Router>
    );
}

// AdminLayout component to provide a consistent structure for admin pages
function AdminLayout() {
    const navigate = useNavigate(); // Hook for programmatic navigation

    const handleLogout = async () => {
        console.log("[AdminLayout] Attempting logout...");
        try {
            await adminLogout(); // Call the service function from authService.js
            console.log("[AdminLayout] Logout service call successful.");

            // Optional: Clear any client-side authentication state if you have one
            // (e.g., if using React Context for auth status)
            // authContext.dispatch({ type: 'LOGOUT' });

            alert("You have been successfully logged out."); // Provide user feedback
            navigate('/login'); // Redirect to the login page
        } catch (error) {
            console.error("[AdminLayout] Logout failed:", error);
            // Display a more user-friendly error if possible
            const errorMessage = (error.response && error.response.data && error.response.data.detail)
                               ? error.response.data.detail
                               : error.message || "An unknown error occurred during logout.";
            alert(`Logout failed: ${errorMessage}. Please try again.`);
            // Depending on the error, you might still want to redirect to login,
            // or allow the user to stay on the page if the server couldn't process logout.
            // For simplicity now, we don't redirect on error here, but you could.
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
                {/* Add other admin navigation links here as needed
                <NavLink
                    to="/admin/requests" // Example
                    className={({ isActive }) => `${styles.navLink || ''} ${isActive ? styles.active : ''}`}
                >
                    Registration Requests
                </NavLink>
                */}

                {/* Logout Button - pushed to the right using inline style for simplicity */}
                <button
                    onClick={handleLogout}
                    className={styles.logoutButton || ''} // Apply styling from App.module.css
                    style={{ marginLeft: 'auto' }} // Pushes button to the right if nav is display:flex
                >
                    Logout
                </button>
            </nav>
            <main className={styles.pageContent}>
                <Outlet /> {/* Child route components will render here */}
            </main>
        </div>
    );
}

export default App;