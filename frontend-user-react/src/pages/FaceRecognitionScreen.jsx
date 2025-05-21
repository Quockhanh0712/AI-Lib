// D:\AI-Lib\frontend-user-react\src\pages\FaceRecognitionScreen.jsx

import React, { useState, useEffect, useRef } from 'react';
// style.css đã được link trong index.html, không cần import ở đây

// Hàm tiện ích để chuyển đổi base64 string sang Blob object
function base64ToBlob(base64, mimeType) {
    const byteCharacters = atob(base64); // Giải mã base64 thành chuỗi nhị phân
    const byteArrays = [];

    for (let offset = 0; offset < byteCharacters.length; offset += 512) {
        const slice = byteCharacters.slice(offset, offset + 512); // Cắt thành từng phần nhỏ
        const byteNumbers = new Array(slice.length);
        for (let i = 0; i < slice.length; i++) {
            byteNumbers[i] = slice.charCodeAt(i); // Chuyển ký tự thành mã ASCII
        }
        const byteArray = new Uint8Array(byteNumbers); // Tạo Uint8Array từ mã ASCII
        byteArrays.push(byteArray);
    }

    return new Blob(byteArrays, { type: mimeType }); // Tạo Blob từ các Uint8Array
}


function FaceRecognitionScreen({ onNavigate, memberIdToRecognize }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [message, setMessage] = useState({ text: '', type: '' });
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [stream, setStream] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false); // Trạng thái để ngăn chặn gửi nhiều request

  // Hàm khởi tạo camera
  const startCamera = async () => {
    setMessage({ text: 'Đang khởi động camera...', type: 'info' });
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
      videoRef.current.srcObject = mediaStream;
      setStream(mediaStream);
      setIsCameraActive(true);
      setMessage({ text: 'Camera đã sẵn sàng. Vui lòng nhìn vào camera.', type: 'success' });
    } catch (err) {
      console.error('Lỗi khi truy cập camera:', err);
      setMessage({ text: 'Không thể truy cập camera. Vui lòng cấp quyền và thử lại.', type: 'error' });
      setIsCameraActive(false);
    }
  };

  // Hàm dừng camera
  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    setIsCameraActive(false);
    setMessage({ text: '', type: '' });
  };

  // Tự động khởi động camera khi component được render
  useEffect(() => {
    // THÊM: Kiểm tra memberIdToRecognize trước khi khởi động camera
    if (!memberIdToRecognize) {
      setMessage({ text: 'Không có mã thành viên. Vui lòng quay lại và nhập mã.', type: 'error' });
      return; // Không khởi động camera nếu không có mã thành viên
    }
    startCamera();

    // Dọn dẹp (stop camera) khi component unmount
    return () => {
      stopCamera();
    };
  }, [memberIdToRecognize]); // THÊM: memberIdToRecognize vào dependency array

  // Hàm chụp ảnh và gửi lên backend
  const captureAndRecognize = async () => {
    if (!isCameraActive || isProcessing || !memberIdToRecognize) { // THÊM: Kiểm tra memberIdToRecognize
      console.log('Camera not active, already processing, or member ID missing.');
      return;
    }

    setIsProcessing(true); // Đặt trạng thái đang xử lý
    setMessage({ text: 'Đang chụp ảnh và nhận diện khuôn mặt...', type: 'info' });

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');

    // Đảm bảo canvas có cùng kích thước với video để tránh biến dạng
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Vẽ khung hình hiện tại từ video lên canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Lấy dữ liệu ảnh dưới dạng base64
    const imageDataUrl = canvas.toDataURL('image/jpeg', 0.9); // Chất lượng 90%
    const base64Image = imageDataUrl.split(',')[1]; // Lấy phần base64 sau "data:image/jpeg;base64,"
    const mimeType = 'image/jpeg'; // Định dạng MIME của ảnh

    // Chuyển đổi base64 thành Blob một cách chính xác
    const imageBlob = base64ToBlob(base64Image, mimeType);

    console.log('Chụp ảnh thành công, gửi lên backend...');

    try {
      const BACKEND_API_URL = import.meta.env.VITE_BACKEND_API_URL;
      const RECOGNIZE_ENDPOINT = '/recognize-face/';

      // Tạo FormData để gửi file và các trường khác
      const formData = new FormData();
      formData.append('file', imageBlob, 'face.jpg'); // Gắn Blob vào FormData với tên 'file'
      formData.append('member_id', memberIdToRecognize);

      console.log(`Calling API: POST ${BACKEND_API_URL}${RECOGNIZE_ENDPOINT}`);
      const response = await fetch(`${BACKEND_API_URL}${RECOGNIZE_ENDPOINT}`, {
        method: 'POST',
        body: formData, // FormData sẽ tự động thiết lập Content-Type là multipart/form-data
      });

      const result = await response.json();
      console.log('Response from Backend:', response.status, result);

      if (!response.ok) {
        console.error('HTTP Error from Backend:', response.status, result);
        setMessage({ text: `Nhận diện thất bại: ${result.detail?.[0]?.msg || result.message || JSON.stringify(result)}`, type: 'error' });
      } else {
        if (result.success) {
          setMessage({ text: `Nhận diện thành công! Chào mừng ${result.user?.full_name || memberIdToRecognize}.`, type: 'success' });

          // Lấy thời gian hiện tại
          const now = new Date();
          console.log('Raw Date object (Client Time):', now); // Ghi log đối tượng Date gốc để kiểm tra

          // Định dạng giờ:phút:giây
          const time = now.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

          // Định dạng ngày/tháng/năm một cách tường minh (DD/MM/YYYY)
          const day = String(now.getDate()).padStart(2, '0');
          const month = String(now.getMonth() + 1).padStart(2, '0'); // Tháng trong JS bắt đầu từ 0
          const year = now.getFullYear();
          const date = `${day}/${month}/${year}`;

          const formattedEntryTime = `${time} ${date}`;
          console.log('Formatted Entry Time:', formattedEntryTime); // Ghi log chuỗi thời gian đã định dạng

          // 1. Hiển thị thông báo thành công trên màn hình video đang chạy
          // 2. Chờ 1.5 giây để người dùng đọc thông báo
          setTimeout(() => {
            stopCamera(); // Tắt camera (màn hình đen)
            // 3. Chờ thêm 1 giây (màn hình đen)
            setTimeout(() => {
              if (onNavigate) {
                // ĐÃ SỬA: Truyền memberId với key là 'memberId'
                onNavigate('mainMenuScreen', { 
                    user: result.user, 
                    entryTime: formattedEntryTime,
                    memberId: memberIdToRecognize // THÊM DÒNG NÀY
                });
              }
            }, 1000); // Thời gian chờ màn hình đen
          }, 1500); // Thời gian chờ thông báo hiển thị trên video
        } else {
          setMessage({ text: `Nhận diện thất bại: ${result.message || 'Khuôn mặt không khớp.'}`, type: 'error' });
        }
      }
    } catch (error) {
      console.error('Lỗi khi gửi yêu cầu nhận diện:', error);
      setMessage({ text: 'Đã xảy ra lỗi khi nhận diện khuôn mặt.', type: 'error' });
    } finally {
      setIsProcessing(false);
    }
  };

  // Hàm xử lý khi nút "Quay lại" được nhấn
  const handleBackToMemberIdInput = () => {
    console.log('Button "Quay lại" clicked from Face Recognition');
    stopCamera();
    if (onNavigate) {
      onNavigate('memberIdInputScreen');
    }
  };

  return (
    <section id="faceRecognitionScreen" className="screen"> {/* Sử dụng class "screen" */}
      <div className="container"> {/* Sử dụng class "container" */}
        <h1><i className="fas fa-camera"></i> Xác thực Khuôn mặt</h1>
        <p>Mã thành viên: <strong>{memberIdToRecognize}</strong></p>
        <p>Vui lòng nhìn thẳng vào camera để hệ thống nhận diện.</p>

        <div className="video-container"> {/* Sử dụng class "video-container" */}
          <video ref={videoRef} autoPlay playsInline muted></video> {/* Loại bỏ inline style, dùng CSS class */}
          <canvas ref={canvasRef} style={{ display: 'none' }}></canvas>
        </div>

        {message.text && (
          <div id="faceRecognitionMessage" className={`message ${message.type}`}> {/* Sử dụng class "message" */}
            {message.text}
          </div>
        )}

        <button
          id="captureButton"
          className="main-button" /* Sử dụng class "main-button" */
          onClick={captureAndRecognize}
          disabled={!isCameraActive || isProcessing}
        >
          <i className="fas fa-camera"></i> Chụp ảnh & Nhận diện
        </button>
        <button
          id="backToMemberIdInput"
          className="secondary-button" /* Sử dụng class "secondary-button" */
          onClick={handleBackToMemberIdInput}
        >
          <i className="fas fa-arrow-left"></i> Quay lại
        </button>
      </div>
    </section>
  );
}

export default FaceRecognitionScreen;
