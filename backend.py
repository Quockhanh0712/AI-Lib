import os
import cv2
import streamlit as st
from deepface import DeepFace
from PIL import Image
import numpy as np

# Đường dẫn đến thư mục lưu ảnh gốc
FACE_DB_PATH = "faces"
os.makedirs(FACE_DB_PATH, exist_ok=True)

st.title("🔍 Hệ thống Nhận diện Khuôn mặt với DeepFace")

# Tải ảnh gốc từ thư mục
def load_face_db():
    return [os.path.join(FACE_DB_PATH, img) for img in os.listdir(FACE_DB_PATH) if img.endswith((".jpg", ".png"))]

# Hàm nhận diện khuôn mặt
def recognize_face(input_img_path):
    try:
        result = DeepFace.find(img_path=input_img_path, db_path=FACE_DB_PATH, enforce_detection=False)
        if result[0].shape[0] > 0:
            matched = os.path.basename(result[0].iloc[0]['identity'])
            return f"✅ Nhận diện: {matched}"
        else:
            return "❌ Không nhận diện được khuôn mặt trùng khớp."
    except Exception as e:
        return f"Lỗi: {e}"

# Giao diện
option = st.sidebar.selectbox("Chọn chức năng", ["📷 Nhận diện từ ảnh", "🎥 Nhận diện từ webcam", "➕ Thêm người mới"])

if option == "📷 Nhận diện từ ảnh":
    uploaded_file = st.file_uploader("Tải ảnh khuôn mặt lên", type=["jpg", "png"])
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        st.image(img, caption="Ảnh đã tải lên", use_column_width=True)
        img_path = f"temp.jpg"
        img.save(img_path)
        result = recognize_face(img_path)
        st.success(result)

elif option == "🎥 Nhận diện từ webcam":
    st.warning("⏳ Đang mở webcam. Nhấn 'q' trong cửa sổ camera để thoát.")
    if st.button("Bắt đầu webcam"):
        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow("Nhấn 'q' để thoát", frame)
            img_path = "temp_frame.jpg"
            cv2.imwrite(img_path, frame)
            result = recognize_face(img_path)
            cv2.putText(frame, result, (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
            cv2.imshow("Camera", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

elif option == "➕ Thêm người mới":
    name = st.text_input("Nhập tên người (không dấu, không khoảng trắng)")
    file = st.file_uploader("Tải ảnh khuôn mặt lên", type=["jpg", "png"])
    if name and file:
        save_path = os.path.join(FACE_DB_PATH, f"{name}.jpg")
        with open(save_path, "wb") as f:
            f.write(file.getbuffer())
        st.success(f"Đã thêm {name} vào cơ sở dữ liệu khuôn mặt.")
