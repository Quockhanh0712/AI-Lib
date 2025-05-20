# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware # Correct import
from app.db import database, models
from app.routers import user_endpoints, admin_endpoints
from app.core.config import settings

# Initialize database tables
try:
    models.Base.metadata.create_all(bind=database.engine)
    print("Database tables checked/created successfully.")
except Exception as e:
    print(f"Error creating database tables: {e}")

app = FastAPI(
    title="Library Attendance System API (Session Auth)",
    description="API for managing library attendance with session-based admin authentication.",
    version="0.1.1"
)

# --- CORS MIDDLEWARE CONFIGURATION ---
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # "http://localhost:3000", # Uncomment if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- END CORS MIDDLEWARE CONFIGURATION ---


# --- SESSION MIDDLEWARE CONFIGURATION ---
print(f"--- Using SECRET_KEY for SessionMiddleware: '{settings.SECRET_KEY}' ---")
if not settings.SECRET_KEY:
    raise ValueError("FATAL: SECRET_KEY is not configured for SessionMiddleware!")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="library_attendance_session", # Custom cookie name
    max_age=14 * 24 * 60 * 60,                  # 14 days session lifetime
    # secure=True, # For HTTPS only in production - default is False
    # The following are defaults and don't need to be explicitly set unless changing them:
    # path="/",
    # domain=None,
    # httponly=True, # <<< Default is True
    # samesite="lax" # <<< Default is "lax"
)
# --- END SESSION MIDDLEWARE ---

# Include API routers
app.include_router(user_endpoints.router)
app.include_router(admin_endpoints.router)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Library Attendance System API! Visit /docs or /redoc for API documentation."}