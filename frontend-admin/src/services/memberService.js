// src/services/memberService.js
import axios from 'axios';

const API_BASE_URL = '/api/admin'; // Using the proxied path

// ... (getAllMembers, getMemberById are likely fine if they are GET requests) ...

export const createMember = async (memberData) => { // memberData is a plain object from AddMemberPage.jsx
    const params = new URLSearchParams();

    // Append fields that have values. Backend expects these specific names.
    if (memberData.member_code) {
        params.append('member_code', memberData.member_code);
    }
    if (memberData.full_name) {
        params.append('full_name', memberData.full_name);
    }
    if (memberData.email) { // Optional
        params.append('email', memberData.email);
    }
    if (memberData.phone_number) { // Optional
        params.append('phone_number', memberData.phone_number);
    }

    const path = '/users/';
    const fullUrl = `${API_BASE_URL}${path}`;
    console.log("[memberService] POSTing to createMember URL:", fullUrl);
    console.log("[memberService] Data being sent (x-www-form-urlencoded):", params.toString());

    try {
        const response = await axios.post(fullUrl, params, { // Send 'params' (URLSearchParams object)
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded' // Explicitly set Content-Type
            },
            withCredentials: true
        });
        return response.data;
    } catch (error) {
        console.error("[memberService] Axios error in createMember:", error.response || error.message);
        throw error; // Re-throw so AddMemberPage can catch it
    }
};

// ... (updateMember and deleteMember will also need review based on what backend expects for PUT/DELETE bodies)
// For PUT, if backend uses Form() for updates, you'd use URLSearchParams too.
// If it expects JSON for PUT, then what you had before for updateMember (sending memberData directly) would be correct.
// Delete usually doesn't have a body.

export const updateMember = async (userId, memberDataToUpdate) => {
    const params = new URLSearchParams();
    // Only append fields that are provided for update
    if (memberDataToUpdate.full_name !== undefined) params.append('full_name', memberDataToUpdate.full_name);
    if (memberDataToUpdate.email !== undefined) params.append('email', memberDataToUpdate.email);
    if (memberDataToUpdate.phone_number !== undefined) params.append('phone_number', memberDataToUpdate.phone_number);
    if (memberDataToUpdate.status_update !== undefined) params.append('status_update', memberDataToUpdate.status_update);


    const path = `/users/${userId}`;
    const fullUrl = `${API_BASE_URL}${path}`;
    console.log("[memberService] PUTing to updateMember URL:", fullUrl);
    console.log("[memberService] Data being sent (x-www-form-urlencoded):", params.toString());
    try {
        const response = await axios.put(fullUrl, params, { // Send 'params'
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, // If backend expects form data for PUT
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

// Keep getAllMembers and getMemberById as they were (they are GET requests and don't send a body like this)
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