// src/components/HomePage.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import styles from './HomePage.module.css'; // Đường dẫn import CSS Modules đã được điều chỉnh

const HomePage = () => {
    return (
        <div className={styles.homePageContainer}>
            {/* Tiêu đề chính của hệ thống */}
            <h1 className={styles.mainTitle}>
                Hệ thống Quản lý Ra vào & Điểm danh Thư viện
            </h1>

            {/* Khối chứa các nút chức năng */}
            <div className={styles.buttonsContainer}>
                {/* Nút "Điểm danh" */}
                <Link
                    to="/recognition" // Đường dẫn đến trang điểm danh (Recognition.jsx)
                    className={`${styles.buttonLink} ${styles.recognitionButton}`}
                >
                    <svg className={styles.buttonIcon} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                    </svg>
                    <span className={styles.buttonText}>Điểm danh</span>
                    <p className={styles.buttonDescription}>Bật camera để nhận diện khuôn mặt và điểm danh</p>
                </Link>

                {/* Nút "Xem sinh viên trong thư viện" */}
                <Link
                    to="/students-in-library" // Đường dẫn đến trang xem sinh viên
                    className={`${styles.buttonLink} ${styles.studentsButton}`}
                >
                    <svg className={styles.buttonIcon} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.653-.131-1.282-.381-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.653.131-1.282.381-1.857m0 0a9.003 9.003 0 018.238 0M12 16a4 4 0 100-8 4 4 0 000 8z"></path>
                    </svg>
                    <span className={styles.buttonText}>Xem sinh viên trong thư viện</span>
                    <p className={styles.buttonDescription}>Xem danh sách sinh viên đang có mặt</p>
                </Link>
            </div>
        </div>
    );
};

export default HomePage;