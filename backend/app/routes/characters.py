from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import CharacterCreateRequest, CharacterCreateResponse
from app.security import get_current_user

router = APIRouter(prefix="/characters", tags=["characters"])


@router.post("", response_model=CharacterCreateResponse)
def create_character(
    req: CharacterCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if req.character_image_id is not None:
        image_exists = db.execute(
            text("""
                SELECT image_id
                FROM images
                WHERE image_id = :image_id
                LIMIT 1
            """),
            {"image_id": str(req.character_image_id)},
        ).fetchone()

        if not image_exists:
            raise HTTPException(status_code=404, detail="Image not found")

    character_id = str(uuid4())

    db.execute(
        text("""
            INSERT INTO characters (
                character_id,
                creator_user_id,
                character_name,
                character_personality,
                character_intro,
                character_call_user,
                chat_style,
                hidden_story,
                opening_remark,
                character_image_id,
                is_public,
                created_at,
                updated_at
            )
            VALUES (
                :character_id,
                :creator_user_id,
                :character_name,
                :character_personality,
                :character_intro,
                :character_call_user,
                :chat_style,
                :hidden_story,
                :opening_remark,
                :character_image_id,
                :is_public,
                NOW(),
                NOW()
            )
        """),
        {
            "character_id": character_id,
            "creator_user_id": current_user["user_id"],
            "character_name": req.character_name,
            "character_personality": req.character_personality,
            "character_intro": req.character_intro,
            "character_call_user": req.character_call_user,
            "chat_style": req.chat_style,
            "hidden_story": req.hidden_story,
            "opening_remark": req.opening_remark,
            "character_image_id": str(req.character_image_id) if req.character_image_id else None,
            "is_public": req.is_public,
        },
    )

    db.commit()

    print("create_character reached return") 
    
    return CharacterCreateResponse(
        character_id=character_id,
        character_name=req.character_name,
        creator_user_id=current_user["user_id"],
        opening_remark=req.opening_remark,
    )