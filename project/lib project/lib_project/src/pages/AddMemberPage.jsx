// src/pages/AddMemberPage.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createMember } from '../services/memberService'; // Ensure this path is correct
import formStyles from '../components/forms/Form.module.css'; // Ensure this path is correct

function AddMemberPage() {
    // State variables for your form inputs
    const [memberCode, setMemberCode] = useState('');
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [phoneNumber, setPhoneNumber] = useState('');

    const [error, setError] = useState(null);
    const [submitting, setSubmitting] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (event) => {
        event.preventDefault();
        console.log("[AddMemberPage] handleSubmit called"); // For debugging
        setError(null); // Clear previous errors
        setSubmitting(true);

        if (!memberCode.trim() || !fullName.trim()) { // Added .trim() for basic validation
            setError('Member Code and Full Name are required.');
            setSubmitting(false);
            return;
        }

        // Construct the data object to send to the service
        // Use the actual state variable names here
        const memberData = {
            member_code: memberCode.trim(), // Use the state variable 'memberCode'
            full_name: fullName.trim(),     // Use the state variable 'fullName'
            email: email.trim() || null,             // Send null if empty, or backend might prefer empty string
            phone_number: phoneNumber.trim() || null // Send null if empty
        };
        console.log("[AddMemberPage] Data being sent to createMember service:", memberData);

        try {
            console.log("[AddMemberPage] Calling createMember service...");
            await createMember(memberData); // createMember service expects an object
            console.log("[AddMemberPage] createMember successful");
            alert('Member created successfully!'); // Simple feedback
            navigate('/admin/members'); // Navigate back to the members list
            console.log("[AddMemberPage] Navigated to /admin/members");
        } catch (err) {
            console.error("[AddMemberPage] Error in handleSubmit:", err);
            if (err && err.data && err.data.detail) {
                // Handle FastAPI validation errors (which come as an array in err.data.detail)
                if (Array.isArray(err.data.detail)) {
                    const errorMessages = err.data.detail.map(d => `${d.loc.join(' -> ')}: ${d.msg}`).join('; ');
                    setError(`Validation Error(s): ${errorMessages}`);
                } else {
                    // Handle other FastAPI error details (string)
                    setError(`API Error: ${err.data.detail}`);
                }
            } else if (err && err.status) { // Other Axios errors with a status (e.g. network error from service)
                setError(`API Error: ${err.status} - ${err.statusText || 'Failed to create member'}`);
            } else { // JavaScript errors or other unexpected errors
                setError(err.message || 'Failed to create member. Please try again.');
            }
        } finally {
            setSubmitting(false);
            console.log("[AddMemberPage] handleSubmit finally block executed.");
        }
    };

    return (
        <div className={formStyles.formContainer}>
            <h2 className={formStyles.formTitle}>Add New Member</h2>
            {error && <p className={formStyles.errorText}>{error}</p>}
            <form onSubmit={handleSubmit}>
                <div className={formStyles.formGroup}>
                    <label htmlFor="memberCode">Member Code: *</label>
                    <input
                        type="text"
                        id="memberCode"
                        value={memberCode}
                        onChange={(e) => setMemberCode(e.target.value)}
                        required
                        autoComplete="off"
                    />
                </div>
                <div className={formStyles.formGroup}>
                    <label htmlFor="fullName">Full Name: *</label>
                    <input
                        type="text"
                        id="fullName"
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        required
                        autoComplete="off"
                    />
                </div>
                <div className={formStyles.formGroup}>
                    <label htmlFor="email">Email:</label>
                    <input
                        type="email"
                        id="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        autoComplete="off"
                    />
                </div>
                <div className={formStyles.formGroup}>
                    <label htmlFor="phoneNumber">Phone Number:</label>
                    <input
                        type="text" // Could be "tel" for better mobile UX
                        id="phoneNumber"
                        value={phoneNumber}
                        onChange={(e) => setPhoneNumber(e.target.value)}
                        autoComplete="off"
                    />
                </div>
                {/* If you were to add a facePhoto input:
                <div>
                    <label htmlFor="facePhoto">Face Photo:</label>
                    <input type="file" id="facePhoto" onChange={(e) => setFacePhoto(e.target.files[0])} />
                </div>
                */}
                <button type="submit" className={formStyles.submitButton} disabled={submitting}>
                    {submitting ? 'Submitting...' : 'Create Member'}
                </button>
            </form>
        </div>
    );
}

export default AddMemberPage;