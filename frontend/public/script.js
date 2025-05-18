// frontend/public/script.js

document.addEventListener('DOMContentLoaded', () => {
    // --- Lấy các phần tử màn hình ---
    const mainMenuScreen = document.getElementById('mainMenuScreen');
    const memberIdInputScreen = document.getElementById('memberIdInputScreen');
    const faceRecognitionScreen = document.getElementById('faceRecognitionScreen');
    const viewMembersScreen = document.getElementById('viewMembersScreen');
    const registerMemberScreen = document.getElementById('registerMemberScreen');

    // --- Lấy các nút điều hướng trên màn hình chính ---
    const goToMemberIdInputButton = document.getElementById('goToMemberIdInput');
    const goToViewMembersScreenButton = document.getElementById('goToViewMembersScreen');
    const goToRegisterMemberScreenButton = document.getElementById('goToRegisterMemberScreen');

    // --- Lấy các nút "Quay lại" ---
    const backToMainFromMemberIdButton = document.getElementById('backToMainFromMemberId');
    const backToMemberIdInputButton = document.getElementById('backToMemberIdInput');
    const backToMainFromViewMembersButton = document.getElementById('backToMainFromViewMembers');
    const backToMainFromRegisterButton = document.getElementById('backToMainFromRegister');

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

    // --- Cấu hình Backend API URL ---
    // Khi chạy trong Docker Compose, frontend có thể truy cập backend bằng tên dịch vụ
    // và cổng mà backend lắng nghe bên trong container (thường là 8000 cho FastAPI)
    const BACKEND_API_URL = 'http://localhost:8000/machine';
    // Endpoint nhận diện khuôn mặt. Cần kiểm tra lại endpoint thực tế trong Backend của bạn (thư mục 'app')
    // Ví dụ: nếu endpoint là /api/v1/face/recognize, thì RECOGNIZE_FACE_ENDPOINT = '/api/v1/face/recognize';
    const RECOGNIZE_FACE_ENDPOINT = '/recognize_face'; // <-- Cần kiểm tra lại endpoint này trong Backend của bạn

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

    // --- Hàm chuyển đổi Data URL sang Blob ---
    function dataURLtoBlob(dataurl) {
        const arr = dataurl.split(',');
        const mime = arr[0].match(/:(.*?);/)[1];
        const bstr = atob(arr[1]);
        let n = bstr.length;
        const u8arr = new Uint8Array(n);
        while (n--) {
            u8arr[n] = bstr.charCodeAt(n);
        }
        return new Blob([u8arr], { type: mime });
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

            const imageDataURL = canvasForCapture.toDataURL('image/jpeg', 0.9); // Lấy ảnh dưới dạng Data URL
            const currentMemberId = displayMemberId.textContent;

            console.log('Đang gửi ảnh và mã thành viên đến Backend...');

            try {
                // Gửi yêu cầu đến Backend-DB (thư mục 'app')
                // Sử dụng FormData để gửi file và các trường form khác
                const formData = new FormData(); // 1. Tạo đối tượng FormData

                // 2. Chuyển Data URL sang Blob và thêm vào FormData
                const imageBlob = dataURLtoBlob(imageDataURL); // Chuyển Data URL sang Blob
                // Thêm Blob vào FormData với tên trường 'file' và tên file
                formData.append('file', imageBlob, 'webcam_image.jpeg'); // Tên trường phải là 'file', tên file tùy ý

                // Thêm mã thành viên với tên trường 'member_id'
                formData.append('member_id', currentMemberId); // Tên trường phải là 'member_id'

                const response = await fetch(`${BACKEND_API_URL}${RECOGNIZE_FACE_ENDPOINT}`, {
                    method: 'POST',
                    // 3. KHÔNG cần thiết lập Content-Type header một cách thủ công
                    // Khi gửi FormData, trình duyệt sẽ tự động thiết lập Content-Type là multipart/form-data
                    // headers: {
                    //     'Content-Type': 'application/json', // XÓA hoặc COMMENT dòng này
                    // },
                    body: formData // 4. Truyền đối tượng FormData vào body
                });

                // Kiểm tra xem phản hồi có thành công không (status code 2xx)
                if (!response.ok) {
                    // Nếu có lỗi từ backend (ví dụ: 400, 401, 404, 422, 500), ném lỗi để catch block xử lý
                    const errorResult = await response.json(); // Đọc phản hồi lỗi từ backend
                    console.error('Lỗi từ Backend:', response.status, errorResult);
                    // Ném một Exception để bắt ở khối catch
                    throw new Error(`Backend responded with status ${response.status}: ${JSON.stringify(errorResult)}`);
                }

                const result = await response.json(); // Phân tích phản hồi JSON từ backend
                console.log('Phản hồi từ Backend:', result);

                // --- Xử lý kết quả thành công ở đây ---
                // Dựa vào cấu trúc phản hồi từ backend (ví dụ: {"message": "...", "member_id": ...})
                // Cập nhật giao diện người dùng
                // Ví dụ: displayRecognitionResult(result);

            } catch (error) {
                console.error('Lỗi khi gửi yêu cầu đến Backend:', error);
                // --- Xử lý lỗi ở đây ---
                // Hiển thị thông báo lỗi cho người dùng trên giao diện
                // Ví dụ: displayErrorMessage('Đã xảy ra lỗi khi kết nối hoặc xử lý nhận diện.');
                // Nếu lỗi là do backend trả về HTTPException (ví dụ: 401, 404, 422),
                // thông tin chi tiết lỗi có thể nằm trong error.message (nếu bạn ném lỗi như ví dụ trên)
            }

        });
    }

    // --- Xử lý sự kiện nút bấm điều hướng ---

    if (goToMemberIdInputButton) {
        goToMemberIdInputButton.addEventListener('click', () => {
            showScreen(memberIdInputScreen);
            memberIdInput.focus();
        });
    }

    if (goToViewMembersScreenButton) {
        goToViewMembersScreenButton.addEventListener('click', () => {
            showScreen(viewMembersScreen);
            // TODO: Gọi Backend-DB để tải danh sách thành viên
            // Ví dụ: fetch(`${BACKEND_API_URL}/members_in_library`)
        });
    }

    if (goToRegisterMemberScreenButton) {
        goToRegisterMemberScreenButton.addEventListener('click', () => {
            showScreen(registerMemberScreen);
            regNameInput.focus();
        });
    }

    if (backToMainFromMemberIdButton) {
        backToMainFromMemberIdButton.addEventListener('click', () => {
            showScreen(mainMenuScreen);
        });
    }

    if (backToMemberIdInputButton) {
        backToMemberIdInputButton.addEventListener('click', () => {
            showScreen(memberIdInputScreen);
            memberIdInput.focus();
        });
    }

    if (backToMainFromViewMembersButton) {
        backToMainFromViewMembersButton.addEventListener('click', () => {
            showScreen(mainMenuScreen);
        });
    }

    if (backToMainFromRegisterButton) {
        backToMainFromRegisterButton.addEventListener('click', () => {
            showScreen(mainMenuScreen);
        });
    }

    // --- Logic cho màn hình Nhập Mã Thành viên ---

    if (submitMemberIdButton) {
        submitMemberIdButton.addEventListener('click', () => {
            const memberId = memberIdInput.value.trim();

            if (memberId === '') {
                showMemberIdMessage('Vui lòng nhập mã thành viên.', 'error');
                return;
            }

            console.log('Mã thành viên đã nhập:', memberId);

            // Lưu ý: Logic kiểm tra mã thành viên hợp lệ (ví dụ: 5 chữ số)
            // nên được thực hiện ở Backend để đảm bảo an toàn và nhất quán.
            // Phần kiểm tra ở frontend này chỉ mang tính tạm thời.

            // Giả lập kiểm tra ở frontend để chuyển màn hình nhanh
            if (memberId.length >= 1) { // Chỉ cần có nhập gì đó là chuyển màn hình
                 showMemberIdMessage('Đang chuyển đến xác thực khuôn mặt...', 'success');
                 displayMemberId.textContent = memberId;
                 showScreen(faceRecognitionScreen);
               } else {
                 showMemberIdMessage('Vui lòng nhập mã thành viên.', 'error');
                 setTimeout(() => {
                     memberIdMessageDiv.textContent = '';
                     memberIdMessageDiv.className = 'message';
                 }, 5000);
               }
        });
    }

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

            // TODO: Gửi dữ liệu đăng ký này tới backend-DB
            console.log('Dữ liệu đăng ký:', { name, email, phone });
            alert(`Yêu cầu đăng ký của ${name} đã được gửi! (Chức năng này sẽ kết nối backend-DB sau)`);
            showScreen(mainMenuScreen);
        });
    }


    // --- Khởi tạo: Mặc định hiển thị màn hình chính khi tải trang ---
    showScreen(mainMenuScreen);
});
