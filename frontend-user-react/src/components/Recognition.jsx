import React, { useRef, useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom'; // Chỉ cần Link, không cần useNavigate nếu bạn không dùng
import styles from './Recognition.module.css'; // Import CSS Modules

const API_BASE_URL = process.env.REACT_APP_AI_SERVICE_URL || 'http://localhost:8001';

const Recognition = () => {
    // Không cần useNavigate nếu bạn không chủ động điều hướng bằng navigate('/path')
    // const navigate = useNavigate();

    const webcamRef = useRef(null);
    const finalFrameRef = useRef(null);
    const confirmMemberCodeRef = useRef(null);

    const [stream, setStream] = useState(null);
    const [isRecognizing, setIsRecognizing] = useState(false);
    const [recognitionInfo, setRecognitionInfo] = useState('');
    const [message, setMessage] = useState('');
    const [messageType, setMessageType] = useState('');
    const [showConfirmForm, setShowConfirmForm] = useState(false);
    const [capturedFinalFrame, setCapturedFinalFrame] = useState('');
    const [confirmMemberCode, setConfirmMemberCode] = useState('');

    const canvasRef = useRef(document.createElement('canvas')); // Canvas ẩn để xử lý khung hình

    /**
     * Bắt đầu stream webcam.
     */
    const startWebcam = useCallback(async (videoElement) => {
        if (!videoElement) {
            console.error("Video element not found for webcam.");
            return null;
        }
        setMessage('Đang khởi tạo camera...');
        setMessageType('info');
        try {
            const mediaStream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
            videoElement.srcObject = mediaStream;
            await videoElement.play();

            canvasRef.current.width = 640;
            canvasRef.current.height = 480;
            setStream(mediaStream);
            setMessage('Camera sẵn sàng. Đang chờ nhận diện...');
            setMessageType('info');
            return mediaStream;
        } catch (error) {
            setMessage(`Lỗi truy cập webcam: ${error.name} - ${error.message}`);
            setMessageType('error');
            console.error("Error accessing webcam:", error);
            // Xử lý các lỗi cụ thể về quyền truy cập
            if (error.name === "NotAllowedError" || error.name === "PermissionDeniedError") {
                setMessage("Bạn cần cấp quyền truy cập camera để sử dụng chức năng này.");
            } else if (error.name === "NotFoundError") {
                setMessage("Không tìm thấy thiết bị camera nào.");
            }
            return null;
        }
    }, []); // No dependencies for this simple function

    /**
     * Dừng stream webcam.
     */
    const stopWebcam = useCallback((currentStream, videoElement) => {
        if (currentStream) {
            currentStream.getTracks().forEach(track => track.stop());
        }
        if (videoElement) {
            videoElement.srcObject = null;
        }
        setStream(null);
    }, []);

    /**
     * Hàm reset tất cả các trạng thái liên quan đến nhận diện.
     */
    const resetRecognitionState = useCallback(() => {
        setIsRecognizing(false);
        stopWebcam(stream, webcamRef.current);
        setRecognitionInfo('');
        setMessage('');
        setMessageType('');
        setShowConfirmForm(false);
        setCapturedFinalFrame('');
        setConfirmMemberCode('');
    }, [stream, stopWebcam]);

    /**
     * Xử lý từng khung hình từ webcam để nhận diện.
     */
    const processFrame = useCallback(async () => {
        // Kiểm tra điều kiện dừng hoặc chưa sẵn sàng
        if (!isRecognizing || !webcamRef.current || !stream || webcamRef.current.readyState < 3) {
            // readyState < 3 nghĩa là video chưa sẵn sàng (HAVE_FUTURE_DATA, HAVE_ENOUGH_DATA)
            // Nếu chưa sẵn sàng, thử lại sau một khoảng ngắn
            if (isRecognizing && webcamRef.current && webcamRef.current.readyState < 3) {
                 setTimeout(processFrame, 100);
            }
            return;
        }

        const video = webcamRef.current;
        const canvas = canvasRef.current;
        const context = canvas.getContext('2d');

        // Đảm bảo video đã sẵn sàng và có kích thước hợp lệ
        if (video.videoWidth === 0 || video.videoHeight === 0) {
            console.warn("Video dimensions are 0. Retrying processFrame...");
            setTimeout(processFrame, 100); // Thử lại sau 100ms
            return;
        }
        
        context.drawImage(video, 0, 0, 640, 480);
        const frameData = canvas.toDataURL('image/jpeg', 0.8);

        try {
            const response = await axios.post(`${API_BASE_URL}/process-frame`, { frame: frameData });
            const data = response.data;

            if (data.full_name && data.similarity) {
                setRecognitionInfo(`Nhận diện: ${data.full_name} (Độ chính xác: ${(data.similarity * 100).toFixed(2)}%)`);
            } else {
                setRecognitionInfo('');
            }

            setMessage(data.status);
            // Cập nhật kiểu thông báo dựa trên trạng thái nhận diện
            if (data.status === 'Nhận diện thành công') {
                setMessageType('success');
            } else if (data.status.includes('Lỗi') || data.status.includes('Không tìm thấy')) {
                setMessageType('error');
            } else {
                setMessageType('info');
            }

            if (data.status === 'Nhận diện thành công') {
                setIsRecognizing(false); // Dừng quá trình nhận diện
                stopWebcam(stream, webcamRef.current); // Dừng webcam
                setShowConfirmForm(true); // Hiển thị form xác nhận điểm danh
                setCapturedFinalFrame(data.final_frame || ''); // Lưu và hiển thị frame cuối cùng
                
                // Tự động focus vào input mã thành viên
                setTimeout(() => {
                    confirmMemberCodeRef.current?.focus();
                }, 100);
            } else {
                // Tiếp tục xử lý khung hình nếu chưa thành công
                setTimeout(processFrame, 500);
            }
        } catch (error) {
            const errorMessage = error.response?.data?.detail || error.message;
            setMessage(`Lỗi kết nối server hoặc xử lý: ${errorMessage}`);
            setMessageType('error');
            console.error("Error processing frame:", error);
            resetRecognitionState(); // Reset toàn bộ trạng thái khi có lỗi nghiêm trọng
        }
    }, [isRecognizing, stream, stopWebcam, resetRecognitionState]);

    // useEffect để khởi động/dừng quá trình nhận diện
    useEffect(() => {
        if (isRecognizing) {
            processFrame(); // Bắt đầu vòng lặp xử lý khung hình
        }
        // Cleanup function: Dừng webcam khi component unmount hoặc isRecognizing thay đổi thành false
        return () => {
            if (stream) {
                stopWebcam(stream, webcamRef.current);
            }
        };
    }, [isRecognizing, processFrame, stream, stopWebcam]);

    const handleStartRecognition = async () => {
        resetRecognitionState(); // Reset mọi thứ trước khi bắt đầu mới
        const startedStream = await startWebcam(webcamRef.current);
        if (startedStream) {
            setIsRecognizing(true); // Bắt đầu vòng lặp processFrame
            setMessage('Đang nhận diện...');
            setMessageType('info');
        }
    };

    const handleStopRecognition = () => {
        resetRecognitionState();
        setMessage('Đã dừng nhận diện.');
        setMessageType('info');
    };

    const handleConfirmAttendance = async (e) => {
        e.preventDefault();

        if (!showConfirmForm || !confirmMemberCode) {
            setMessage('Không thể xác nhận. Vui lòng nhận diện khuôn mặt và nhập mã thành viên.');
            setMessageType('warning');
            return;
        }

        try {
            const response = await axios.post(`${API_BASE_URL}/confirm-attendance`, { member_code: confirmMemberCode });
            const data = response.data;
            setMessage(`Đã điểm danh: ${data.full_name}`);
            setMessageType('success');
            
            setTimeout(() => {
                resetRecognitionState(); // Reset trạng thái sau 3 giây để bắt đầu lại
            }, 3000);
            
        } catch (error) {
            const errorMessage = error.response?.data?.detail || error.message;
            setMessage(`Lỗi điểm danh: ${errorMessage}`);
            setMessageType('error');
            console.error("Error confirming attendance:", error);
        }
    };

    return (
        <div className={styles.recognitionContainer}>
            <h1 className={styles.mainTitle}>Hệ thống quản lý ra vào & điểm danh</h1>
            <h2 className={styles.subTitle}>Nhận diện khuôn mặt</h2>

            <div className={styles.contentWrapper}>
                {/* Phần Webcam và Final Frame */}
                <div className={styles.videoPanel}>
                    {/* Webcam chỉ hiển thị khi đang nhận diện và form xác nhận chưa hiện */}
                    {/* Thêm key để đảm bảo video element được render lại nếu cần */}
                    <video
                        key="webcam-feed"
                        ref={webcamRef}
                        autoPlay
                        playsInline
                        muted // Thêm muted để tránh lỗi autplay policy trên Chrome
                        className={`${styles.webcamVideo} ${showConfirmForm ? styles.hidden : ''}`}
                    ></video>
                    {/* Final Frame chỉ hiển thị khi có ảnh và form xác nhận đã hiện */}
                    <img
                        key="final-frame-display"
                        ref={finalFrameRef}
                        src={capturedFinalFrame || "data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=="}
                        alt="Khung hình cuối cùng"
                        className={`${styles.finalFrameImage} ${capturedFinalFrame && showConfirmForm ? '' : styles.hidden}`}
                    />
                </div>

                {/* Phần Thông tin và Xác nhận */}
                <div className={styles.infoPanel}>
                    <h3 className={styles.infoTitle}>Thông tin và Điểm danh</h3>
                    <div className={styles.buttonGroup}>
                        <button
                            onClick={handleStartRecognition}
                            // Nút Bắt đầu ẩn khi đang nhận diện HOẶC khi form xác nhận đang hiện
                            className={`${styles.actionButton} ${styles.startButton} ${(isRecognizing || showConfirmForm) ? styles.hidden : ''}`}
                        >
                            Bắt đầu nhận diện
                        </button>
                        <button
                            onClick={handleStopRecognition}
                            // Nút Dừng hiện khi đang nhận diện HOẶC khi form xác nhận đang hiện (để có thể reset)
                            className={`${styles.actionButton} ${styles.stopButton} ${(!isRecognizing && !showConfirmForm) ? styles.hidden : ''}`}
                        >
                            Dừng nhận diện
                        </button>
                    </div>

                    {recognitionInfo && <p className={`${styles.recognitionInfo} ${messageType === 'success' ? styles.successText : styles.infoText}`}>{recognitionInfo}</p>}
                    {message && <p className={`${styles.statusMessage} ${messageType === 'success' ? styles.successText : messageType === 'error' ? styles.errorText : styles.infoText}`}>{message}</p>}

                    <form onSubmit={handleConfirmAttendance} className={`${styles.confirmForm} ${showConfirmForm ? '' : styles.hidden}`}>
                        <label htmlFor="confirm_member_code" className={styles.formLabel}>Xác nhận điểm danh (mã thành viên):</label>
                        <input
                            type="text"
                            id="confirm_member_code"
                            name="confirm_member_code"
                            ref={confirmMemberCodeRef}
                            value={confirmMemberCode}
                            onChange={(e) => setConfirmMemberCode(e.target.value)}
                            required
                            className={styles.formInput}
                            placeholder="Nhập mã thành viên"
                        />
                        <button type="submit" className={`${styles.actionButton} ${styles.confirmButton}`}>
                            Xác nhận điểm danh
                        </button>
                    </form>
                </div>
            </div>

            {/* Các nút điều hướng */}
            <div className={styles.navigationButtons}>
                <Link to="/" className={styles.navButton}>Quay về Trang chủ</Link>
                <Link to="/students-in-library" className={styles.navButton}>Xem Sinh viên trong Thư viện</Link>
            </div>
        </div>
    );
};

export default Recognition;