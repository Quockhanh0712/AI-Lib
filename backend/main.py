# backend/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from db import database
from routers import user_endpoints, admin_endpoints
import os

app = FastAPI(
    title="AI Library System API",
    description="API cho hệ thống quản lý thư viện AI",
    version="1.0.0",
)

origins = [
    "http://localhost",
    "http://localhost:8082",
    "http://localhost:8083",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.environ.get("SESSION_SECRET_KEY", "your-super-secret-key-for-session-management-replace-this-in-production")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

@app.on_event("startup")
def on_startup():
    print("Creating database tables if they don't exist...")
    database.create_database_tables()
    print("Database tables checked/created successfully.")

# Đăng ký các router
app.include_router(user_endpoints.router, prefix="/machine", tags=["Machine/User Public"])
app.include_router(admin_endpoints.router, prefix="/admin", tags=["Admin"])

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Library Attendance System API (Simple Admin Auth)! Visit /docs."}