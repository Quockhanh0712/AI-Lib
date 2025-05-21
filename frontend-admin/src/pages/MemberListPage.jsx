// src/pages/MemberListPage.jsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getAllMembers, deleteMember as apiDeleteMember } from '../services/memberService'; // Ensure path is correct
import styles from './MemberListPage.module.css'; // Ensure path is correct and you have this file

function MemberListPage() {
    const [members, setMembers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchMembers = async () => {
        console.log("[MemberListPage] Attempting to fetch members...");
        setLoading(true);
        setError(null); // Clear previous errors
        try {
            // Example: get all members, no filters for now
            // The API GET /admin/users/ takes optional query params: skip, limit, status_filter
            const response = await getAllMembers({ skip: 0, limit: 100 }); // Pass params if needed
            console.log("[MemberListPage] API response received:", response);

            if (response && response.data) { // Check if response and response.data exist
                setMembers(response.data);
                console.log("[MemberListPage] Members set to state:", response.data);
            } else {
                console.error("[MemberListPage] API response or response.data is undefined/null.");
                setMembers([]); // Set to empty array if response is not as expected
                setError('Failed to parse member data from API.');
            }
        } catch (err) {
            console.error("[MemberListPage] Error fetching members:", err);
            // More detailed error checking
            if (err.response) { // Axios error structure
                console.error("[MemberListPage] API Error Status:", err.response.status);
                console.error("[MemberListPage] API Error Data:", err.response.data);
                setError(`Failed to fetch members. API Error: ${err.response.data.detail || err.response.status}`);
            } else if (err.request) { // Network error, CORS issue (less likely now but good to check)
                 setError('Network error or no response from server while fetching members.');
            } else { // Other JS error
                setError(`Failed to fetch members: ${err.message}`);
            }
            setMembers([]); // Clear members on error
        } finally {
            setLoading(false);
            console.log("[MemberListPage] Fetch members process finished. Loading set to false.");
        }
    };

    useEffect(() => {
        console.log("[MemberListPage] Component mounted, calling fetchMembers.");
        fetchMembers();
    }, []); // Empty dependency array means this runs once on mount

    // Make sure apiDeleteMember is correctly imported at the top of your file:
// import { getAllMembers, deleteMember as apiDeleteMember } from '../services/memberService';

// ... inside your MemberListPage component ...

    const handleDeleteMember = async (userIdToDelete) => {
        console.log("[MemberListPage] handleDeleteMember called for ID:", userIdToDelete); // For debugging

        if (!userIdToDelete && userIdToDelete !== 0) { // Check if userIdToDelete is undefined, null, or empty string (0 is a valid ID)
            console.error("[MemberListPage] No userIdToDelete provided to handleDeleteMember.");
            alert("Error: No user ID specified for deletion.");
            return;
        }

        // Confirmation dialog
        if (window.confirm(`Are you sure you want to delete member with ID ${userIdToDelete}? This action cannot be undone.`)) {
            console.log("[MemberListPage] User confirmed deletion for ID:", userIdToDelete);
            try {
                console.log("[MemberListPage] Calling deleteMember service (apiDeleteMember) for ID:", userIdToDelete);
                await apiDeleteMember(userIdToDelete); // This calls the function from memberService.js

                console.log("[MemberListPage] deleteMember service call successful for ID:", userIdToDelete);
                alert('Member deleted successfully!');

                // Refetch members to update the list after deletion
                console.log("[MemberListPage] Re-fetching members after deletion...");
                fetchMembers(); // This function should already be defined in your MemberListPage to get all members
            } catch (err) {
                console.error("[MemberListPage] Error deleting member ID:", userIdToDelete, "Error:", err);
                if (err.response) { // Axios error
                    alert(`Failed to delete member. API Error: ${err.response.data.detail || err.response.status}`);
                } else { // Other JavaScript errors
                    alert(`Failed to delete member: ${err.message || 'An unknown error occurred.'}`);
                }
            }
        } else {
            console.log("[MemberListPage] User cancelled deletion for ID:", userIdToDelete);
        }
    };

    console.log("[MemberListPage] Rendering. Loading:", loading, "Error:", error, "Members count:", members.length);

    if (loading) {
        return <p className={styles.loadingText || ''}>Loading members...</p>;
    }
    if (error) {
        return <p className={styles.errorText || ''}>Error: {error}</p>;
    }

    return (
        <div className={styles.pageContainer || ''}>
            <div className={styles.header || ''}>
                <h2 className={styles.title || ''}>Member Management</h2>
                <Link to="/admin/members/add" className={styles.addButton || ''}>Add New Member</Link>
            </div>

            {members.length === 0 ? (
                <p className={styles.noDataText || ''}>No members found. (Is the database seeded with users?)</p>
            ) : (
                <table className={styles.table || ''}>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Member Code</th>
                            <th>Full Name</th>
                            <th>Email</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {members.map(member => (
                            <tr key={member.id}>
                                <td>{member.id}</td>
                                <td>{member.member_code}</td>
                                <td>{member.full_name}</td>
                                <td>{member.email || 'N/A'}</td>
                                <td>{member.status}</td>
                                <td className={styles.actions || ''}>
                                    <Link to={`/admin/members/edit/${member.id}`}>Edit</Link>
                                    <button
                                        onClick={() => handleDeleteMember(member.id)}
                                        className={styles.deleteButton || ''}
                                    >
                                        Delete
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
}

export default MemberListPage;