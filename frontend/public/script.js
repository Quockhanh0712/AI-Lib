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
    const recognitionStatusMessageDiv = document.getElementById('recognitionStatusMessage');


    // --- Lấy các phần tử của màn hình xem danh sách người dùng ---
    const usersInLibraryListDiv = document.getElementById('usersInLibraryList');


    // --- Lấy các phần tử của màn hình đăng ký thành viên ---
    const regMemberCodeInput = document.getElementById('regMemberCodeInput');
    const regNameInput = document.getElementById('regName');
    const regEmailInput = document.getElementById('regEmail');
    const regPhoneInput = document.getElementById('regPhone');
    const submitRegistrationButton = document.getElementById('submitRegistration');
    const regPhotoInput = document.getElementById('regPhotoInput');
    const registrationMessageDiv = document.createElement('div');
    registrationMessageDiv.className = 'message';
     if (submitRegistrationButton) {
        submitRegistrationButton.parentNode.insertBefore(registrationMessageDiv, submitRegistrationButton.nextSibling);
    }


    let mediaStream = null;

    // --- Cấu hình Backend API URL ---
    const BACKEND_API_URL = 'http://localhost:8000/machine';
    const RECOGNIZE_FACE_ENDPOINT = '/recognize_face';
    const CHECK_USER_ENDPOINT = '/users/';
    const USERS_IN_LIBRARY_ENDPOINT = '/attendance/in-library';
    const REGISTRATION_ENDPOINT = '/registration-requests/';
    const CHECK_IN_ENDPOINT = '/attendance/check-in';


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
        // Xóa input và thông báo trên màn hình đăng ký
        if (regMemberCodeInput) regMemberCodeInput.value = '';
        if (regNameInput) regNameInput.value = '';
        if (regEmailInput) regEmailInput.value = '';
        if (regPhoneInput) regPhoneInput.value = '';
        if (regPhotoInput) regPhotoInput.value = '';
        if (recognitionStatusMessageDiv) {
             recognitionStatusMessageDiv.textContent = '';
             recognitionStatusMessageDiv.className = 'message';
        }
         if (registrationMessageDiv) {
             registrationMessageDiv.textContent = '';
             registrationMessageDiv.className = 'message';
        }
        // Xóa nội dung danh sách người dùng khi chuyển màn hình khác
        if (usersInLibraryListDiv) {
             usersInLibraryListDiv.innerHTML = '<p>Đang tải danh sách...</p>';
        }
    }

    // --- Hàm để hiển thị thông báo trên màn hình nhập mã ---
    function showMemberIdMessage(msg, type) {
        if (memberIdMessageDiv) {
            memberIdMessageDiv.textContent = msg;
            memberIdMessageDiv.className = 'message ' + type;
        }
    }

    // --- Hàm để hiển thị thông báo trên màn hình nhận diện ---
    function showRecognitionMessage(msg, type) {
        if (recognitionStatusMessageDiv) {
            recognitionStatusMessageDiv.textContent = msg;
            recognitionStatusMessageDiv.className = 'message ' + type;
        }
    }

     // --- Hàm để hiển thị thông báo trên màn hình đăng ký ---
    function showRegistrationMessage(msg, type) {
        if (registrationMessageDiv) {
            registrationMessageDiv.textContent = msg;
            registrationMessageDiv.className = 'message ' + type;
        }
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
                showScreen(mainMenuScreen);
            }
        } else {
            alert('Trình duyệt của bạn không hỗ trợ truy cập webcam.');
            showScreen(mainMenuScreen);
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


    // --- Xử lý khi nhấn nút "Chụp ảnh" (gửi ảnh và member_id đến Backend) ---
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
            const currentMemberId = displayMemberId.textContent; // Lấy mã thành viên từ phần tử hiển thị

            if (!currentMemberId) {
                 showRecognitionMessage('Lỗi: Không có mã thành viên để xác minh.', 'error');
                 console.error('Member ID is missing on face recognition screen.');
                 return;
            }

            console.log('Đang gửi ảnh và mã thành viên đến Backend để xác minh...');
            showRecognitionMessage('Đang xử lý xác minh khuôn mặt...', 'info'); // Hiển thị thông báo đang xử lý

            try {
                const formData = new FormData();
                const imageBlob = dataURLtoBlob(imageDataURL);
                formData.append('file', imageBlob, 'webcam_image.jpeg');
                // Gửi member_id dưới dạng string
                formData.append('member_id', currentMemberId); // Gửi mã thành viên với tên trường 'member_id'

                console.log(`Đang gọi API: POST ${BACKEND_API_URL}${RECOGNIZE_FACE_ENDPOINT}`);
                const response = await fetch(`${BACKEND_API_URL}${RECOGNIZE_FACE_ENDPOINT}`, {
                    method: 'POST',
                    // 3. KHÔNG cần thiết lập Content-Type header một cách thủ công
                    // Khi gửi FormData, trình duyệt sẽ tự động thiết lập Content-Type là multipart/form-data
                    // headers: {
                    //     'Content-Type': 'application/json', // XÓA hoặc COMMENT dòng này
                    // },
                    body: formData // 4. Truyền đối tượng FormData vào body
                });

                // Phản hồi từ backend sẽ có cấu trúc { success: bool, message: str, user: {...} }
                const result = await response.json();
                console.log('Phản hồi từ Backend:', response.status, result);

                if (!response.ok) {
                    // Xử lý các mã lỗi HTTP khác ngoài 2xx
                    console.error('Lỗi HTTP từ Backend:', response.status, result);
                    showRecognitionMessage(`Lỗi HTTP: ${response.status} - ${result.detail || result.message || JSON.stringify(result)}`, 'error');
                } else {
                    // Xử lý phản hồi 2xx
                    if (result.success) {
                        // Xác minh thành công
                        const userName = result.user && result.user.full_name ? result.user.full_name : currentMemberId;
                        showRecognitionMessage(`Xác minh thành công! Chào mừng, ${userName}!`, 'success');
                        // TODO: Thêm logic tự động check-in user ở đây nếu cần
                        // Ví dụ: callCheckInApi(currentMemberId);
                    } else {
                        // Xác minh thất bại (backend trả về success: false)
                        showRecognitionMessage(`Xác minh thất bại: ${result.message || 'Khuôn mặt không khớp hoặc tài khoản không hợp lệ.'}`, 'error');
                    }
                }


            } catch (error) {
                console.error('Lỗi khi gửi yêu cầu đến Backend:', error);
                // Hiển thị thông báo lỗi chung nếu có lỗi mạng hoặc lỗi khác
                if (!recognitionStatusMessageDiv.textContent.startsWith('Lỗi từ Backend:')) {
                     showRecognitionMessage('Đã xảy ra lỗi khi gửi yêu cầu xác minh.', 'error');
                }
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
        goToViewMembersScreenButton.addEventListener('click', async () => {
            showScreen(viewMembersScreen);
            if (usersInLibraryListDiv) usersInLibraryListDiv.innerHTML = '<p>Đang tải danh sách...</p>';

            try {
                console.log(`Đang gọi API: GET ${BACKEND_API_URL}${USERS_IN_LIBRARY_ENDPOINT}`);
                const response = await fetch(`${BACKEND_API_URL}${USERS_IN_LIBRARY_ENDPOINT}`);

                const result = await response.json(); // Parse JSON dù thành công hay thất bại

                if (!response.ok) {
                     console.error('Lỗi khi tải danh sách:', response.status, result);
                     if (usersInLibraryListDiv) usersInLibraryListDiv.innerHTML = `<p class="message error">Lỗi khi tải danh sách: ${response.status} - ${result.detail || result.message || JSON.stringify(result)}</p>`;
                     return;
                }

                console.log('Danh sách người dùng đang ở thư viện:', result);

                 if (usersInLibraryListDiv) {
                     if (result.length === 0) { // Kiểm tra mảng rỗng
                          usersInLibraryListDiv.innerHTML = '<p>Không có người dùng nào đang ở thư viện.</p>';
                     } else {
                         let html = '<h3>Người dùng đang ở Thư viện:</h3><ul>';
                         result.forEach(item => { // result là mảng các UserInLibraryResponse
                             // Lấy thông tin Tên và Thời gian vào
                             const fullName = item.user_session_owner ? item.user_session_owner.full_name : 'N/A';
                             const entryTime = item.entry_time ? new Date(item.entry_time).toLocaleString() : 'N/A';

                             // SỬA ĐỔI: Bỏ phần hiển thị Mã thành viên
                             html += `<li>Tên: ${fullName} - Vào lúc: ${entryTime}</li>`;
                         });
                         html += '</ul>';
                         usersInLibraryListDiv.innerHTML = html;
                     }
                 }


            } catch (error) {
                console.error('Lỗi khi gửi yêu cầu tải danh sách:', error);
                if (usersInLibraryListDiv) usersInLibraryListDiv.innerHTML = `<p class="message error">Đã xảy ra lỗi khi gửi yêu cầu tải danh sách.</p>`;
            }

        });
    }

    if (goToRegisterMemberScreenButton) {
        goToRegisterMemberScreenButton.addEventListener('click', () => {
            showScreen(registerMemberScreen);
            if (regMemberCodeInput) regMemberCodeInput.focus();
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
        submitMemberIdButton.addEventListener('click', async () => {
            const memberId = memberIdInput.value.trim();

            if (memberId === '') {
                showMemberIdMessage('Vui lòng nhập mã thành viên.', 'error');
                return;
            }

            console.log('Đang kiểm tra mã thành viên:', memberId);
            showMemberIdMessage('Đang kiểm tra mã thành viên...', 'info');


            try {
                 console.log(`Đang gọi API: GET ${BACKEND_API_URL}${CHECK_USER_ENDPOINT}${memberId}/check`);
                const response = await fetch(`${BACKEND_API_URL}${CHECK_USER_ENDPOINT}${memberId}/check`);

                const result = await response.json(); // Parse JSON dù thành công hay thất bại

                if (!response.ok) {
                    console.error('Lỗi khi kiểm tra mã thành viên:', response.status, result);
                    showMemberIdMessage(`Lỗi: ${result.detail || result.message || 'Mã thành viên không hợp lệ.'}`, 'error');
                    return;
                }

                console.log('Mã thành viên hợp lệ:', result); // result là thông tin user nếu thành công

                // Nếu mã thành viên hợp lệ, chuyển sang màn hình nhận diện
                const userName = result.full_name || memberId; // Lấy tên nếu có, không thì dùng mã
                showMemberIdMessage(`Mã thành viên hợp lệ. Chào mừng ${userName}! Đang chuyển đến xác thực khuôn mặt...`, 'success');
                displayMemberId.textContent = memberId; // Hiển thị mã thành viên trên màn hình nhận diện
                setTimeout(() => {
                    showScreen(faceRecognitionScreen);
                }, 1500);


            } catch (error) {
                console.error('Lỗi khi gửi yêu cầu kiểm tra mã thành viên:', error);
                showMemberIdMessage('Đã xảy ra lỗi khi kiểm tra mã thành viên.', 'error');
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

    // --- Logic cho màn hình Đăng ký Thành viên ---
    if (submitRegistrationButton) {
        submitRegistrationButton.addEventListener('click', async () => {
            const requestedMemberCode = regMemberCodeInput ? regMemberCodeInput.value.trim() : '';
            const name = regNameInput.value.trim();
            const email = regEmailInput.value.trim();
            const phone = regPhoneInput.value.trim();

            const photoInput = document.getElementById('regPhotoInput');
            const photoFile = photoInput && photoInput.files && photoInput.files.length > 0 ? photoInput.files[0] : null;


            if (requestedMemberCode === '') {
                 showRegistrationMessage('Vui lòng nhập mã thành viên yêu cầu.', 'error');
                 return;
            }
            if (name === '' || email === '' || phone === '') {
                showRegistrationMessage('Vui lòng điền đầy đủ thông tin bắt buộc.', 'error');
                return;
            }


            console.log('Đang gửi yêu cầu đăng ký:', { requestedMemberCode, name, email, phone, photo: photoFile ? photoFile.name : 'Không có ảnh' });
            showRegistrationMessage('Đang gửi yêu cầu đăng ký...', 'info');

            try {
                const formData = new FormData();
                formData.append('requested_member_code', requestedMemberCode);
                formData.append('full_name', name);
                formData.append('email', email);
                formData.append('phone_number', phone);

                if (photoFile) {
                     formData.append('photo', photoFile, photoFile.name);
                }

                console.log(`Đang gọi API: POST ${BACKEND_API_URL}${REGISTRATION_ENDPOINT}`);
                const response = await fetch(`${BACKEND_API_URL}${REGISTRATION_ENDPOINT}`, {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (!response.ok) {
                    console.error('Lỗi từ Backend khi đăng ký:', response.status, result);
                    showRegistrationMessage(`Lỗi khi đăng ký: ${response.status} - ${result.detail || result.message || JSON.stringify(result)}`, 'error');
                } else {
                    console.log('Đăng ký thành công:', result);
                    showRegistrationMessage('Đăng ký thành công!', 'success');

                     if (regMemberCodeInput) regMemberCodeInput.value = '';
                     regNameInput.value = '';
                     regEmailInput.value = '';
                     regPhoneInput.value = '';
                     if(regPhotoInput) regPhotoInput.value = '';
                }


            } catch (error) {
                console.error('Lỗi khi gửi yêu cầu đăng ký:', error);
                 if (!registrationMessageDiv.textContent.startsWith('Lỗi khi đăng ký:')) {
                     showRegistrationMessage('Đã xảy ra lỗi khi gửi yêu cầu đăng ký.', 'error');
                 }
            }
        });
    }


    // --- Khởi tạo: Mặc định hiển thị màn hình chính khi tải trang ---
    showScreen(mainMenuScreen);
});
