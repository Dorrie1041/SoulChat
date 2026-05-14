import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    ConversationItemResponse, 
    MessageItemResponse,
    SuggestedRepliesResponse,
    ContinueCharacterResponse
)
from app.security import get_current_user
from app.routes.chat import(
    client,
    get_character,
    get_memory_block,
    get_relationship_block,
    get_recent_messages,
    build_system_prompt,
    save_message
)

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

@router.post("/{conversation_id}/suggested_replies", response_model=SuggestedRepliesResponse)
def suggest_replies(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    conversation = db.execute(
        text("""
            SELECT conversation_id, user_id, character_id
            FROM conversations
            WHERE conversation_id = :conversation_id 
             And user_id = :user_id
            LIMIT 1
        """),
        {"conversation_id": conversation_id, "user_id": current_user["user_id"]},
    ).fetchone()


    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")  
     
    character_id = str(conversation[2])
    user_id = current_user["user_id"]

    character = get_character(db, character_id)
    memory_block = get_memory_block(db, user_id, character_id)
    relationship_block = get_relationship_block(db, user_id, character_id)
    history_messages = get_recent_messages(db, conversation_id, limit=12)

    system_prompt = build_system_prompt(
        character=character,
        memory_block=memory_block,
        relationship_block=relationship_block,
    )

    response = client.chat.completions.create (
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            *history_messages,
            {
                "role": "user",
                "content": """
    Generate 4 short possible replies the USER could send next.

    Rules:
    - Replies should match the user's likely emotional position in this conversation.
    - Each reply should be natural, conversational, and short.
    - Do not answer as the character.
    - Return ONLY JSON in this format:
    {"suggestions": ["...", "...", "...", "..."]}
    """
            },
        ],
        temperature=0.8,
    )

    

    raw_text = response.choices[0].message.content or "{suggestions: []}"

    try:
        data = json.loads(raw_text)
        suggestions = data.get("suggestions", [])
    except Exception:
        suggestions = []


    suggestions = [str(s) for s in suggestions if str(s).strip()]
    suggestions = suggestions[:4]

    return SuggestedRepliesResponse(suggestions=suggestions)

@router.post("/{conversation_id}/continue}", response_model=ContinueCharacterResponse)
def continue_character(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    conversation = db.execute(
        text("""
            SELECT conversation_id, user_id, character_id
            FROM conversations
            WHERE conversation_id = :conversation_id 
             And user_id = :user_id
            LIMIT 1
        """),
        {
            "conversation_id": conversation_id, 
            "user_id": current_user["user_id"]
         },
    ).fetchone()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    character_id = str(conversation[2])
    user_id = current_user["user_id"]

    character = get_character(db, character_id)
    memory_block = get_memory_block(db, user_id, character_id)
    relationship_block = get_relationship_block(db, user_id, character_id)
    history_messages = get_recent_messages(db, conversation_id, limit=12)

    system_prompt = build_system_prompt(
        character=character,
        memory_block=memory_block,
        relationship_block=relationship_block,
    )

    response = client.chat.completions.create (
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            *history_messages,
            {
                "role": "user",
                "content": """
        The user is silent and tapped a button asking the character to continue talking.

        Continue as the character.
        Do not act as the user.
        Do not ask too many questions.
        Keep it natural, immersive, and emotionally engaging.
        """
            }
        ],
        temperature=0.9,
    )
    reply = response.choices[0].message.content or ""

    assistant_message_id = save_message(
        db=db,
        conversation_id=conversation_id,
        sender_type="assistant",
        message_text=reply,
        message_type="text",
    )

    return ContinueCharacterResponse(
        reply=reply,
        conversation_id=conversation_id,
        assistant_message_id=assistant_message_id
    )

