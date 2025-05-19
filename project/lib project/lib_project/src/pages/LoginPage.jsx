// src/pages/LoginPage.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminLogin } from '../services/authService';
import styles from './LoginPage.module.css'; // We'll create this CSS file next

// Placeholder for an AuthContext if you implement one later
// import { useAuth } from '../context/AuthContext'; // Example

function LoginPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    // const { login } = useAuth(); // Example if using AuthContext

    const handleSubmit = async (event) => {
        event.preventDefault();
        setError('');
        setLoading(true);

        if (!username || !password) {
            setError('Both username and password are required.');
            setLoading(false);
            return;
        }

        try {
            const adminData = await adminLogin({ username, password });
            // On successful login, the API should set an HttpOnly session cookie.
            // The browser will automatically send this cookie with subsequent requests to the same domain.
            // console.log('Login successful:', adminData);

            // If using an AuthContext to manage login state globally:
            // login(adminData); // Update auth state

            // For now, just navigate. The protected routes will rely on the cookie.
            navigate('/admin/members'); // Or to a default admin dashboard
        } catch (err) {
            // err might be the error.response object from axios
            if (err && err.data && err.data.detail) {
                setError(err.data.detail); // API specific error
            } else if (err && err.status === 401) {
                setError('Invalid username or password.');
            }
            else {
                setError('Login failed. Please try again or check API connection.');
            }
            console.error("Login error:", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.loginPageContainer}>
            <div className={styles.loginBox}>
                <h1 className={styles.title}>Admin Login</h1>
                {error && <p className={styles.errorMessage}>{error}</p>}
                <form onSubmit={handleSubmit}>
                    <div className={styles.inputGroup}>
                        <label htmlFor="username">Username</label>
                        <input
                            type="text"
                            id="username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                            autoComplete="username"
                        />
                    </div>
                    <div className={styles.inputGroup}>
                        <label htmlFor="password">Password</label>
                        <input
                            type="password"
                            id="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            autoComplete="current-password"
                        />
                    </div>
                    <button type="submit" className={styles.loginButton} disabled={loading}>
                        {loading ? 'Logging in...' : 'Login'}
                    </button>
                </form>
            </div>
        </div>
    );
}

export default LoginPage;