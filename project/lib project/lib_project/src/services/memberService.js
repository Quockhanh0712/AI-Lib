// src/services/memberService.js
import axios from 'axios';

const API_BASE_URL = '/api/admin'; // Using the proxied path

// ... (getAllMembers, getMemberById as they were) ...
export const getAllMembers = (params) => {
    const path = '/users/';
    const fullUrl = `${API_BASE_URL}${path}`;
    console.log("[memberService] Requesting URL for getAllMembers:", fullUrl, "with params:", params);
    return axios.get(fullUrl, {
        params,
        withCredentials: true
    });
};

export const getMemberById = (userId) => {
    const path = `/users/${userId}`;
    const fullUrl = `${API_BASE_URL}${path}`;
    console.log("[memberService] Requesting URL for getMemberById:", fullUrl);
    return axios.get(fullUrl, {
        withCredentials: true
    });
};


export const createMember = async (formData) => { // formData is now a FormData object
    const path = '/users/';
    const fullUrl = `${API_BASE_URL}${path}`;
    console.log("[memberService] POSTing FormData to createMember URL:", fullUrl);
    
    // Log FormData content for debugging
    for (let pair of formData.entries()) {
        console.log(`[memberService] FormData Field: ${pair[0]}, Value: ${pair[1] instanceof File ? pair[1].name : pair[1]}`);
    }

    try {
        const response = await axios.post(fullUrl, formData, {
            // When sending FormData, Axios automatically sets the
            // 'Content-Type' header to 'multipart/form-data' with the correct boundary.
            // So, you typically don't need to set it manually here.
            // headers: { 'Content-Type': 'multipart/form-data' }, // Usually NOT needed
            withCredentials: true
        });
        return response.data;
    } catch (error) {
        console.error("[memberService] Axios error in createMember:", error.response || error.message);
        throw error; // Re-throw so AddMemberPage can catch it
    }
};

// updateMember would also need to handle FormData if admins can update photos.
// For now, keeping it as x-www-form-urlencoded as per previous setup.
// If you need to update photos, this needs to change to FormData too.
export const updateMember = async (userId, formData, memberCodeForAI) => { // formData is now a FormData object
    // The backend /admin/users/{user_id} PUT endpoint will receive these form fields.
    // It needs to know the member_code to pass to the AI service if new photos are included.
    // We can add member_code to FormData if not already there and photos are present.
    
    const hasPhotos = formData.has('photos'); // Check if 'photos' field exists in FormData

    if (hasPhotos && memberCodeForAI && !formData.has('member_code')) {
        formData.append('member_code', memberCodeForAI); // Add member_code for AI service call if photos are present
    }

    const path = `/users/${userId}`; // PUT request to update user by DB ID
    const fullUrl = `${API_BASE_URL}${path}`;
    console.log("[memberService] PUTing FormData to updateMember URL:", fullUrl);
    for (let pair of formData.entries()) {
        console.log(`[memberService] Update FormData Field: ${pair[0]}, Value: ${pair[1] instanceof File ? pair[1].name : pair[1]}`);
    }

    try {
        const response = await axios.put(fullUrl, formData, {
            // Axios will set 'Content-Type': 'multipart/form-data' automatically for FormData
            withCredentials: true
        });
        return response.data;
    } catch (error) {
        console.error("[memberService] Axios error in updateMember:", error.response || error.message);
        throw error;
    }
};

export const deleteMember = async (userId) => {
    const path = `/users/${userId}`;
    const fullUrl = `${API_BASE_URL}${path}`;
    console.log("[memberService] DELETing from deleteMember URL:", fullUrl);
    try {
        const response = await axios.delete(fullUrl, {
            withCredentials: true
        });
        return response.data;
    } catch (error) {
        console.error("[memberService] Axios error in deleteMember:", error.response || error.message);
        throw error;
    }
};