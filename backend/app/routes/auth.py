from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pwdlib import PasswordHash
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import(
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse
)

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = PasswordHash.recommended()

@router.post("/register", response_model=RegisterResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.execute(
        text("""
            SELECT user_id
            FROM users
            WHERE email = :email 
            LIMIT 1 
        """),
        {"email": req.email}
    ).fetchone()

    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    user_id = str(uuid4())
    password_hash = pwd_context.hash(req.password)

    db.execute(
        text(
            """
            INSERT INTO users(
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
                "password_hash": password_hash,
            },
    )
    db.commit()

    return RegisterResponse(
        user_id=user_id,
        username=req.username,
        email=req.email
    )

@router.post("/login", response_model=LoginResponse)
def login(req:LoginRequest, db: Session = Depends(get_db)):
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
    
    user_id, username, email, password_hash = row

    if not password_hash or not pwd_context.verify(req.password, password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    return LoginResponse(
        user_id=str(user_id),
        username=username,
        email=email,
    )