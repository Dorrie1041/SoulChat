from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas import MeResponse
from app.db import get_db
from app.security import get_current_user

router = APIRouter(tags=["users"])

@router.get("/me", response_model=MeResponse)
def get_me(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    row = db.execute(
        text("""
            SELECT 
                user_id,
                username,
                email,
                role,
                persona_preference,
                created_at
            FROM users
            WHERE user_id = :user_id
            LIMIT 1  
        """),
        {"user_id": current_user["user_id"]},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Not found user")
    
    return MeResponse(
        user_id=str(row[1]),
        username=row[1],
        email=row[2],
        role=row[3],
        persona_preference=row[4],
        created_at=str(row[5]) if row[5] else None
    )
