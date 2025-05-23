// src/pages/MemberListPage.jsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom'; // Link is already imported
import { getAllMembers, deleteMember as apiDeleteMember } from '../services/memberService';
import styles from './MemberListPage.module.css';

function MemberListPage() {
    const [members, setMembers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchMembers = async () => {
        console.log("[MemberListPage] Attempting to fetch members...");
        setLoading(true);
        setError(null);
        try {
            const response = await getAllMembers({ skip: 0, limit: 100 }); // Or your desired default pagination
            console.log("[MemberListPage] API response received:", response);
            if (response && response.data) {
                setMembers(response.data);
            } else {
                console.error("[MemberListPage] API response or response.data is undefined/null.");
                setMembers([]);
                setError('Failed to parse member data from API.');
            }
        } catch (err) {
            console.error("[MemberListPage] Error fetching members:", err);
            if (err.response) {
                setError(`Failed to fetch members. API Error: ${err.response.data.detail || err.response.status}`);
            } else if (err.request) {
                 setError('Network error or no response from server while fetching members.');
            } else {
                setError(`Failed to fetch members: ${err.message}`);
            }
            setMembers([]);
        } finally {
            setLoading(false);
            console.log("[MemberListPage] Fetch members process finished. Loading set to false.");
        }
    };

    useEffect(() => {
        console.log("[MemberListPage] Component mounted, calling fetchMembers.");
        fetchMembers();
    }, []);

    const handleDeleteMember = async (userIdToDelete) => {
        console.log("[MemberListPage] handleDeleteMember called for ID:", userIdToDelete);
        if (!userIdToDelete && userIdToDelete !== 0) {
            alert("Error: No user ID specified for deletion.");
            return;
        }
        if (window.confirm(`Are you sure you want to delete member with ID ${userIdToDelete}? This action cannot be undone.`)) {
            try {
                await apiDeleteMember(userIdToDelete);
                alert('Member deleted successfully!');
                fetchMembers();
            } catch (err) {
                console.error("[MemberListPage] Error deleting member ID:", userIdToDelete, "Error:", err);
                alert(`Failed to delete member. API Error: ${(err.response && err.response.data && err.response.data.detail) || err.message || 'Unknown error'}`);
            }
        } else {
            console.log("[MemberListPage] User cancelled deletion for ID:", userIdToDelete);
        }
    };

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
                                    <Link to={`/admin/members/edit/${member.id}`} className={styles.actionLink || ''}>Edit</Link>
                                    <button
                                        onClick={() => handleDeleteMember(member.id)}
                                        className={`${styles.actionButton || ''} ${styles.deleteButton || ''}`}
                                    >
                                        Delete
                                    </button>
                                    {/* Link to user's specific attendance history */}
                                    <Link
                                        to={`/admin/attendance-history?member_code=${member.member_code}`}
                                        className={styles.actionLink || ''} // Reuse actionLink style or create new
                                        style={{ marginLeft: '10px' }} // Add some spacing
                                    >
                                        History
                                    </Link>
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