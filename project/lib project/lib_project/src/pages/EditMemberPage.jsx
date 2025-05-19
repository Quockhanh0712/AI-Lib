// src/pages/EditMemberPage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getMemberById, updateMember } from '../services/memberService'; // Ensure paths are correct
import formStyles from '../components/forms/Form.module.css';

function EditMemberPage() {
    const [initialDataLoading, setInitialDataLoading] = useState(true); // For fetching existing data
    const [memberData, setMemberData] = useState({ // State to hold form fields
        fullName: '',
        email: '',
        phoneNumber: '',
        status: 'Approved' // Default status for the select dropdown
    });
    // Separate state for the original member code if it's not editable or needed for display
    const [originalMemberCode, setOriginalMemberCode] = useState('');


    const [error, setError] = useState(null);
    const [submitting, setSubmitting] = useState(false); // For update submission

    const { memberId } = useParams(); // Get memberId from URL (e.g., /admin/members/edit/123)
    const navigate = useNavigate();

    useEffect(() => {
        const fetchMemberData = async () => {
            console.log("[EditMemberPage] useEffect triggered. Fetching member with ID:", memberId);
            if (!memberId) {
                console.error("[EditMemberPage] No memberId found in URL params.");
                setError("No member ID specified.");
                setInitialDataLoading(false);
                return;
            }
            setInitialDataLoading(true);
            setError(null);
            try {
                console.log("[EditMemberPage] Calling getMemberById service for ID:", memberId);
                const response = await getMemberById(memberId); // This is from memberService.js
                console.log("[EditMemberPage] Data received from getMemberById:", response); // Log the whole response

                if (response && response.data) {
                    const fetchedUser = response.data;
                    console.log("[EditMemberPage] Fetched user data:", fetchedUser);
                    setMemberData({
                        fullName: fetchedUser.full_name || '',
                        email: fetchedUser.email || '',
                        phoneNumber: fetchedUser.phone_number || '',
                        status: fetchedUser.status || 'Approved'
                    });
                    setOriginalMemberCode(fetchedUser.member_code || ''); // Store original member code
                } else {
                    console.error("[EditMemberPage] getMemberById response or response.data is undefined.");
                    setError("Could not retrieve member details.");
                }
            } catch (err) {
                console.error("[EditMemberPage] Error fetching member data:", err);
                if (err.response) {
                    setError(`API Error: ${err.response.status} - ${err.response.data.detail || err.response.statusText}`);
                } else {
                    setError(err.message || "Failed to fetch member data.");
                }
            } finally {
                setInitialDataLoading(false);
                console.log("[EditMemberPage] Finished fetching member data. InitialDataLoading:", false);
            }
        };

        fetchMemberData();
    }, [memberId]); // Re-run if memberId changes

    const handleInputChange = (event) => {
        const { name, value } = event.target;
        setMemberData(prevData => ({
            ...prevData,
            [name]: value
        }));
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        console.log("[EditMemberPage] handleSubmit called. Data to update:", memberData);
        setError(null);
        setSubmitting(true);

        // Prepare data for update (only send changed fields if backend supports partial updates,
        // or send all fields if backend expects all editable fields)
        // The backend update endpoint takes individual Form fields.
        const updatePayload = {
            full_name: memberData.fullName.trim(),
            email: memberData.email.trim() || null,
            phone_number: memberData.phoneNumber.trim() || null,
            status_update: memberData.status
        };
         console.log("[EditMemberPage] Payload for updateMember service:", updatePayload);


        try {
            await updateMember(memberId, updatePayload); // updateMember from memberService.js
            alert('Member updated successfully!');
            navigate('/admin/members');
        } catch (err) {
            console.error("[EditMemberPage] Error updating member:", err);
             if (err.response && err.response.data && err.response.data.detail) {
                if (Array.isArray(err.response.data.detail)) {
                    const errorMessages = err.response.data.detail.map(d => `${d.loc.join(' -> ')}: ${d.msg}`).join('; ');
                    setError(`Validation Error(s): ${errorMessages}`);
                } else {
                    setError(`API Error: ${err.response.data.detail}`);
                }
            } else if (err.response && err.response.status) {
                setError(`API Error: ${err.response.status} - ${err.response.statusText || 'Failed to update member'}`);
            } else {
                setError(err.message || 'Failed to update member. Please try again.');
            }
        } finally {
            setSubmitting(false);
        }
    };

    if (initialDataLoading) {
        return <p className={formStyles.loadingText || ''}>Loading member data...</p>;
    }

    if (error && !memberData.fullName) { // Show error prominently if initial load failed
        return (
            <div className={formStyles.formContainer}>
                <p className={formStyles.errorText}>Error: {error}</p>
                <Link to="/admin/members">Back to Members List</Link>
            </div>
        );
    }

    return (
        <div className={formStyles.formContainer}>
            <h2 className={formStyles.formTitle}>Edit Member (ID: {memberId}, Code: {originalMemberCode})</h2>
            {/* Display submission error, not initial load error if form is visible */}
            {error && submitting && <p className={formStyles.errorText}>{error}</p>}
            <form onSubmit={handleSubmit}>
                <div className={formStyles.formGroup}>
                    <label htmlFor="fullName">Full Name: *</label>
                    <input
                        type="text"
                        id="fullName"
                        name="fullName" // Important for handleInputChange
                        value={memberData.fullName}
                        onChange={handleInputChange}
                        required
                    />
                </div>
                <div className={formStyles.formGroup}>
                    <label htmlFor="email">Email:</label>
                    <input
                        type="email"
                        id="email"
                        name="email" // Important for handleInputChange
                        value={memberData.email}
                        onChange={handleInputChange}
                    />
                </div>
                <div className={formStyles.formGroup}>
                    <label htmlFor="phoneNumber">Phone Number:</label>
                    <input
                        type="text"
                        id="phoneNumber"
                        name="phoneNumber" // Important for handleInputChange
                        value={memberData.phoneNumber}
                        onChange={handleInputChange}
                    />
                </div>
                <div className={formStyles.formGroup}>
                    <label htmlFor="status">Status:</label>
                    <select 
                        id="status" 
                        name="status" // Important for handleInputChange
                        value={memberData.status} 
                        onChange={handleInputChange}
                    >
                        <option value="Approved">Approved</option>
                        <option value="Inactive">Inactive</option>
                    </select>
                </div>
                <button type="submit" className={formStyles.submitButton} disabled={submitting}>
                    {submitting ? 'Updating...' : 'Update Member'}
                </button>
            </form>
        </div>
    );
}

export default EditMemberPage;