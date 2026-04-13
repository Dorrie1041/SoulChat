from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import CharacterCreateRequest, CharacterCreateResponse

router = APIRouter(prefix="/characters", tags=["characters"])

@router.post("", response_model=CharacterCreateResponse)
def create_character(req: CharacterCreateRequest, db: Session=Depends(get_db)):
    user_exists = db.execute(
        text("""
            SELECT user_id
            FROM users
            WHERE user_id = :user_id  
            """),
            {"user_id": str(req.creator_user_id)},
    ).fetchone()

    if not user_exists:
        raise HTTPException(status_code=404, detail="Creator user not found")
    
    if req.character_image_id is not None:
        image_exists = db.execute(
            text("""
                SELECT image_id
                FROM images
                WHERE image_id = :image_id
                LIMIT 1   
            """),
            {"image_id": str(req.character_image_id)}
        ).fetchone()

        if not image_exists:
            raise HTTPException(status_code=404, detail="Image not found")
        
        character_id = str(uuid4)

        db.execute(
            text("""
                INSERT INTO characters(
                    character_id,
                    creator_user_id,
                    character_name,
                    character_personality,
                    character_intro,
                    character_call_user,
                    chat_style,
                    hidden_story,
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
                    :character_image_id,
                    :is_public,
                    NOW(),
                    NOW()
                 ) 
            """),
            {
                "character_id": character_id,
                "creator_user_id": str(req.creator_user_id),
                "character_name": req.character_name,
                "character_personality": req.character_personality,
                "character_intro": req.character_intro,
                "character_call_user": req.character_call_user,
                "chat_style": req.chat_style,
                "hidden_story": req.hidden_story,
                "character_image_id": req.character_image_id,
                "is_public": req.is_public
            },
        )

        db.commit()

        return CharacterCreateResponse(
            character_id=character_id,
            character_name=req.character_name,
            creator_user_id=str(req.creator_user_id),
        )
    