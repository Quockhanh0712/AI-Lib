// src/pages/AttendanceHistoryPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { getAdminAllCompletedAttendance } from '../services/memberService';
import styles from './AttendanceHistoryPage.module.css'; // <<< USING ITS OWN CSS MODULE PRIMARILY

function AttendanceHistoryPage() {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchParams, setSearchParams] = useSearchParams();

    const [filters, setFilters] = useState({
        member_code_filter: searchParams.get('member_code') || '',
        start_date_filter: searchParams.get('start_date') || '',
        end_date_filter: searchParams.get('end_date') || '',
    });
    const [currentPage, setCurrentPage] = useState(0);
    const [limitPerPage] = useState(20); // Or make this configurable

    const fetchHistory = useCallback(async (currentFilters, page) => {
        console.log("[AttendanceHistoryPage] Fetching history with filters:", currentFilters, "Page:", page);
        setLoading(true);
        setError(null);
        try {
            const paramsToSend = {
                skip: page * limitPerPage,
                limit: limitPerPage,
            };
            if (currentFilters.member_code_filter) paramsToSend.member_code_filter = currentFilters.member_code_filter;
            if (currentFilters.start_date_filter) paramsToSend.start_date_filter = currentFilters.start_date_filter;
            if (currentFilters.end_date_filter) paramsToSend.end_date_filter = currentFilters.end_date_filter;

            const responseData = await getAdminAllCompletedAttendance(paramsToSend);
            if (responseData) {
                setHistory(responseData);
            } else {
                setHistory([]);
                setError("No data received or unexpected format.");
            }
        } catch (err) {
            console.error("[AttendanceHistoryPage] Error fetching history:", err);
            setHistory([]);
            if (err.response) {
                setError(`API Error: ${err.response.data.detail || err.response.status}`);
            } else {
                setError(err.message || "Failed to fetch attendance history.");
            }
        } finally {
            setLoading(false);
        }
    }, [limitPerPage]);

    useEffect(() => {
        const initialFilters = {
            member_code_filter: searchParams.get('member_code') || '',
            start_date_filter: searchParams.get('start_date') || '',
            end_date_filter: searchParams.get('end_date') || '',
        };
        setFilters(initialFilters);
        fetchHistory(initialFilters, currentPage);
    }, [searchParams, fetchHistory, currentPage]); // Note: fetchHistory is in dep array

    const handleFilterChange = (event) => {
        const { name, value } = event.target;
        setFilters(prevFilters => ({ ...prevFilters, [name]: value }));
    };

    const handleApplyFilters = (event) => {
        event.preventDefault();
        const newSearchParams = new URLSearchParams();
        if (filters.member_code_filter) newSearchParams.set('member_code', filters.member_code_filter);
        if (filters.start_date_filter) newSearchParams.set('start_date', filters.start_date_filter);
        if (filters.end_date_filter) newSearchParams.set('end_date', filters.end_date_filter);
        setSearchParams(newSearchParams);
        setCurrentPage(0); // Reset to first page on new filter
    };

    const handleNextPage = () => {
        if (history.length < limitPerPage) return;
        setCurrentPage(prevPage => prevPage + 1);
    };

    const handlePreviousPage = () => {
        setCurrentPage(prevPage => Math.max(0, prevPage - 1));
    };

    if (loading) return <p className={styles.loadingText}>Loading attendance history...</p>;

    return (
        <div className={styles.pageContainer}>
            <div className={styles.header}>
                <h2 className={styles.title}>Attendance History</h2>
                {/* Optionally, a link to go back to member list or clear filters */}
                <Link to="/admin/attendance-history" onClick={() => {
                    setFilters({ member_code_filter: '', start_date_filter: '', end_date_filter: ''});
                    setCurrentPage(0);
                    // setSearchParams({}); // This would also trigger refetch
                }} className={styles.clearFiltersButton}>Clear Filters / Show All</Link>
            </div>

            <form onSubmit={handleApplyFilters} className={styles.filterForm}>
                <div className={styles.formGroup}>
                    <label htmlFor="member_code_filter">Member Code:</label>
                    <input
                        type="text"
                        id="member_code_filter"
                        name="member_code_filter"
                        value={filters.member_code_filter}
                        onChange={handleFilterChange}
                        placeholder="Filter by Member Code"
                    />
                </div>
                <div className={styles.formGroup}>
                    <label htmlFor="start_date_filter">Start Date:</label>
                    <input
                        type="date"
                        id="start_date_filter"
                        name="start_date_filter"
                        value={filters.start_date_filter}
                        onChange={handleFilterChange}
                    />
                </div>
                <div className={styles.formGroup}>
                    <label htmlFor="end_date_filter">End Date:</label>
                    <input
                        type="date"
                        id="end_date_filter"
                        name="end_date_filter"
                        value={filters.end_date_filter}
                        onChange={handleFilterChange}
                    />
                </div>
                <button type="submit" className={styles.filterButton}>Apply Filters</button>
            </form>

            {error && <p className={styles.errorText}>Error: {error}</p>}

            {history.length === 0 && !loading ? (
                <p className={styles.noDataText}>No attendance records found for the current filters.</p>
            ) : (
                <>
                    <table className={styles.historyTable}>
                        <thead>
                            <tr>
                                <th>Session ID</th>
                                <th>User ID</th>
                                <th>Entry Time</th>
                                <th>Exit Time</th>
                                <th>Duration (Mins)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {history.map(record => (
                                <tr key={record.id}>
                                    <td>{record.id}</td>
                                    <td>{record.user_id}</td> {/* Consider fetching/joining member_code or name */}
                                    <td>{record.entry_time ? new Date(record.entry_time).toLocaleString() : 'N/A'}</td>
                                    <td>{record.exit_time ? new Date(record.exit_time).toLocaleString() : 'N/A'}</td>
                                    <td>{record.duration_minutes !== null ? record.duration_minutes : 'N/A'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    <div className={styles.paginationControls}>
                        <button onClick={handlePreviousPage} disabled={currentPage === 0 || loading} className={styles.pageButton}>Previous</button>
                        <span>Page {currentPage + 1}</span>
                        <button onClick={handleNextPage} disabled={history.length < limitPerPage || loading} className={styles.pageButton}>Next</button>
                    </div>
                </>
            )}
        </div>
    );
}

export default AttendanceHistoryPage;