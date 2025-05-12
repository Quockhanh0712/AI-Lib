import asyncio
import platform
import uuid
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool
import bcrypt
from jose import JWTError, jwt
from deepface import DeepFace
import numpy as np
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection pool configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Thay bằng username MySQL của bạn
    'password': '',  # Thay bằng password MySQL của bạn
    'database': 'library_db',
    'pool_name': 'library_pool',
    'pool_size': 5
}

# Initialize connection pool
db_pool = None

def get_db_connection():
    global db_pool
    try:
        if db_pool is None:
            db_pool = MySQLConnectionPool(**DB_CONFIG)
        return db_pool.get_connection()
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# JWT configuration
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic models
class User(BaseModel):
    student_id: str
    full_name: str
    email: str

class AdminLogin(BaseModel):
    username: str
    password: str

class Book(BaseModel):
    code: str
    title: str
    author: str
    description: Optional[str] = None
    publisher: Optional[str] = None
    published_year: Optional[int] = None
    available: bool = True

class BorrowRecord(BaseModel):
    user_id: int
    book_id: int
    borrow_date: datetime
    return_date: Optional[datetime]
    status: str

class CartItem(BaseModel):
    user_id: int
    book_id: int

# JWT functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Face recognition
async def verify_face(file: UploadFile):
    try:
        # Save uploaded file temporarily
        temp_path = f"temp_{uuid.uuid4()}.jpg"
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Get all users' face embeddings
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, student_id, face_embedding FROM users WHERE face_embedding IS NOT NULL")
        users = cursor.fetchall()
        cursor.close()
        connection.close()

        # Verify face against database
        for user in users:
            embedding = np.frombuffer(user['face_embedding'], dtype=np.float32)
            result = DeepFace.verify(temp_path, embedding, model_name="VGG-Face", enforce_detection=True)
            if result["verified"]:
                os.remove(temp_path)
                return user['id']
        
        os.remove(temp_path)
        raise HTTPException(status_code=401, detail="Face verification failed")
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Face verification error: {str(e)}")

# Authentication endpoints
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Check if user is admin
    cursor.execute("SELECT * FROM admins WHERE username = %s", (form_data.username,))
    admin = cursor.fetchone()
    
    if admin and bcrypt.checkpw(form_data.password.encode('utf-8'), admin['password'].encode('utf-8')):
        token = create_access_token({"sub": f"admin:{admin['id']}"})
        cursor.close()
        connection.close()
        return {"access_token": token, "token_type": "bearer", "role": "admin"}
    
    # Check if user is student
    cursor.execute("SELECT * FROM users WHERE student_id = %s", (form_data.username,))
    user = cursor.fetchone()
    
    cursor.close()
    connection.close()
    
    if user:
        token = create_access_token({"sub": f"user:{user['id']}"})
        return {"access_token": token, "token_type": "bearer", "role": "user"}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

# User endpoints
@app.post("/users")
async def create_user(user: User, file: UploadFile = File(...)):
    try:
        # Extract face embedding
        temp_path = f"temp_{uuid.uuid4()}.jpg"
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
        
        embedding = DeepFace.represent(temp_path, model_name="VGG-Face", enforce_detection=True)[0]["embedding"]
        embedding_bytes = np.array(embedding).tobytes()
        
        os.remove(temp_path)
        
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO users (student_id, full_name, email, face_embedding) VALUES (%s, %s, %s, %s)",
            (user.student_id, user.full_name, user.email, embedding_bytes)
        )
        connection.commit()
        cursor.close()
        connection.close()
        return {"message": "User created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@app.get("/users/me")
async def get_user_info(current_user: str = Depends(get_current_user)):
    user_id = current_user.split(":")[1]
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, student_id, full_name, email FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Book endpoints
@app.post("/books")
async def create_book(book: Book, current_user: str = Depends(get_current_user)):
    if not current_user.startswith("admin:"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO books (code, title, author, description, publisher, published_year, available) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (book.code, book.title, book.author, book.description, book.publisher, book.published_year, book.available)
    )
    connection.commit()
    cursor.close()
    connection.close()
    return {"message": "Book created successfully"}

@app.get("/books")
async def search_books(query: Optional[str] = None):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    if query:
        cursor.execute(
            "SELECT id, code, title, author, description, publisher, published_year, available, created_at "
            "FROM books WHERE title LIKE %s OR author LIKE %s OR code = %s",
            (f"%{query}%", f"%{query}%", query)
        )
    else:
        cursor.execute(
            "SELECT id, code, title, author, description, publisher, published_year, available, created_at FROM books"
        )
    
    books = cursor.fetchall()
    cursor.close()
    connection.close()
    return books

# Cart endpoints
@app.post("/cart")
async def add_to_cart(cart_item: CartItem, current_user: str = Depends(get_current_user)):
    user_id = current_user.split(":")[1]
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Check if book is available
    cursor.execute("SELECT available FROM books WHERE id = %s", (cart_item.book_id,))
    book = cursor.fetchone()
    if not book or not book[0]:
        cursor.close()
        connection.close()
        raise HTTPException(status_code=400, detail="Book not available")
    
    # Check if book is already in cart
    cursor.execute(
        "SELECT id FROM cart WHERE user_id = %s AND book_id = %s",
        (user_id, cart_item.book_id)
    )
    if cursor.fetchone():
        cursor.close()
        connection.close()
        raise HTTPException(status_code=400, detail="Book already in cart")
    
    cursor.execute(
        "INSERT INTO cart (user_id, book_id) VALUES (%s, %s)",
        (user_id, cart_item.book_id)
    )
    connection.commit()
    cursor.close()
    connection.close()
    return {"message": "Book added to cart"}

@app.get("/cart")
async def get_cart(current_user: str = Depends(get_current_user)):
    user_id = current_user.split(":")[1]
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT b.id, b.code, b.title, b.author, b.description, b.publisher, b.published_year, b.available "
        "FROM cart c JOIN books b ON c.book_id = b.id WHERE c.user_id = %s",
        (user_id,)
    )
    items = cursor.fetchall()
    cursor.close()
    connection.close()
    return items

