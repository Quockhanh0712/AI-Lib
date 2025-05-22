// src/pages/EditMemberPage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { getMemberById, updateMember } from '../services/memberService';
import formStyles from '../components/forms/Form.module.css';

function EditMemberPage() {
    const [initialDataLoading, setInitialDataLoading] = useState(true);
    const [memberData, setMemberData] = useState({
        fullName: '',
        email: '',
        phoneNumber: '',
        status: 'Approved'
    });
    const [originalMemberCode, setOriginalMemberCode] = useState('');
    const [newPhoto, setNewPhoto] = useState(null); // State for a single NEW photo
    const [newPhotoPreview, setNewPhotoPreview] = useState(null); // Preview for the NEW photo

    const [error, setError] = useState(null);
    const [submitting, setSubmitting] = useState(false);

    const { memberId } = useParams();
    const navigate = useNavigate();

    useEffect(() => {
        // ... (fetchMemberData useEffect remains the same as your provided version) ...
        const fetchMemberData = async () => {
            console.log("[EditMemberPage] useEffect: Fetching member with DB ID:", memberId);
            if (!memberId) {
                setError("No member ID specified.");
                setInitialDataLoading(false);
                return;
            }
            setInitialDataLoading(true);
            setError(null);
            try {
                const response = await getMemberById(memberId);
                if (response && response.data) {
                    const fetchedUser = response.data;
                    setMemberData({
                        fullName: fetchedUser.full_name || '',
                        email: fetchedUser.email || '',
                        phoneNumber: fetchedUser.phone_number || '',
                        status: fetchedUser.status || 'Approved'
                    });
                    setOriginalMemberCode(fetchedUser.member_code || '');
                } else {
                    setError("Could not retrieve member details.");
                }
            } catch (err) {
                handleApiError(err, "fetching member data");
            } finally {
                setInitialDataLoading(false);
            }
        };
        fetchMemberData();
    }, [memberId]);


    const handleInputChange = (event) => {
        const { name, value } = event.target;
        setMemberData(prevData => ({ ...prevData, [name]: value }));
    };

    const handleNewPhotoChange = (event) => {
        if (newPhotoPreview) {
            URL.revokeObjectURL(newPhotoPreview);
        }
        const file = event.target.files[0];
        if (file) {
            setNewPhoto(file);
            setNewPhotoPreview(URL.createObjectURL(file));
        } else {
            setNewPhoto(null);
            setNewPhotoPreview(null);
        }
    };

    useEffect(() => { // Cleanup for newPhotoPreview
        return () => {
            if (newPhotoPreview) {
                URL.revokeObjectURL(newPhotoPreview);
            }
        };
    }, [newPhotoPreview]);

    const handleApiError = (err, action = "performing action") => {
        // ... (handleApiError function remains the same as your provided version) ...
        console.error(`[EditMemberPage] Error ${action}:`, err);
        if (err.response && err.response.data && err.response.data.detail) {
            const detail = err.response.data.detail;
            if (Array.isArray(detail)) {
                const errorMessages = detail.map(d => `${d.loc.join(' -> ')}: ${d.msg}`).join('; ');
                setError(`Validation Error(s): ${errorMessages}`);
            } else {
                setError(`API Error: ${detail}`);
            }
        } else if (err.response && err.response.status) {
            setError(`API Error: ${err.response.status} - ${err.response.statusText || `Failed ${action}`}`);
        } else {
            setError(err.message || `Failed ${action}. An unexpected error occurred.`);
        }
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        setError(null);
        setSubmitting(true);

        const formData = new FormData();
        formData.append('full_name', memberData.fullName.trim());
        if (memberData.email.trim()) formData.append('email', memberData.email.trim());
        if (memberData.phoneNumber.trim()) formData.append('phone_number', memberData.phoneNumber.trim());
        formData.append('status_update', memberData.status);

        // Append the new photo if one was selected
        // Backend will expect a single 'photo' (not 'photos') if a new one is sent
        if (newPhoto) {
            formData.append('photo', newPhoto, newPhoto.name);
        }
        
        console.log("[EditMemberPage] FormData being sent to updateMember service:");
        for (let pair of formData.entries()) {
            console.log(pair[0]+ ': ' + (pair[1] instanceof File ? pair[1].name : pair[1]));
        }

        try {
            // Pass originalMemberCode if your updateMember service needs it to inform the AI service
            await updateMember(memberId, formData, originalMemberCode);
            alert('Member updated successfully!');
            navigate('/admin/members');
        } catch (err) {
            handleApiError(err, "updating member");
        } finally {
            setSubmitting(false);
        }
    };

    // ... (loading and error return JSX as before) ...
    if (initialDataLoading) {
        return <p className={formStyles.loadingText || ''}>Loading member data...</p>;
    }
    if (error && !submitting) { 
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
            {error && submitting && <p className={formStyles.errorText}>{error}</p>}
            <form onSubmit={handleSubmit}>
                {/* ... (fullName, email, phoneNumber, status inputs as before, using handleInputChange) ... */}
                <div className={formStyles.formGroup}>
                    <label htmlFor="fullName">Full Name: *</label>
                    <input type="text" id="fullName" name="fullName" value={memberData.fullName} onChange={handleInputChange} required />
                </div>
                <div className={formStyles.formGroup}>
                    <label htmlFor="email">Email:</label>
                    <input type="email" id="email" name="email" value={memberData.email} onChange={handleInputChange} />
                </div>
                <div className={formStyles.formGroup}>
                    <label htmlFor="phoneNumber">Phone Number:</label>
                    <input type="text" id="phoneNumber" name="phoneNumber" value={memberData.phoneNumber} onChange={handleInputChange} />
                </div>
                <div className={formStyles.formGroup}>
                    <label htmlFor="status">Status:</label>
                    <select id="status" name="status" value={memberData.status} onChange={handleInputChange}>
                        <option value="Approved">Approved</option>
                        <option value="Inactive">Inactive</option>
                    </select>
                </div>


                <div className={formStyles.formGroup}>
                    <label htmlFor="newPhoto">Add/Replace Face Photo:</label> {/* Changed label */}
                    <input
                        type="file"
                        id="newPhoto"
                        name="newPhoto" // Field name for new photo
                        accept="image/*"
                        onChange={handleNewPhotoChange}
                        // Not 'required' for edit, user might only want to change text fields
                    />
                    <div style={{ marginTop: '10px' }}>
                        {newPhotoPreview && (
                            <img src={newPhotoPreview} alt="New Photo Preview" style={{ width: '100px', height: '100px', objectFit: 'cover', border: '1px solid #ccc' }} />
                        )}
                    </div>
                    <small>Uploading a new photo will send it for AI enrollment. Existing face data might be added to or replaced depending on AI service logic.</small>
                </div>

                <button type="submit" className={formStyles.submitButton} disabled={submitting}>
                    {submitting ? 'Updating...' : 'Update Member'}
                </button>
            </form>
        </div>
    );
}

export default EditMemberPage;