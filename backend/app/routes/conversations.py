from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import ConversationItemResponse
from app.security import get_current_user

router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.get("", response_model=List[ConversationItemResponse])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    rows = db.execute(
        text("""
            SELECT
                c.conversation_id,
                c.character_id,
                ch.character_name,
                (
                    SELECT m.message_text
                    FROM messages m
                    WHERE m.conversation_id = c.conversation_id
                    ORDER BY m.created_at DESC
                    LIMIT 1
                ) AS last_message,
                c.last_message_at
             FROM conversations c
             JOIN characters ch
                ON c.character_id = ch.character_id
             WHERE c.user_id = :user_id
             ORDER BY c.last_message_at DESC NULLS LAST, c.created_at DESC
        """),
        {"user_id": current_user["user_id"]},
    ).fetchall()

    results = []
    for row in rows:
        results.append(
            ConversationItemResponse(
                conversation_id=str(row[0]),
                character_id=str(row[1]),
                character_name=row[2],
                last_message=row[3],
                last_message_at=str(row[4]) if row[4] else None
            )
        )
    return results