# Borrow endpoints
@app.post("/borrow")
async def borrow_books(file: UploadFile = File(...), current_user: str = Depends(get_current_user)):
    user_id = await verify_face(file)
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Get cart items
    cursor.execute("SELECT book_id FROM cart WHERE user_id = %s", (user_id,))
    cart_items = cursor.fetchall()
    
    if not cart_items:
        cursor.close()
        connection.close()
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    try:
        unavailable_books = []
        for item in cart_items:
            # Check book availability
            cursor.execute("SELECT available FROM books WHERE id = %s", (item[0],))
            book = cursor.fetchone()
            if not book or not book[0]:
                unavailable_books.append(item[0])
                continue
                
            cursor.execute(
                "INSERT INTO borrow_records (user_id, book_id, borrow_date, status) VALUES (%s, %s, %s, %s)",
                (user_id, item[0], datetime.now(), "BORROWED")
            )
            cursor.execute("UPDATE books SET available = FALSE WHERE id = %s", (item[0],))
        
        # Clear cart
        cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        if unavailable_books:
            return {"message": f"Borrow successful, except for unavailable books: {unavailable_books}"}
        return {"message": "Borrow successful"}
    except Exception as e:
        connection.rollback()
        cursor.close()
        connection.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/return")
async def return_books(book_codes: List[str], current_user: str = Depends(get_current_user)):
    user_id = current_user.split(":")[1]
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        for code in book_codes:
            # Check if book exists and is borrowed by user
            cursor.execute(
                "SELECT br.id FROM borrow_records br JOIN books b ON br.book_id = b.id "
                "WHERE b.code = %s AND br.user_id = %s AND br.status = 'BORROWED'",
                (code, user_id)
            )
            record = cursor.fetchone()
            
            if not record:
                continue
                
            cursor.execute(
                "UPDATE borrow_records SET return_date = %s, status = 'RETURNED' WHERE id = %s",
                (datetime.now(), record[0])
            )
            cursor.execute("UPDATE books SET available = TRUE WHERE code = %s", (code,))
        
        connection.commit()
        cursor.close()
        connection.close()
        return {"message": "Books returned successfully"}
    except Exception as e:
        connection.rollback()
        cursor.close()
        connection.close()
        raise HTTPException(status_code=500, detail=str(e))

# Admin endpoints
@app.get("/borrow-records")
async def get_borrow_records(current_user: str = Depends(get_current_user)):
    if not current_user.startswith("admin:"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT br.id, br.user_id, br.book_id, br.borrow_date, br.return_date, br.status, "
        "u.student_id, u.full_name, b.title, b.code "
        "FROM borrow_records br "
        "JOIN users u ON br.user_id = u.id "
        "JOIN books b ON br.book_id = b.id"
    )
    records = cursor.fetchall()
    
    # Check for overdue records (assuming 14 days borrowing period)
    current_time = datetime.now()
    for record in records:
        if record['status'] == 'BORROWED' and (current_time - record['borrow_date']).days > 14:
            cursor.execute(
                "UPDATE borrow_records SET status = 'OVERDUE' WHERE id = %s",
                (record['id'],)
            )
            record['status'] = 'OVERDUE'
    
    connection.commit()
    cursor.close()
    connection.close()
    return records

# Database initialization
def init_db():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id VARCHAR(20) UNIQUE NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE,
            face_embedding BLOB,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INT AUTO_INCREMENT PRIMARY KEY,
            code VARCHAR(20) UNIQUE NOT NULL,
            title VARCHAR(200) NOT NULL,
            author VARCHAR(100),
            description TEXT,
            publisher VARCHAR(100),
            published_year YEAR,
            available BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS borrow_records (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            book_id INT,
            borrow_date DATETIME NOT NULL,
            return_date DATETIME,
            status ENUM('BORROWED', 'RETURNED', 'OVERDUE') DEFAULT 'BORROWED',
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            book_id INT,
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    """)
    
    # Create default admin
    hashed_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
    cursor.execute(
        "INSERT IGNORE INTO admins (username, password) VALUES (%s, %s)",
        ("admin", hashed_password)
    )
    
    connection.commit()
    cursor.close()
    connection.close()

@app.on_event("startup")
async def startup_event():
    init_db()

if platform.system() == "Emscripten":
    asyncio.ensure_future(startup_event())
else:
    if __name__ == "__main__":
        asyncio.run(startup_event())
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)