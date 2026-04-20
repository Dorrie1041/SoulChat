from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import ConversationItemResponse, MessageItemResponse
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

@router.get("/{conversation_id}/messages", response_model=List[MessageItemResponse])
def get_conversation_messages(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    conversation = db.execute(
        text("""
            SELECT conversation_id, user_id
            FROM conversations
            WHERE conversation_id = :conversation_id
            LIMIT 1   
        """
        ),
        {"conversation_id": conversation_id},
    ).fetchone()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if str(conversation[1]) != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not allowed to view this conversation")
    
    rows = db.execute(
        text("""
            SELECT 
                message_id,
                conversation_id,
                sender_type,
                message_text,
                message_type,
                created_at
            FROM messages
            WHERE conversation_id = :conversation_id
            ORDER BY created_at ASC  
        """),
        {"conversation_id": conversation_id},
    ).fetchall()

    results = []

    for row in rows:
        results.append(
            MessageItemResponse(
                message_id=str(row[0]),
                conversation_id=str(row[1]),
                sender_type=row[2],
                message_text=row[3],
                message_type=row[4],
                created_at=str(row[5]) if row[5] else None, 
            )
        )
    
    return results