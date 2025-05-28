// D:\AI-Lib\frontend-user-react\src\components\StudentsInLibrary.jsx

import React, { useState, useEffect } from 'react'; // THÊM useState và useEffect
import axios from 'axios'; // THÊM axios
import { Link } from 'react-router-dom';
import styles from './StudentsInLibrary.module.css';

const StudentsInLibrary = () => {
    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [checkoutMemberCode, setCheckoutMemberCode] = useState(''); // Đã có rồi, giữ nguyên
    const [message, setMessage] = useState(''); // Để hiển thị thông báo thành công/lỗi
    const [isPolling, setIsPolling] = useState(true); // Trạng thái để điều khiển việc polling

    // HÀM ĐỂ FETCH DANH SÁCH SINH VIÊN
    const fetchStudentsInLibrary = async () => {
        try {
            setError(null); // Reset lỗi trước mỗi lần fetch
            const response = await axios.get('http://localhost:8000/machine/current-members/');
            setStudents(response.data);
            setMessage(''); // Xóa thông báo cũ
        } catch (err) {
            console.error("Error fetching students in library:", err);
            setError("Không thể tải danh sách sinh viên. Vui lòng thử lại.");
            setStudents([]); // Đảm bảo danh sách rỗng nếu có lỗi
        } finally {
            setLoading(false);
        }
    };

    // HÀM XỬ LÝ CHECK-OUT
    const handleCheckout = async () => {
        if (!checkoutMemberCode) {
            setMessage('Vui lòng nhập mã thành viên để Check-Out.');
            return;
        }

        try {
            const response = await axios.post('http://localhost:8000/machine/attendance/check-out', {
                member_code: checkoutMemberCode
            });
            setMessage(response.data.message || 'Check-Out thành công!');
            setCheckoutMemberCode(''); // Xóa input sau khi check-out
            // Sau khi check-out, gọi lại hàm fetch để cập nhật danh sách
            fetchStudentsInLibrary();
        } catch (err) {
            console.error("Error during check-out:", err);
            if (err.response && err.response.data && err.response.data.detail) {
                setMessage(`Lỗi Check-Out: ${err.response.data.detail}`);
            } else {
                setMessage('Lỗi khi thực hiện Check-Out. Vui lòng thử lại.');
            }
        }
    };

    // useEffect để fetch dữ liệu lần đầu và thiết lập polling
    useEffect(() => {
        fetchStudentsInLibrary(); // Fetch dữ liệu lần đầu

        let intervalId;
        if (isPolling) {
            // Thiết lập polling mỗi 5 giây (hoặc thời gian bạn muốn)
            intervalId = setInterval(() => {
                fetchStudentsInLibrary();
            }, 5000); // Poll mỗi 5 giây
        }

        // Cleanup function để xóa interval khi component unmount
        return () => {
            if (intervalId) {
                clearInterval(intervalId);
            }
        };
    }, [isPolling]); // isPolling là dependency để control việc polling

    if (loading) {
        return <div className={styles.loading}>Đang tải danh sách...</div>;
    }

    return (
        <div className={styles.studentsInLibraryContainer}>
            <div className={styles.studentsListCard}>
                <h1 className={styles.pageTitle}>Sinh viên đang có mặt trong thư viện</h1>

                {message && <p className={styles.message}>{message}</p>} {/* Hiển thị thông báo */}

                <div className={styles.checkoutSection}>
                    <input
                        type="text"
                        placeholder="Nhập mã thành viên để Check-Out"
                        value={checkoutMemberCode}
                        onChange={(e) => setCheckoutMemberCode(e.target.value)}
                        className={styles.memberCodeInput}
                    />
                    <button onClick={handleCheckout} className={styles.checkoutButton}>
                        Check Out
                    </button>
                </div>

                {error ? (
                    <p className={styles.errorText}>{error}</p>
                ) : students.length === 0 ? (
                    <p className={styles.placeholderText}>Chưa có sinh viên nào đang có mặt trong thư viện.</p>
                ) : (
                    <table className={styles.studentsTable}>
                        <thead>
                            <tr>
                                <th>Họ và tên</th>
                                <th>Thời gian vào</th>      
                            </tr>
                        </thead>
                        <tbody>
                            {students.map((student) => (
                                <tr key={student.id}>
                                    <td>{student.user_session_owner.full_name}</td>
                                    <td>{student.entry_time}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}

                <div className={styles.backButtonContainer}>
                    <Link to="/" className={styles.backButton}>
                        Quay về trang chủ
                    </Link>
                </div>
            </div>
        </div>
    );
};

export default StudentsInLibrary;