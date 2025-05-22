// src/pages/AddMemberPage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { createMember } from '../services/memberService';
import formStyles from '../components/forms/Form.module.css';

function AddMemberPage() {
    const [memberCode, setMemberCode] = useState('');
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [phoneNumber, setPhoneNumber] = useState('');
    const [photo, setPhoto] = useState(null); // State for a single File object
    const [photoPreview, setPhotoPreview] = useState(null); // State for a single preview URL

    const [error, setError] = useState(null);
    const [submitting, setSubmitting] = useState(false);
    const navigate = useNavigate();

    const handlePhotoChange = (event) => {
        // Clean up old preview if it exists
        if (photoPreview) {
            URL.revokeObjectURL(photoPreview);
        }

        const file = event.target.files[0]; // Get the first (and only) file

        if (file) {
            setPhoto(file); // Store the single File object
            setPhotoPreview(URL.createObjectURL(file)); // Create preview for the single file
        } else {
            // No file selected or selection cleared
            setPhoto(null);
            setPhotoPreview(null);
        }
    };

    // Cleanup ObjectURL when the component unmounts or photoPreview changes
    useEffect(() => {
        return () => {
            if (photoPreview) {
                URL.revokeObjectURL(photoPreview);
            }
        };
    }, [photoPreview]);


    const handleSubmit = async (event) => {
        event.preventDefault();
        console.log("[AddMemberPage] handleSubmit called");
        setError(null);
        setSubmitting(true);

        if (!memberCode.trim() || !fullName.trim()) {
            setError('Member Code and Full Name are required.');
            setSubmitting(false);
            return;
        }
        // Assuming a photo is still required for initial enrollment
        if (!photo) {
            setError('A photo is required for face enrollment.');
            setSubmitting(false);
            return;
        }

        const formData = new FormData();
        formData.append('member_code', memberCode.trim());
        formData.append('full_name', fullName.trim());
        if (email.trim()) formData.append('email', email.trim());
        if (phoneNumber.trim()) formData.append('phone_number', phoneNumber.trim());
        
        // Append the single photo file.
        // The backend (admin_endpoints.py create_new_user_by_admin_endpoint)
        // will be changed to expect a single 'photo' (not 'photos')
        formData.append('photo', photo, photo.name);

        console.log("[AddMemberPage] Data being sent to createMember service (FormData):");
        for (let pair of formData.entries()) {
            console.log(pair[0]+ ': ' + (pair[1] instanceof File ? pair[1].name : pair[1]));
        }

        try {
            console.log("[AddMemberPage] Calling createMember service...");
            await createMember(formData);
            console.log("[AddMemberPage] createMember successful");
            alert('Member created and photo submitted successfully!');
            navigate('/admin/members');
        } catch (err) {
            console.error("[AddMemberPage] Error in handleSubmit:", err);
            // ... (your existing detailed error handling) ...
            if (err.response && err.response.data && err.response.data.detail) {
                if (Array.isArray(err.response.data.detail)) {
                    const errorMessages = err.response.data.detail.map(d => `${d.loc.join(' -> ')}: ${d.msg}`).join('; ');
                    setError(`Validation Error(s): ${errorMessages}`);
                } else {
                    setError(`API Error: ${err.response.data.detail}`);
                }
            } else if (err.response && err.response.status) {
                setError(`API Error: ${err.response.status} - ${err.response.statusText || 'Failed to create member'}`);
            } else {
                setError(err.message || 'Failed to create member. Please try again.');
            }
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className={formStyles.formContainer}>
            <h2 className={formStyles.formTitle}>Add New Member (with Face Enrollment)</h2>
            {error && <p className={formStyles.errorText}>{error}</p>}
            <form onSubmit={handleSubmit}>
                {/* ... (memberCode, fullName, email, phoneNumber inputs as before) ... */}
                <div className={formStyles.formGroup}>
                    <label htmlFor="memberCode">Member Code: *</label>
                    <input type="text" id="memberCode" value={memberCode} onChange={(e) => setMemberCode(e.target.value)} required autoComplete="off"/>
                </div>
                <div className={formStyles.formGroup}>
                    <label htmlFor="fullName">Full Name: *</label>
                    <input type="text" id="fullName" value={fullName} onChange={(e) => setFullName(e.target.value)} required autoComplete="off"/>
                </div>
                <div className={formStyles.formGroup}>
                    <label htmlFor="email">Email:</label>
                    <input type="email" id="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="off"/>
                </div>
                <div className={formStyles.formGroup}>
                    <label htmlFor="phoneNumber">Phone Number:</label>
                    <input type="text" id="phoneNumber" value={phoneNumber} onChange={(e) => setPhoneNumber(e.target.value)} autoComplete="off"/>
                </div>

                <div className={formStyles.formGroup}>
                    <label htmlFor="photo">Member Photo: *</label> {/* Changed label */}
                    <input
                        type="file"
                        id="photo" // Changed id
                        name="photo" // Changed name to singular 'photo'
                        // REMOVED multiple attribute
                        accept="image/*"
                        onChange={handlePhotoChange}
                        required // Still required for this flow
                    />
                    <div style={{ marginTop: '10px' }}>
                        {photoPreview && ( // Display single preview
                            <img src={photoPreview} alt="Preview" style={{ width: '100px', height: '100px', objectFit: 'cover', border: '1px solid #ccc' }} />
                        )}
                    </div>
                </div>

                <button type="submit" className={formStyles.submitButton} disabled={submitting}>
                    {submitting ? 'Submitting...' : 'Create Member & Submit Face'}
                </button>
            </form>
        </div>
    );
}

export default AddMemberPage;