from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db import get_db
from app.security import get_current_user

from app.routes.chat import (
    client,
    get_character,
    get_memory_block,
    get_relationship_block,
    get_recent_messages,
    save_message,
    build_system_prompt,
)
from app.schemas import (
    MessageRegenerateRequest,
    MessageRegenerateResponse,              
)

router = APIRouter(tags=["messages"])

@router.delete("/conversations/{conversation_id}/messages/after/{message_id}")
def delete_messages_after(conversation_id: str, 
                          message_id: str, 
                          db: Session = Depends(get_db),
                          current_user: dict = Depends(get_current_user)):
    selected = db.execute(
        text("""
            SELECT m.created_at
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.conversation_id
            WHERE m.message_id = :message_id
              AND c.conversation_id = :conversation_id
              AND c.user_id = :user_id
        """),
        {"message_id": message_id, 
         "conversation_id": conversation_id, 
         "user_id": current_user["user_id"]
         },
    ).fetchone()

    if not selected:
        raise HTTPException(status_code=404, detail="Message not found")
    
    selected_created_at = selected[0]
    db.execute(
        text("""
            DELETE FROM messages
            WHERE conversation_id = :conversation_id
              AND created_at > :selected_created_at

        """),
        {"conversation_id": conversation_id, 
         "selected_created_at": selected_created_at}
    )

    db.execute(
        text("""
            UPDATE conversations
            SET last_message_at = (
                SELECT MAX(created_at)
                FROM messages
                WHERE conversation_id = :conversation_id
            ),
             updated_at = NOW()
            WHERE conversation_id = :conversation_id
        """),
        {"conversation_id": conversation_id}
    )

    db.commit()

    return {
        "message": "Coversation history has been rolled back to the selected message.",
        "conversation_id": conversation_id,
        "kept_message_id": message_id
    }

@router.post(
    "/conversations/{conversation_id}/messages/{message_id}/regenerate",
    response_model=MessageRegenerateResponse,
)
def regenerate_from_message(
    conversation_id: str,
    message_id: str,
    request: MessageRegenerateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    selected = db.execute(
        text("""
            SELECT
                m.message_id,
                m.sender_type,,
                m.created_at
                c.character_id,
                c.user_id
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.conversation_id
            WHERE m.message_id = :message_id
              AND c.conversation_id = :conversation_id
              AND c.user_id = :user_id
              LIMIT 1
        """),
        {"message_id": message_id, 
         "conversation_id": conversation_id, 
         "user_id": current_user["user_id"]
         },
    ).fetchone()

    if not selected:
        raise HTTPException(status_code=404, detail="Message not found")
    
    sender_type = selected[1]
    selected_created_at = selected[2]
    character_id = selected[3]
    user_id = selected[4]

    if sender_type != "user":
        raise HTTPException(status_code=400, detail="Only user messages can be regenerated")
    
    try:
        db.execute(
            text("""
                DELETE FROM messages
                WHERE conversation_id = :conversation_id
                  AND created_at >= :selected_created_at
            """),
            {"conversation_id": conversation_id, 
             "selected_created_at": selected_created_at},
        )

        db.execute(
            text("""
                UPDATE messages
                SET message_text = :new_message
                WHERE message_id = :message_id
                 AND conversation_id = :conversation_id
            """),
            {
                "new_message": request.new_message,
                "message_id": message_id,
                "conversation_id": conversation_id
            },
        ) 

        db.execute(
            text("""
                UPDATE conversations
                SET updatesd_at = NOW(),
                    last_message_at = NOW()
                WHERE conversation_id = :conversation_id
            """),
            {"conversation_id": conversation_id}
        )

        db.commit()

        character = get_character(db, str(character_id))
        memory_block = get_memory_block(db, str(user_id), str(character_id))
        relationship_block = get_relationship_block(db, str(user_id), str(character_id))        
        history_messages = get_recent_messages(db, conversation_id, limit=12)

        system_prompt = build_system_prompt(
            character = character, 
            memory_block = memory_block, 
            relationship_block = relationship_block
            )
        
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                *history_messages,
            ],
            temperature=0.9,
        )

        reply = response.choices[0].message.content or ""

        assistant_message_id = save_message(
            db=db,
            conversation_id=conversation_id,
            sender_type="assistant",
            message_text=reply,
        )

        return MessageRegenerateResponse(
            reply=reply,
            conversation_id=conversation_id,
            user_message_id=message_id,
            assistant_message_id=assistant_message_id,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

        