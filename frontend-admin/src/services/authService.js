// src/services/authService.js
import axios from 'axios';

// API_BASE_URL now points to the proxy path on the frontend server
// Vite will proxy any request starting with /api to your backend
const API_BASE_URL = '/api/admin';

export const adminLogin = async (credentials) => {
    const params = new URLSearchParams();
    params.append('username', credentials.username);
    params.append('password', credentials.password);

    const loginPath = "/login"; // Path relative to API_BASE_URL
    const fullLoginUrl = `${API_BASE_URL}${loginPath}`; // Will be /api/admin/login
    console.log("[authService] Attempting login to URL:", fullLoginUrl);

    try {
        const response = await axios.post(fullLoginUrl, params, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            withCredentials: true // Important for cookie handling via proxy
        });
        console.log("[authService] Login successful, response data:", response.data);
        return response.data;
    } catch (error) {
        console.error("[authService] Full error object from login attempt:", error);
        if (error.response) { // The request was made and the server responded with a status code
            console.error("[authService] Login API Error Response Data:", error.response.data);
            console.error("[authService] Login API Error Status:", error.response.status);
            throw error.response; // Re-throw the response object so components can access status and data
        } else if (error.request) { // The request was made but no response was received
            console.error("[authService] No response from server during login (proxied). Request object:", error.request);
            throw new Error('No response from server during login. Check network or API proxy.');
        } else { // Something happened in setting up the request that triggered an Error
            console.error("[authService] Error setting up login request (proxied):", error.message);
            throw new Error('Error setting up login request (proxied): ' + error.message);
        }
    }
};

export const adminLogout = async () => {
    const logoutPath = "/logout"; // Path relative to API_BASE_URL
    const fullLogoutUrl = `${API_BASE_URL}${logoutPath}`; // Will be /api/admin/logout
    console.log("[authService] Attempting logout from URL:", fullLogoutUrl);

    try {
        // Logout needs the session cookie (sent via withCredentials) for the backend to identify the session.
        // The backend /admin/logout endpoint doesn't require a request body.
        const response = await axios.post(fullLogoutUrl, {} , { // Sending empty object as data for POST
            withCredentials: true // ESSENTIAL for sending the session cookie
        });
        console.log("[authService] Logout successful, response data:", response.data);
        return response.data; // Backend typically returns a success message
    } catch (error) {
        console.error("[authService] Full error object from logout attempt:", error);
        if (error.response) {
            console.error("[authService] Logout API Error Response Data:", error.response.data);
            console.error("[authService] Logout API Error Status:", error.response.status);
            throw error.response;
        } else if (error.request) {
            console.error("[authService] No response from server during logout (proxied). Request object:", error.request);
            throw new Error('No response from server during logout. Check network or API proxy.');
        } else {
            console.error("[authService] Error setting up logout request (proxied):", error.message);
            throw new Error('Error setting up logout request (proxied): ' + error.message);
        }
    }
};

// Optional: Function to fetch current admin's profile (e.g., for display or auth check)
export const getAdminProfile = async () => {
    const profilePath = "/me"; // Path relative to API_BASE_URL, matches backend @router.get("/me")
    const fullProfileUrl = `${API_BASE_URL}${profilePath}`; // Will be /api/admin/me
    console.log("[authService] Attempting to get admin profile from URL:", fullProfileUrl);

    try {
        // This endpoint needs the session cookie to identify the current admin.
        const response = await axios.get(fullProfileUrl, {
            withCredentials: true // ESSENTIAL for sending the session cookie
        });
        console.log("[authService] Get admin profile successful, response data:", response.data);
        return response.data;
    } catch (error) {
        console.error("[authService] Full error object from getAdminProfile attempt:", error);
        if (error.response) {
            // If 401 or 403, means not authenticated or session expired/invalid
            if (error.response.status === 401 || error.response.status === 403) {
                console.warn("[authService] Not authenticated or session expired when getting profile. Status:", error.response.status);
                return null; // Indicate not authenticated, component can handle this (e.g., redirect to login)
            }
            // For other errors, re-throw the response object
            console.error("[authService] GetAdminProfile API Error Response Data:", error.response.data);
            console.error("[authService] GetAdminProfile API Error Status:", error.response.status);
            throw error.response;
        } else if (error.request) {
            console.error("[authService] No response from server during getAdminProfile (proxied). Request object:", error.request);
            throw new Error('No response from server during getAdminProfile. Check network or API proxy.');
        } else {
            console.error("[authService] Error setting up getAdminProfile request (proxied):", error.message);
            throw new Error('Error setting up getAdminProfile request (proxied): ' + error.message);
        }
    }
};