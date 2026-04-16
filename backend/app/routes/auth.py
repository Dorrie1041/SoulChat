from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from pwdlib import PasswordHash

from app.db import get_db
from app.schemas import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
)
from app.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

password_hasher = PasswordHash.recommended()


@router.post("/register", response_model=RegisterResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.execute(
        text("""
            SELECT user_id
            FROM users
            WHERE email = :email
            LIMIT 1
        """),
        {"email": req.email},
    ).fetchone()

    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    user_id = str(uuid4())
    hashed_password = password_hasher.hash(req.password)

    db.execute(
        text("""
            INSERT INTO users (
                user_id,
                username,
                email,
                password_hash,
                role,
                persona_preference,
                created_at,
                updated_at
            )
            VALUES (
                :user_id,
                :username,
                :email,
                :password_hash,
                'user',
                NULL,
                NOW(),
                NOW()
            )
        """),
        {
            "user_id": user_id,
            "username": req.username,
            "email": req.email,
            "password_hash": hashed_password,
        },
    )
    db.commit()

    return RegisterResponse(
        user_id=user_id,
        username=req.username,
        email=req.email,
    )


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    row = db.execute(
        text("""
            SELECT user_id, username, email, password_hash
            FROM users
            WHERE email = :email
            LIMIT 1
        """),
        {"email": req.email},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id, username, email, stored_hash = row

    if not stored_hash or not password_hasher.verify(req.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(str(user_id))

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=str(user_id),
        username=username,
        email=email,
    )