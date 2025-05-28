import cv2
import numpy as np
import tensorflow as tf
from deepface import DeepFace
from mtcnn import MTCNN
from fastapi import FastAPI, Depends, HTTPException, Form, File, UploadFile, status 
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from pydantic import BaseModel
from datetime import datetime
from collections import deque
import json
import base64
import math
import os
import uuid

# --- Cấu hình GPU TensorFlow ---
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        tf.config.set_visible_devices(gpus[0], 'GPU')
        print("GPU khả dụng")
    except RuntimeError as e:
        print(f"Lỗi GPU: {e}")
else:
    print("Không tìm thấy GPU, chạy trên CPU")

# --- Cấu hình cơ sở dữ liệu ---
DATABASE_URL = os.environ.get("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/default_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Mô hình SQLAlchemy ---
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    member_code = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    face_embeddings = relationship("FaceEmbedding", back_populates="user", uselist=False)
    attendance_sessions = relationship("AttendanceSession", back_populates="user")

class FaceEmbedding(Base):
    __tablename__ = 'face_embeddings'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    embedding = Column(Text)
    user = relationship("User", back_populates="face_embeddings")

class AttendanceSession(Base):
    __tablename__ = 'attendance_sessions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    entry_time = Column(TIMESTAMP, nullable=False)
    exit_time = Column(TIMESTAMP, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    user = relationship("User", back_populates="attendance_sessions")

Base.metadata.create_all(bind=engine)

# --- Pydantic Schema ---
class FrameRequest(BaseModel):
    frame: str

class ConfirmAttendanceRequest(BaseModel):
    member_code: str

class UpdateExitTimeRequest(BaseModel):
    member_code: str

class FaceRecognitionResponse(BaseModel):
    status: str
    full_name: str | None
    similarity: float | None
    distance: float | None
    final_frame: str | None

# --- Trạng thái toàn cục ---
frame_queue = deque(maxlen=5)
best_member_code = None
recognition_time = None
embedding_cache = None
cache_version = 0
detector = MTCNN()
UPLOAD_DIR = "uploaded_photos"
os.makedirs(UPLOAD_DIR, exist_ok=True)
# --- Ngưỡng cho nhận diện (SẼ ĐƯỢC CẬP NHẬT TỰ ĐỘNG KHI KHỞI ĐỘNG ỨNG DỤNG) ---
COSINE_SIMILARITY_THRESHOLD = 0.75
EUCLIDEAN_DISTANCE_THRESHOLD = 0.85

# --- Hàm tiền xử lý ảnh ---
def preprocess_image(img):
    try:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        faces = detector.detect_faces(img_rgb)
        if not faces:
            return None, None, "Không phát hiện khuôn mặt"
        if len(faces)>=2:
            return None, None, "Có nhiều khuôn mặt"
        # Luôn chọn khuôn mặt lớn nhất để đảm bảo chất lượng
        largest_face = max(faces, key=lambda f: f['box'][2] * f['box'][3])
        face = largest_face

        x, y, w, h = face['box']
        landmarks = face['keypoints']
        margin = int(max(w, h) * 0.1)
        x_m, y_m = max(0, x - margin), max(0, y - margin)
        w_m, h_m = w + 2 * margin, h + 2 * margin
        face_img = img[y_m:y_m + h_m, x_m:x_m + w_m]

        if face_img.size == 0:
            return None, None, "Vùng khuôn mặt không hợp lệ"

        left_eye = landmarks['left_eye']
        right_eye = landmarks['right_eye']
        dx = right_eye[0] - left_eye[0]
        dy = right_eye[1] - left_eye[1]

        if dx == 0:
            angle = 0
        else:
            angle = math.degrees(math.atan2(dy, dx))
            if angle > 90:
                angle -= 180
            elif angle < -90:
                angle += 180

        M = cv2.getRotationMatrix2D((w_m // 2, h_m // 2), angle, 1)
        aligned_img = cv2.warpAffine(face_img, M, (w_m, h_m))
        resized_img = cv2.resize(aligned_img, (224, 224), interpolation=cv2.INTER_AREA)

        gray_img = cv2.cvtColor(resized_img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        clahe_img = clahe.apply(gray_img)
        final_img = cv2.cvtColor(clahe_img, cv2.COLOR_GRAY2BGR)

        return final_img, {'x': x_m, 'y': y_m, 'w': w_m, 'h': h_m}, None
    except Exception as e:
        return None, None, f"Lỗi tiền xử lý: {str(e)}"

# --- Hàm tiện ích ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def extract_embedding(img):
    preprocessed_img, facial_area, error = preprocess_image(img)
    if error:
        tf.keras.backend.clear_session()
        return None, None, error
    try:
        result = DeepFace.represent(preprocessed_img, model_name="ArcFace", detector_backend="skip", enforce_detection=False)[0]
        tf.keras.backend.clear_session()
        embedding = np.array(result["embedding"])

        norm = np.linalg.norm(embedding)
        norm_embedding = embedding / norm if norm > 0 else embedding

        return norm_embedding, facial_area, None
    except Exception as e:
        tf.keras.backend.clear_session()
        return None, None, f"Lỗi trích xuất embedding (ArcFace): {str(e)}"

def load_embedding_cache(db: Session):
    global embedding_cache, cache_version
    users = db.query(User).all()
    user_embeddings = []
    for user in users:
        if user.face_embeddings and user.face_embeddings.embedding:
            try:
                embeddings = json.loads(user.face_embeddings.embedding)
                valid_embeddings = []
                for emb in embeddings:
                    if len(emb) > 0:
                        np_emb = np.array(emb)
                        norm = np.linalg.norm(np_emb)
                        valid_embeddings.append(np_emb / norm if norm > 0 else np_emb)

                if valid_embeddings:
                    user_embeddings.append({
                        "user_id": user.id,
                        "member_code": user.member_code,
                        "full_name": user.full_name,
                        "embeddings": valid_embeddings
                    })
            except json.JSONDecodeError:
                continue
    embedding_cache = user_embeddings
    cache_version += 1
    print(f"DEBUG: Cache đã được tải lại. Phiên bản mới: {cache_version}") # Debugging
    return embedding_cache

def cosine_similarity(input_embedding: np.ndarray, known_embeddings: np.ndarray) -> np.ndarray:
    if known_embeddings.ndim == 1:
        known_embeddings = known_embeddings[np.newaxis, :]
    input_norm = np.linalg.norm(input_embedding)
    known_norms = np.linalg.norm(known_embeddings, axis=1)
    safe_known_norms = np.where(known_norms == 0, 1e-10, known_norms)
    similarities = np.dot(known_embeddings, input_embedding) / (input_norm * safe_known_norms)
    return similarities

def euclidean_distance(input_embedding: np.ndarray, known_embeddings: np.ndarray) -> np.ndarray:
    if known_embeddings.ndim == 1:
        known_embeddings = known_embeddings[np.newaxis, :]
    distances = np.linalg.norm(known_embeddings - input_embedding, axis=1)
    return distances


def process_frame(frame_data: str, db: Session):
    global best_member_code, recognition_time, frame_queue, COSINE_SIMILARITY_THRESHOLD, EUCLIDEAN_DISTANCE_THRESHOLD
    try:
        img_data = base64.b64decode(frame_data.split(',')[1])
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        input_embedding, facial_area, error = extract_embedding(frame)
        if error:
            return {"status": error, "full_name": None, "similarity": None, "distance": None, "final_frame": None}

        # Đảm bảo cache được load hoặc re-load nếu cần
        global embedding_cache
        if embedding_cache is None:
            load_embedding_cache(db) # Force load if it's None (e.g., first run or explicitly set to None)
        user_embeddings = embedding_cache # Always use the global cache

        if not user_embeddings:
            return {"status": "Không có người dùng", "full_name": None, "similarity": None, "distance": None, "final_frame": None}

        matches = []
        for user in user_embeddings:
            if not user["embeddings"]:
                continue

            sims = cosine_similarity(input_embedding, np.array(user["embeddings"]))
            max_sim = np.max(sims) if len(sims) > 0 else 0

            dists = euclidean_distance(input_embedding, np.array(user["embeddings"]))
            min_dist = np.min(dists) if len(dists) > 0 else float('inf')

            if max_sim >= COSINE_SIMILARITY_THRESHOLD and min_dist <= EUCLIDEAN_DISTANCE_THRESHOLD:
                matches.append({"sim": max_sim, "dist": min_dist, "user": user})

        if not matches:
            frame_queue.clear()
            return {"status": "Không nhận diện được", "full_name": None, "similarity": None, "distance": None, "final_frame": None}

        best_match = sorted(matches, key=lambda x: (x["sim"], -x["dist"]), reverse=True)[0]

        frame_queue.append({
            "member_code": best_match["user"]["member_code"],
            "sim": best_match["sim"],
            "dist": best_match["dist"]
        })

        member_counts = {}
        for item in frame_queue:
            mc = item["member_code"]
            member_counts[mc] = member_counts.get(mc, 0) + 1

        for mc, count in member_counts.items():
            if count >= 4:
                recent_frames = list(frame_queue)[-3:]
                if all(f["member_code"] == mc for f in recent_frames):
                    best_member_code = mc
                    recognition_time = datetime.now()

                    if facial_area:
                        cv2.rectangle(frame, (facial_area['x'], facial_area['y']),
                                        (facial_area['x'] + facial_area['w'], facial_area['y'] + facial_area['h']),
                                        (0, 255, 0), 2)
                    _, buffer = cv2.imencode('.jpg', frame)
                    final_frame_b64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"

                    frame_queue.clear()

                    return {
                        "status": "Nhận diện thành công",
                        "full_name": best_match["user"]["full_name"],
                        "similarity": float(best_match["sim"]),
                        "distance": float(best_match["dist"]),
                        "final_frame": final_frame_b64
                    }
        return {"status": "Đang nhận diện", "full_name": None, "similarity": None, "distance": None, "final_frame": None}
    except Exception as e:
        tf.keras.backend.clear_session()
        return {"status": f"Lỗi: {str(e)}", "full_name": None, "similarity": None, "distance": None, "final_frame": None}

# --- FastAPI ---
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Khởi tạo cache khi ứng dụng khởi động
@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    try:
        global embedding_cache
        print("DEBUG: Khởi tạo cache khi ứng dụng bắt đầu...")
        embedding_cache = load_embedding_cache(db)
        print(f"DEBUG: Đã tải {len(embedding_cache)} embedding ban đầu khi khởi động.")
    finally:
        db.close()


@app.post('/process-frame', response_model=FaceRecognitionResponse)
async def process_frame_endpoint(req: FrameRequest, db: Session = Depends(get_db)):
    return process_frame(req.frame, db)

@app.post('/confirm-attendance')
async def confirm_attendance(req: ConfirmAttendanceRequest, db: Session = Depends(get_db)):
    global best_member_code, recognition_time
    if not recognition_time or not best_member_code:
        raise HTTPException(status_code=400, detail="Chưa nhận diện được khuôn mặt")
    if (datetime.now() - recognition_time).total_seconds() > 30:
        raise HTTPException(status_code=400, detail="Thời gian xác nhận hết hạn")
    if req.member_code != best_member_code:
        raise HTTPException(status_code=400, detail="Mã thành viên không khớp")

    user = db.query(User).filter(User.member_code == req.member_code).first()
    if not user:
        raise HTTPException(status_code=404, detail="Mã thành viên không tồn tại")

    existing_session = db.query(AttendanceSession).filter(
        AttendanceSession.user_id == user.id,
        AttendanceSession.exit_time == None
    ).first()
    if existing_session:
        raise HTTPException(status_code=400, detail="Người dùng chưa kết thúc phiên điểm danh trước đó")

    entry_time = recognition_time
    attendance_session = AttendanceSession(
        user_id=user.id,
        entry_time=entry_time,
        exit_time=None,
        duration_minutes=None
    )
    db.add(attendance_session)
    db.commit()

    frame_queue.clear()
    best_member_code = None
    recognition_time = None
    return {
        "status": "Đã ghi điểm danh",
        "full_name": user.full_name,
    }
@app.post('/update-exit-time')
async def update_exit_time(req: UpdateExitTimeRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.member_code == req.member_code).first()
    if not user:
        raise HTTPException(status_code=404, detail="Mã thành viên không tồn tại")

    session = db.query(AttendanceSession).filter(
        AttendanceSession.user_id == user.id,
        AttendanceSession.exit_time == None
    ).first()
    if not session:
        raise HTTPException(status_code=400, detail="Không có phiên điểm danh đang mở")

    session.exit_time = datetime.now()
    duration = (session.exit_time - session.entry_time).total_seconds() / 60
    session.duration_minutes = int(duration)
    db.commit()
    return {
        "status": "Đã cập nhật thời gian rời đi",
        "full_name": user.full_name,
        "exit_time": session.exit_time.isoformat(),
        "duration_minutes": session.duration_minutes
    }

@app.post('/add-face')
async def add_face(
    member_code: str = Form(...),
    webcam_frame: str = Form(None),
    files: list[UploadFile] = File([]),
    db: Session = Depends(get_db)
):
    global embedding_cache, cache_version # Giữ nguyên tên biến
    user = db.query(User).filter(User.member_code == member_code).first()
    if not user:
        raise HTTPException(status_code=404, detail="Mã thành viên không tồn tại")

    images = []
    if webcam_frame:
        try:
            img_data = base64.b64decode(webcam_frame.split(',')[1])
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            images.append(img)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Lỗi xử lý ảnh webcam: {str(e)}")

    if len(files) > 3:
        raise HTTPException(status_code=400, detail="Chỉ được tải lên tối đa 3 ảnh")
    for file in files:
        content = await file.read()
        nparr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        images.append(img)

    if not images:
        raise HTTPException(status_code=400, detail="Cần cung cấp ít nhất một ảnh")

    embeddings = []
    for img in images:
        embedding, _, error = extract_embedding(img)
        if error:
            raise HTTPException(status_code=400, detail=error)
        embeddings.append(embedding.tolist())

    existing_embedding = db.query(FaceEmbedding).filter(FaceEmbedding.user_id == user.id).first()
    if existing_embedding:
        current_embeddings = json.loads(existing_embedding.embedding)
        current_embeddings.extend(embeddings)
        existing_embedding.embedding = json.dumps(current_embeddings)
    else:
        face_embedding = FaceEmbedding(user_id=user.id, embedding=json.dumps(embeddings))
        db.add(face_embedding)
    db.commit()

    # >>> ĐIỀU CHỈNH CHÍNH Ở ĐÂY <<<
    # Sau khi database được cập nhật thành công, tải lại cache ngay lập tức.
    print("DEBUG: Database đã thay đổi. Đang tải lại embedding cache...")
    load_embedding_cache(db) # Gọi hàm tải lại cache
    # Không cần setting embedding_cache = None nữa vì load_embedding_cache đã ghi đè nó
    # và cũng không cần tăng cache_version ở đây vì load_embedding_cache đã làm việc đó.
    # >>> KẾT THÚC ĐIỀU CHỈNH <<<

    return {"status": "Đã lưu embedding", "full_name": user.full_name}

# Endpoint này sẽ được Backend Chính gọi để trích xuất embedding từ một ảnh duy nhất.
@app.post("/face-embeddings/extract")
async def extract_face_embedding_from_upload(
    image_file: UploadFile = File(...) # Nhận file ảnh từ request
):
    """
    Nhận một file ảnh, phát hiện/trích xuất khuôn mặt, tính toán embedding,
    và lưu ảnh vào thư mục UPLOAD_DIR.
    """
    if not image_file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tệp tải lên không phải là ảnh."
        )

    content = await image_file.read()
    nparr = np.frombuffer(content, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR) # Đọc ảnh ban đầu (BGR)

    if img_bgr is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể giải mã ảnh. Đảm bảo đây là tệp ảnh hợp lệ."
        )

    embedding_result_np, facial_area_info, error = extract_embedding(img_bgr)
    print(f"DEBUG AI: embedding_result_np after extract_embedding: {embedding_result_np}")
    if embedding_result_np is not None:
        print(f"DEBUG AI: type of embedding_result_np: {type(embedding_result_np)}")
        print(f"DEBUG AI: type of first element: {type(embedding_result_np[0]) if len(embedding_result_np) > 0 else 'N/A'}")

    if error:
        return {"embedding": None, "photo_path": None, "message": error}


    if embedding_result_np is None:
        return {"embedding": None, "photo_path": None, "message": "Không thể trích xuất embedding. Vui lòng kiểm tra lại ảnh."}


    unique_filename = f"{uuid.uuid4()}_{image_file.filename}"
    file_path_on_server = os.path.join(UPLOAD_DIR, unique_filename)
    cv2.imwrite(file_path_on_server, img_bgr)
    return {
        "embedding": embedding_result_np.tolist(),
        "photo_path": file_path_on_server,
        "message": "Khuôn mặt đã được xử lý và embedding trích xuất thành công."
    }


@app.post("/reload-embedding-cache")
async def reload_embedding_cache_endpoint(db: Session = Depends(get_db)):
    """
    Endpoint để kích hoạt việc tải lại toàn bộ embedding cache.
    Chỉ được gọi bởi Backend Admin sau khi DB đã được cập nhật.
    """
    print("DEBUG (AI Service): Nhận được yêu cầu tải lại embedding cache...")
    # Gọi hàm tải lại cache toàn cục
    load_embedding_cache(db) 
    print("DEBUG (AI Service): Đã tải lại embedding cache thành công.")
    return {"status": "success", "message": "Embedding cache reloaded."}
