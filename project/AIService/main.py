# AIService/main.py
import os
from dotenv import load_dotenv

load_dotenv() # Load .env variables at the very start

import cv2
import numpy as np
# import tensorflow as tf # Often implicitly imported by deepface or tf_keras
from deepface import DeepFace
from mtcnn import MTCNN # For face detection
from fastapi import FastAPI, Depends, HTTPException, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session as DbSessionType
from pydantic import BaseModel
from datetime import datetime
# from collections import deque # Not currently used in the /add-face endpoint
import json
# import base64 # Not directly used here, handled by file upload processing
# import math # Not directly used in simplified preprocess

from typing import Optional, List # <<< IMPORTED Optional and List

# --- Database Configuration ---
DATABASE_URL = os.getenv("AI_DATABASE_URL", 'mysql+pymysql://root:your_db_password_fallback@localhost:3306/lib_ai_fallback')
print(f"--- [AI Service] Attempting to use DATABASE_URL: {DATABASE_URL} ---")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- SQLAlchemy Models ---
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    member_code = Column(String(50), unique=True, nullable=False, index=True)
    # If AI service needs full_name for responses, ensure it's in this model and 'users' table
    # full_name = Column(String(255), nullable=True)
    face_embeddings = relationship("FaceEmbedding", back_populates="user_owner")

class FaceEmbedding(Base):
    __tablename__ = 'face_embeddings'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    embedding_vector = Column(Text, nullable=False) # Storing JSON string of embedding list
    created_at = Column(TIMESTAMP, server_default=func.now())
    user_owner = relationship("User", back_populates="face_embeddings")

try:
    Base.metadata.create_all(bind=engine)
    print("[AI Service] Database tables checked/created successfully.")
except Exception as e:
    print(f"[AI Service] Error creating database tables: {e}")
    # Consider how to handle this - if DB is essential, app might not be useful
    # raise e # Optionally re-raise to stop startup

# --- Pydantic Schemas ---
class AddFaceResponse(BaseModel):
    status: str
    message: Optional[str] = None
    embeddings_count: Optional[int] = None

# --- Global Variables & Face Processing ---
try:
    print("[AI Service] Initializing MTCNN detector...")
    detector = MTCNN()
    print("[AI Service] MTCNN detector initialized.")
except Exception as e:
    print(f"[AI Service] Error initializing MTCNN detector: {e}")
    detector = None # Allow app to start but face detection will fail

# Placeholder for the complex preprocess_image from the PDF
# For now, this simplified version relies more on DeepFace's internal capabilities
def preprocess_image(img_array: np.ndarray):
    print("[AI Service] Preprocessing image...")
    if detector is None:
        return None, "MTCNN Detector not initialized."
    if img_array is None or img_array.size == 0:
        return None, "Invalid image data (empty)."
    try:
        # DeepFace.extract_faces can perform detection and alignment
        # The 'img_path' can be a numpy array.
        # Using a more robust detection backend if available and if MTCNN from global isn't used by it directly.
        # detector_backend='mtcnn' here will use the MTCNN library.
        # If you want to use the global 'detector', you might need to pass the detected faces to DeepFace.represent
        # with detector_backend='skip'.
        # For simplicity now, let DeepFace handle detection if it can find a face.
        faces = DeepFace.extract_faces(
            img_path=img_array,
            detector_backend='mtcnn', # Uses the MTCNN library
            enforce_detection=True,   # Raise error if no face found
            align=True                # Align faces
        )
        if not faces or len(faces) == 0:
            return None, "No face detected by DeepFace.extract_faces."
        
        # DeepFace.extract_faces returns a list of dicts, each with 'face' (numpy array of detected face)
        # We'll use the first detected face.
        processed_face_array = faces[0]['face']
        # DeepFace returns face already in BGR and normalized (0-1 range for some models)
        # and typically resized. The PDF had custom resizing and CLAHE.
        # For now, we pass what DeepFace.extract_faces gives.
        return processed_face_array, None
    except ValueError as ve: # Often "Face could not be detected." from DeepFace
        print(f"[AI Service] Preprocessing ValueError (likely no face detected): {str(ve)}")
        return None, str(ve)
    except Exception as e:
        print(f"[AI Service] Error in preprocessing/face extraction: {str(e)}")
        return None, f"Error in preprocessing: {str(e)}"

