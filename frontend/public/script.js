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
    const regNameInput = document.getElementById('regName');
    const regEmailInput = document.getElementById('regEmail');
    const regPhoneInput = document.getElementById('regPhone');
    const submitRegistrationButton = document.getElementById('submitRegistration');
    const regPhotoInput = document.getElementById('regPhotoInput'); // Input file cho ảnh đăng ký
    const registrationMessageDiv = document.createElement('div');
    registrationMessageDiv.className = 'message';
     if (submitRegistrationButton) {
        submitRegistrationButton.parentNode.insertBefore(registrationMessageDiv, submitRegistrationButton.nextSibling);
    }


    let mediaStream = null;

    // --- Cấu hình Backend API URL ---
    const BACKEND_API_URL = 'http://localhost:8000/machine';
    const RECOGNIZE_FACE_ENDPOINT = '/recognize_face';
    const CHECK_USER_ENDPOINT = '/users/'; // Endpoint kiểm tra user: /machine/users/{member_code}/check
    const USERS_IN_LIBRARY_ENDPOINT = '/attendance/in-library'; // Endpoint xem người dùng đang ở thư viện
    const REGISTRATION_ENDPOINT = '/registration-requests/'; // Endpoint đăng ký
    const CHECK_IN_ENDPOINT = '/attendance/check-in'; // Endpoint điểm danh vào (nếu cần gọi riêng)


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
        if (regPhotoInput) regPhotoInput.value = ''; // Xóa file đã chọn
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
             usersInLibraryListDiv.innerHTML = '<p>Đang tải danh sách...</p>'; // Reset placeholder
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
                showScreen(mainMenuScreen); // Quay về menu chính nếu lỗi webcam
            }
        } else {
            alert('Trình duyệt của bạn không hỗ trợ truy cập webcam.');
            showScreen(mainMenuScreen); // Quay về menu chính nếu không hỗ trợ
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
            const currentMemberId = displayMemberId.textContent; // Lấy mã thành viên từ phần tử hiển thị

            console.log('Đang gửi ảnh và mã thành viên đến Backend...');
            showRecognitionMessage('Đang xử lý nhận diện...', 'info'); // Hiển thị thông báo đang xử lý

            try {
                const formData = new FormData(); // Tạo đối tượng FormData
                const imageBlob = dataURLtoBlob(imageDataURL); // Chuyển Data URL sang Blob
                formData.append('file', imageBlob, 'webcam_image.jpeg'); // Thêm Blob vào FormData với tên trường 'file'
                formData.append('member_id', currentMemberId); // Thêm mã thành viên với tên trường 'member_id'

                const response = await fetch(`${BACKEND_API_URL}${RECOGNIZE_FACE_ENDPOINT}`, {
                    method: 'POST',
                    body: formData // Gửi FormData
                });

                if (!response.ok) {
                    const errorResult = await response.json();
                    console.error('Lỗi từ Backend:', response.status, errorResult);
                    showRecognitionMessage(`Lỗi từ Backend: ${response.status} - ${JSON.stringify(errorResult.detail || errorResult)}`, 'error');
                    // throw new Error(`Backend responded with status ${response.status}`); // Tạm bỏ throw để không crash
                } else {
                    const result = await response.json();
                    console.log('Phản hồi từ Backend:', result);
                     // Hiển thị thông báo thành công chung từ backend
                    showRecognitionMessage(`Thành công: ${result.message || JSON.stringify(result)}`, 'success');
                }


            } catch (error) {
                console.error('Lỗi khi gửi yêu cầu đến Backend:', error);
                if (!recognitionStatusMessageDiv.textContent.startsWith('Lỗi từ Backend:')) {
                     showRecognitionMessage('Đã xảy ra lỗi khi gửi yêu cầu.', 'error');
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
        goToViewMembersScreenButton.addEventListener('click', async () => { // Sử dụng async
            showScreen(viewMembersScreen);
            // showRecognitionMessage('Đang tải danh sách...', 'info'); // Sử dụng tạm recognition message div hoặc tạo div mới
            // Xóa nội dung cũ trước khi tải
            if (usersInLibraryListDiv) usersInLibraryListDiv.innerHTML = '<p>Đang tải danh sách...</p>'; // Hiển thị placeholder

            try {
                // Gọi Backend để tải danh sách thành viên đang ở thư viện
                console.log(`Đang gọi API: GET ${BACKEND_API_URL}${USERS_IN_LIBRARY_ENDPOINT}`);
                const response = await fetch(`${BACKEND_API_URL}${USERS_IN_LIBRARY_ENDPOINT}`);

                if (!response.ok) {
                    const errorResult = await response.json();
                     console.error('Lỗi khi tải danh sách:', response.status, errorResult);
                     if (usersInLibraryListDiv) usersInLibraryListDiv.innerHTML = `<p class="message error">Lỗi khi tải danh sách: ${response.status}</p>`;
                     // throw new Error(`Backend responded with status ${response.status}`); // Tạm bỏ throw
                     return; // Dừng lại nếu lỗi
                }

                const users = await response.json();
                console.log('Danh sách người dùng đang ở thư viện:', users);

                 // --- Hiển thị danh sách trên giao diện (vẫn giữ logic hiển thị) ---
                 if (usersInLibraryListDiv) {
                     if (users.length === 0) {
                          usersInLibraryListDiv.innerHTML = '<p>Không có người dùng nào đang ở thư viện.</p>';
                     } else {
                         let html = '<h3>Người dùng đang ở thư viện:</h3><ul>';
                         users.forEach(user => {
                             // Dựa vào cấu trúc UserInLibrary schema: session_id, member_code, full_name, entry_time
                             const entryTime = user.entry_time ? new Date(user.entry_time).toLocaleString() : 'N/A'; // Định dạng thời gian, kiểm tra null
                             html += `<li>Mã: ${user.member_code} - Tên: ${user.full_name} - Vào lúc: ${entryTime}</li>`;
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
        submitMemberIdButton.addEventListener('click', async () => { // Sử dụng async
            const memberId = memberIdInput.value.trim();

            if (memberId === '') {
                showMemberIdMessage('Vui lòng nhập mã thành viên.', 'error');
                return;
            }

            console.log('Đang kiểm tra mã thành viên:', memberId);
            showMemberIdMessage('Đang kiểm tra mã thành viên...', 'info'); // Hiển thị thông báo đang kiểm tra


            try {
                // Gọi Backend để kiểm tra mã thành viên
                 console.log(`Đang gọi API: GET ${BACKEND_API_URL}${CHECK_USER_ENDPOINT}${memberId}/check`);
                const response = await fetch(`${BACKEND_API_URL}${CHECK_USER_ENDPOINT}${memberId}/check`); // Sử dụng endpoint mới

                if (!response.ok) {
                    const errorResult = await response.json();
                    console.error('Lỗi khi kiểm tra mã thành viên:', response.status, errorResult);
                    showMemberIdMessage(`Lỗi: ${errorResult.detail || 'Mã thành viên không hợp lệ.'}`, 'error');
                    // throw new Error(`Backend responded with status ${response.status}`); // Tạm bỏ throw
                    return; // Dừng lại nếu lỗi
                }

                const user = await response.json();
                console.log('Mã thành viên hợp lệ:', user);

                // Nếu mã thành viên hợp lệ, chuyển sang màn hình nhận diện
                showMemberIdMessage(`Mã thành viên hợp lệ. Đang chuyển đến xác thực khuôn mặt...`, 'success');
                displayMemberId.textContent = memberId; // Hiển thị mã thành viên trên màn hình nhận diện
                // Chờ một chút trước khi chuyển màn hình để người dùng kịp đọc thông báo
                setTimeout(() => {
                    showScreen(faceRecognitionScreen);
                }, 1500); // Chờ 1.5 giây


            } catch (error) {
                console.error('Lỗi khi gửi yêu cầu kiểm tra mã thành viên:', error);
                showMemberIdMessage('Đã xảy ra lỗi khi kiểm lý mã thành viên.', 'error');
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
        submitRegistrationButton.addEventListener('click', async () => { // Sử dụng async
            const name = regNameInput.value.trim();
            const email = regEmailInput.value.trim();
            const phone = regPhoneInput.value.trim();
            // Lấy mã thành viên yêu cầu (nếu có trường nhập riêng)
            // const requestedMemberCode = document.getElementById('regMemberCodeInput').value.trim(); // Ví dụ

            // Lấy file ảnh từ input (nếu có input file)
            const photoInput = document.getElementById('regPhotoInput'); // Lấy input file element
            const photoFile = photoInput && photoInput.files && photoInput.files.length > 0 ? photoInput.files[0] : null; // Lấy File object đầu tiên


            // --- Kiểm tra dữ liệu (thêm kiểm tra mã thành viên yêu cầu và ảnh nếu cần) ---
            if (name === '' || email === '' || phone === '') {
                showRegistrationMessage('Vui lòng điền đầy đủ thông tin bắt buộc.', 'error');
                return;
            }
            // if (!requestedMemberCode) {
            //      showRegistrationMessage('Vui lòng nhập mã thành viên yêu cầu.', 'error');
            //      return;
            // }
            // Ảnh giờ là tùy chọn ở backend, nên không cần kiểm tra bắt buộc ở đây
            // if (!photoFile) {
            //      showRegistrationMessage('Vui lòng chọn ảnh để đăng ký.', 'error');
            //      return;
            // }


            console.log('Đang gửi yêu cầu đăng ký:', { name, email, phone, photo: photoFile ? photoFile.name : 'Không có ảnh' });
            showRegistrationMessage('Đang gửi yêu cầu đăng ký...', 'info'); // Hiển thị thông báo đang gửi

            try {
                const formData = new FormData(); // Tạo FormData

                // Thêm các trường dữ liệu vào FormData (tên trường phải khớp backend)
                // formData.append('requested_member_code', requestedMemberCode); // Thêm mã thành viên yêu cầu nếu có
                formData.append('full_name', name);
                formData.append('email', email);
                formData.append('phone_number', phone);

                // Thêm file ảnh vào FormData (nếu có input file và người dùng đã chọn)
                if (photoFile) {
                     formData.append('photo', photoFile, photoFile.name); // 'photo' là tên tham số trong backend
                }

                console.log(`Đang gọi API: POST ${BACKEND_API_URL}${REGISTRATION_ENDPOINT}`);
                const response = await fetch(`${BACKEND_API_URL}${REGISTRATION_ENDPOINT}`, {
                    method: 'POST',
                    body: formData // Gửi FormData
                });

                // Kiểm tra phản hồi
                if (!response.ok) {
                    const errorResult = await response.json();
                    console.error('Lỗi từ Backend khi đăng ký:', response.status, errorResult);
                    showRegistrationMessage(`Lỗi khi đăng ký: ${response.status} - ${JSON.stringify(errorResult.detail || errorResult)}`, 'error');
                    // throw new Error(`Backend responded with status ${response.status}`); // Tạm bỏ throw
                } else {
                    const result = await response.json();
                    console.log('Đăng ký thành công:', result);
                    showRegistrationMessage('Đăng ký thành công!', 'success'); // Hiển thị thông báo thành công

                    // Sau khi đăng ký thành công, có thể xóa form và chuyển về màn hình chính
                     regNameInput.value = '';
                     regEmailInput.value = '';
                     regPhoneInput.value = '';
                     if(regPhotoInput) regPhotoInput.value = ''; // Xóa file đã chọn
                    // setTimeout(() => {
                    //     showScreen(mainMenuScreen); // Tạm bỏ chuyển màn hình tự động
                    // }, 3000);
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
