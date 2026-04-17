from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import CharacterCreateRequest, CharacterCreateResponse, CharacterItemResponse, CharacterDetailResponse
from app.security import get_current_user
from typing import List

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

@router.get("", response_model=List[CharacterItemResponse])
def list_characters(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    rows = db.execute(
        text("""
            SELECT 
                character_id,
                character_name,
                character_personality,
                character_intro,
                character_call_user,
                chat_style,
                hidden_story,
                opening_remark,
                character_image_id,
                is_public,
                creator_user_id
             FROM characters
             WHERE creator_user_id = :user_id 
             OR is_public = TRUE
             ORDER BY created_at DESC
        """),
        {"user_id": current_user["user_id"]},
    ).fetchall()

    results = []
    for row in rows:
        results.append(
            CharacterItemResponse(
                character_id=str(row[0]),
                character_name=row[1],
                character_personality=row[2],
                character_intro=row[3],
                character_call_user=row[4],
                chat_style=row[5],
                hidden_story=row[6],
                opening_remark=row[7],
                character_image_id=str(row[8]) if row[8] else None,
                is_public=row[9],
                creator_user_id=str(row[10]),
            )
        )
    
    return results

@router.get("/{character_id}", response_model=CharacterDetailResponse)
def get_character_detail(
    character_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    row = db.execute(
        text("""
            SELECT
                character_id,
                character_name,
                character_personality,
                character_intro,
                character_call_user,
                chat_style,
                hidden_story,
                opening_remark,
                character_image_id,
                is_public,
                creator_user_id
            FROM characters
            WHERE character_id = :character_id
            LIMIT 1   
        """),
        {"character_id": character_id},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Character not found")
    
    is_owner = str(row[10]) == current_user["user_id"]
    is_public = row[9]

    if not is_owner and not is_public:
        raise HTTPException(status_code=403, detail="Not allowed to view this character")
    
    return CharacterDetailResponse(
        character_id=str(row[0]),
        character_name=row[1],
        character_personality=row[2],
        character_intro=row[3],
        character_call_user=row[4],
        chat_style=row[5],
        hidden_story=row[6],
        opening_remark=row[7],
        character_image_id=str(row[8]) if row[8] else None,
        is_public=row[9],
        creator_user_id=str(row[10]),
    )