def extract_embedding(preprocessed_face_array: np.ndarray):
    print("[AI Service] Extracting embedding from preprocessed face...")
    if preprocessed_face_array is None:
        return None, "Cannot extract embedding from None image."
    try:
        # Now that the face is already detected and extracted by preprocess_image,
        # we tell DeepFace.represent to skip detection.
        embedding_objs = DeepFace.represent(
            img_path=preprocessed_face_array, # This is the cropped/aligned face
            model_name="Facenet",    # Or "VGG-Face", "ArcFace" etc.
            enforce_detection=False, # We've already detected/extracted the face
            detector_backend='skip'  # Don't re-run detection
        )
        if not embedding_objs or len(embedding_objs) == 0:
            return None, "Could not generate embedding (DeepFace.represent returned empty)."
        
        embedding_vector = embedding_objs[0]["embedding"]
        return np.array(embedding_vector), None
    except Exception as e:
        print(f"[AI Service] DeepFace.represent error: {str(e)}")
        return None, f"Lỗi trích xuất embedding: {str(e)}"

# --- FastAPI App Instance (for AI Service) ---
ai_app = FastAPI(title="AI Face Recognition Service")

# CORS Middleware for AI Service
ai_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000", # Admin Backend
        "http://127.0.0.1:8000",
        "http://localhost:5173", # Frontend (if it ever calls AI service directly)
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency for DB Session
def get_ai_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@ai_app.post('/add-face', response_model=AddFaceResponse)
async def add_face_endpoint(
    member_code: str = Form(...),
    files: List[UploadFile] = File(...), # <<< Ensure this is List[UploadFile]
    db: DbSessionType = Depends(get_ai_db)
):
    # Correctly get the number of files received. 'files' is now a List.
    num_files_received = len(files) if files else 0
    print(f"[AI Service] Received /add-face request for member_code: {member_code} with {num_files_received} file(s).")

    user = db.query(User).filter(User.member_code == member_code).first()
    if not user:
        print(f"[AI Service] User not found for member_code: {member_code}")
        raise HTTPException(status_code=404, detail=f"Mã thành viên {member_code} không tồn tại trong AI DB.")

    if not files or num_files_received == 0: # Check if the list is empty or None
        raise HTTPException(status_code=400, detail="Cần cung cấp ít nhất một ảnh.")
    
    # The limit check should be based on the number of files received.
    # The PDF/previous setup suggested a max of 3.
    if num_files_received > 3:
        raise HTTPException(status_code=400, detail="Chỉ được tải lên tối đa 3 ảnh.")

    saved_embeddings_count = 0
    all_errors_for_files = []

    # 'files' is now definitely a list, so we can iterate through it
    for uploaded_file in files:
        try:
            contents = await uploaded_file.read()
            nparr = np.frombuffer(contents, np.uint8)
            img_array_original = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img_array_original is None:
                msg = f"Could not decode image: {uploaded_file.filename}"
                print(f"[AI Service] {msg}")
                all_errors_for_files.append(msg)
                continue

            face_img_array, preproc_error = preprocess_image(img_array_original)
            if preproc_error:
                msg = f"Error preprocessing {uploaded_file.filename}: {preproc_error}"
                print(f"[AI Service] {msg}")
                all_errors_for_files.append(msg)
                continue
            
            embedding_vector, extract_error = extract_embedding(face_img_array)
            if extract_error:
                msg = f"Error extracting embedding for {uploaded_file.filename}: {extract_error}"
                print(f"[AI Service] {msg}")
                all_errors_for_files.append(msg)
                continue

            embedding_json = json.dumps(embedding_vector.tolist())
            db_embedding = FaceEmbedding(user_id=user.id, embedding_vector=embedding_json)
            db.add(db_embedding)
            saved_embeddings_count += 1
            print(f"[AI Service] Embedding extracted and staged for save for {uploaded_file.filename}")

        except Exception as e:
            msg = f"General error processing file {uploaded_file.filename}: {str(e)}"
            print(f"[AI Service] {msg}")
            all_errors_for_files.append(msg)
            continue
        finally:
            if uploaded_file: # Ensure uploaded_file is not None before calling close
                await uploaded_file.close()
    
    if saved_embeddings_count > 0:
        db.commit()
        final_message = f"Đã lưu {saved_embeddings_count} embedding(s)."
        if all_errors_for_files:
            final_message += f" Errors encountered with other files: {'; '.join(all_errors_for_files)}"
        print(f"[AI Service] Successfully saved {saved_embeddings_count} embeddings for user {user.member_code}")
        return AddFaceResponse(status="success", message=final_message, embeddings_count=saved_embeddings_count)
    else:
        error_detail = "Không thể xử lý hoặc trích xuất embedding từ bất kỳ ảnh nào được cung cấp."
        if all_errors_for_files:
            error_detail += f" Details: {'; '.join(all_errors_for_files)}"
        print(f"[AI Service] No embeddings were successfully processed for user {user.member_code}")
        raise HTTPException(status_code=400, detail=error_detail)
# You can add other AI endpoints from the "code" PDF here as needed
# (e.g., /process-frame, /confirm-attendance, /add-user (for AI DB user))

print("[AI Service] Main script fully loaded. Uvicorn will start the FastAPI app 'ai_app'.")