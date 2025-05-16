// frontend/public/script.js

document.addEventListener('DOMContentLoaded', () => {
    // --- Lấy các phần tử màn hình ---
    const mainMenuScreen = document.getElementById('mainMenuScreen');
    const memberIdInputScreen = document.getElementById('memberIdInputScreen');
    const faceRecognitionScreen = document.getElementById('faceRecognitionScreen');
    const viewMembersScreen = document.getElementById('viewMembersScreen'); // Màn hình mới
    const registerMemberScreen = document.getElementById('registerMemberScreen'); // Màn hình mới

    // --- Lấy các nút điều hướng trên màn hình chính ---
    const goToMemberIdInputButton = document.getElementById('goToMemberIdInput');
    const goToViewMembersScreenButton = document.getElementById('goToViewMembersScreen'); // Nút mới
    const goToRegisterMemberScreenButton = document.getElementById('goToRegisterMemberScreen'); // Nút mới

    // --- Lấy các nút "Quay lại" ---
    const backToMainFromMemberIdButton = document.getElementById('backToMainFromMemberId');
    const backToMemberIdInputButton = document.getElementById('backToMemberIdInput');
    const backToMainFromViewMembersButton = document.getElementById('backToMainFromViewMembers'); // Nút mới
    const backToMainFromRegisterButton = document.getElementById('backToMainFromRegister'); // Nút mới

    // --- Lấy các phần tử của màn hình nhập mã thành viên ---
    const memberIdInput = document.getElementById('memberIdInput');
    const submitMemberIdButton = document.getElementById('submitMemberIdButton');
    const memberIdMessageDiv = document.getElementById('memberIdMessage');

    // --- Lấy các phần tử của màn hình xác thực khuôn mặt ---
    const displayMemberId = document.getElementById('displayMemberId');
    const webcamFeed = document.getElementById('webcamFeed');
    const canvasForCapture = document.getElementById('canvasForCapture');
    const captureImageButton = document.getElementById('captureImageButton');

    // --- Lấy các phần tử của màn hình đăng ký thành viên ---
    const regNameInput = document.getElementById('regName');
    const regEmailInput = document.getElementById('regEmail');
    const regPhoneInput = document.getElementById('regPhone');
    const submitRegistrationButton = document.getElementById('submitRegistration');

    let mediaStream = null;

    // --- Hàm điều khiển hiển thị màn hình ---
    function showScreen(screenToShow) {
        const allScreens = document.querySelectorAll('.screen');
        allScreens.forEach(screen => {
            screen.classList.add('hidden');
        });
        screenToShow.classList.remove('hidden');

        if (screenToShow === faceRecognitionScreen) {
            startWebcam();
        } else {
            stopWebcam();
        }

        // Xóa thông báo lỗi và input khi chuyển màn hình (nếu có)
        if (memberIdInput) memberIdInput.value = '';
        if (memberIdMessageDiv) {
            memberIdMessageDiv.textContent = '';
            memberIdMessageDiv.className = 'message';
        }
        // Có thể thêm logic xóa form đăng ký ở đây
        if (regNameInput) regNameInput.value = '';
        if (regEmailInput) regEmailInput.value = '';
        if (regPhoneInput) regPhoneInput.value = '';
    }

    // --- Hàm để hiển thị thông báo trên màn hình nhập mã ---
    function showMemberIdMessage(msg, type) {
        memberIdMessageDiv.textContent = msg;
        memberIdMessageDiv.className = 'message ' + type;
    }

    // --- Xử lý Webcam ---
    async function startWebcam() {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            try {
                mediaStream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
                webcamFeed.srcObject = mediaStream;
                webcamFeed.play();

                webcamFeed.addEventListener('loadedmetadata', () => {
                    canvasForCapture.width = webcamFeed.videoWidth;
                    canvasForCapture.height = webcamFeed.videoHeight;
                });
                console.log('Webcam đã khởi động.');
            } catch (error) {
                console.error('Lỗi khi truy cập webcam:', error);
                alert('Không thể truy cập webcam. Vui lòng cho phép trình duyệt sử dụng camera và thử lại.');
                showScreen(memberIdInputScreen);
            }
        } else {
            alert('Trình duyệt của bạn không hỗ trợ truy cập webcam.');
            showScreen(memberIdInputScreen);
        }
    }

    function stopWebcam() {
        if (mediaStream) {
            mediaStream.getTracks().forEach(track => track.stop());
            mediaStream = null;
            webcamFeed.srcObject = null;
            console.log('Webcam đã dừng.');
        }
    }

    // --- Xử lý khi nhấn nút "Chụp ảnh" (gửi ảnh đến Backend) ---
    if (captureImageButton) {
        captureImageButton.addEventListener('click', async () => {
            if (!webcamFeed.srcObject) {
                alert('Webcam chưa sẵn sàng để chụp ảnh.');
                return;
            }

            const context = canvasForCapture.getContext('2d');
            context.translate(canvasForCapture.width, 0);
            context.scale(-1, 1);
            context.drawImage(webcamFeed, 0, 0, canvasForCapture.width, canvasForCapture.height);
            context.setTransform(1, 0, 0, 1, 0, 0);

            const imageDataURL = canvasForCapture.toDataURL('image/jpeg', 0.9);
            const currentMemberId = displayMemberId.textContent;

            console.log('Đang gửi ảnh và mã thành viên đến Backend...');
            
            try {
                const response = await fetch('http://localhost:5000/recognize_face', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        member_id: currentMemberId,
                        image: imageDataURL
                    }),
                });

                const result = await response.json();
                console.log('Phản hồi từ Backend:', result);

                if (result.status === 'success') {
                    alert(`Xác thực thành công! Chào mừng ${result.member_name} (ID: ${result.member_id})`);
                    showScreen(mainMenuScreen);
                } else {
                    alert(`Xác thực thất bại: ${result.message}`);
                }

            } catch (error) {
                console.error('Lỗi khi gửi yêu cầu đến Backend:', error);
                alert('Đã xảy ra lỗi khi kết nối với hệ thống nhận diện. Vui lòng thử lại.');
            }
        });
    }

    // --- Xử lý sự kiện nút bấm điều hướng ---

    // Nút "Điểm danh Khuôn mặt" trên màn hình chính -> Chuyển đến màn hình nhập mã
    if (goToMemberIdInputButton) {
        goToMemberIdInputButton.addEventListener('click', () => {
            showScreen(memberIdInputScreen);
            memberIdInput.focus();
        });
    }

    // Nút "Xem Người đang ở Thư viện" trên màn hình chính -> Chuyển đến màn hình xem thành viên
    if (goToViewMembersScreenButton) {
        goToViewMembersScreenButton.addEventListener('click', () => {
            showScreen(viewMembersScreen);
            // TODO: Tại đây, bạn có thể gọi backend để tải danh sách thành viên
            // alert('Tính năng Xem Người đang ở Thư viện sẽ hiển thị danh sách tại đây!');
        });
    }

    // Nút "Gửi Yêu cầu Đăng ký Thành viên" trên màn hình chính -> Chuyển đến màn hình đăng ký
    if (goToRegisterMemberScreenButton) {
        goToRegisterMemberScreenButton.addEventListener('click', () => {
            showScreen(registerMemberScreen);
            regNameInput.focus(); // Tự động focus vào ô tên
        });
    }

    // Nút "Quay lại" từ màn hình nhập mã -> Về màn hình chính
    if (backToMainFromMemberIdButton) {
        backToMainFromMemberIdButton.addEventListener('click', () => {
            showScreen(mainMenuScreen);
        });
    }

    // Nút "Quay lại" từ màn hình xác thực khuôn mặt -> Về màn hình nhập mã
    if (backToMemberIdInputButton) {
        backToMemberIdInputButton.addEventListener('click', () => {
            showScreen(memberIdInputScreen);
            memberIdInput.focus();
        });
    }

    // Nút "Quay lại" từ màn hình xem thành viên -> Về màn hình chính
    if (backToMainFromViewMembersButton) {
        backToMainFromViewMembersButton.addEventListener('click', () => {
            showScreen(mainMenuScreen);
        });
    }

    // Nút "Quay lại" từ màn hình đăng ký thành viên -> Về màn hình chính
    if (backToMainFromRegisterButton) {
        backToMainFromRegisterButton.addEventListener('click', () => {
            showScreen(mainMenuScreen);
        });
    }

    // --- Logic cho màn hình Nhập Mã Thành viên ---

    // Xử lý khi nhấn nút "Kiểm tra"
    if (submitMemberIdButton) {
        submitMemberIdButton.addEventListener('click', () => {
            const memberId = memberIdInput.value.trim();

            if (memberId === '') {
                showMemberIdMessage('Vui lòng nhập mã thành viên.', 'error');
                return;
            }

            console.log('Mã thành viên đã nhập:', memberId);

            if (memberId.length === 5 && !isNaN(memberId)) {
                showMemberIdMessage('Mã thành viên hợp lệ!', 'success');
                displayMemberId.textContent = memberId;
                showScreen(faceRecognitionScreen);
            } else {
                showMemberIdMessage('Mã thành viên không hợp lệ. Vui lòng thử lại.', 'error');
                setTimeout(() => {
                    memberIdMessageDiv.textContent = '';
                    memberIdMessageDiv.className = 'message';
                }, 5000);
            }
        });
    }

    // Thêm chức năng nhấn Enter để kiểm tra mã thành viên
    if (memberIdInput) {
        memberIdInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                submitMemberIdButton.click();
            }
        });
    }

    // --- Logic cho màn hình Đăng ký Thành viên (placeholder) ---
    if (submitRegistrationButton) {
        submitRegistrationButton.addEventListener('click', () => {
            const name = regNameInput.value.trim();
            const email = regEmailInput.value.trim();
            const phone = regPhoneInput.value.trim();

            if (name === '' || email === '' || phone === '') {
                alert('Vui lòng điền đầy đủ thông tin để đăng ký!');
                return;
            }

            // TODO: Tại đây, bạn sẽ gửi dữ liệu đăng ký này tới backend
            console.log('Dữ liệu đăng ký:', { name, email, phone });
            alert(`Yêu cầu đăng ký của ${name} đã được gửi! (Chức năng này sẽ kết nối backend sau)`);
            showScreen(mainMenuScreen); // Quay về màn hình chính sau khi gửi
        });
    }


    // --- Khởi tạo: Mặc định hiển thị màn hình chính khi tải trang ---
    showScreen(mainMenuScreen);
});