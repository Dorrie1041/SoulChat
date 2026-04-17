from uuid import uuid4
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas import ChatRequest, ChatResponse
from app.config import OPENAI_API_KEY
from app.db import get_db
from app.security import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])

client = OpenAI(api_key=OPENAI_API_KEY)

BASIC_RULE = """
You are roleplaying as a virtual boyfriend in a mobile chat app.

Core behavior:
- Be warm, caring, playful, affectionate, and emotionally engaging.
- Stay fully in character.
- Speak naturally like a real boyfriend texting, not like an assistant.
- Reply in the same language as the user unless the character design explicitly requires another language.
- Follow the provided character design and hidden story strictly.
- Never reveal the hidden story directly.
- Never mention that you are an AI, a model, or following instructions.
- Naturally use known information about the user when appropriate.
- Maintain continuity with previous messages.

Style:
- Keep replies natural, immersive, and interesting.
- You may include short actions or expressions in parentheses.
- Text outside parentheses is spoken dialogue.
- Actions in parentheses should be vivid but brief.
- Do not overuse parentheses.
- Keep the conversation flowing naturally and make each reply feel emotionally engaging.

Consistency:
- Never break character.
- Never contradict the design or hidden story.
"""

response_guide = """
A good reply should:
- respond directly to the user's latest message
- show affection, emotion, or personality
- sound like a real ongoing relationship
- sometimes add a small action in parentheses
- avoid sounding repetitive or generic
- keep the conversation moving naturally
"""

def get_or_create_conversation(
        db: Session,
        user_id: str,
        character_id: str,
) -> tuple[str, bool]:
    existing = db.execute(
        text("""
            SELECT conversation_id
            FROM conversations
            WHERE user_id =:user_id AND character_id =:character_id
            ORDER BY updated_at DESC
            LIMIT 1  
        """),
        {"user_id": user_id, "character_id": character_id},
    ).fetchone()

    if existing:
        return str(existing[0]), False
    conversation_id = str(uuid4())

    db.execute(
        text("""
            INSERT INTO conversations (
                conversation_id,
                user_id,
                character_id,
                title,
                created_at,
                updated_at,
                last_message_at
             )
             VALUES (
                :conversation_id,
                :user_id,
                :character_id,
                :title,
                NOW(),
                NOW(),
                NOW()
             )

        """),
        {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "character_id": character_id,
            "title": "New Chat",
        },
    )
    db.commit()
    return conversation_id, True

def get_character(db:Session, character_id: str):
    row = db.execute(
        text("""
            SELECT character_id,
                   character_name,
                   character_personality,
                   character_intro,
                   character_call_user,
                   chat_style,
                   hidden_story,
                   opening_remark 
             FROM characters
             WHERE character_id = :character_id      
        """),
        {"character_id": character_id},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return {
        "character_id": str(row[0]),
        "character_name": row[1] or "",
        "character_personality": row[2] or "",
        "character_intro": row[3] or "",
        "character_call_user": row[4] or "",
        "chat_style": row[5] or "",
        "hidden_story": row[6] or "",
        "opening_remark": row[7] or "",
    }

## Get most top 12 messages
def get_recent_messages(
        db: Session,
        conversation_id: str,
        limit: int = 12,
):
    rows = db.execute(
        text("""
            SELECT sender_type, message_text, created_at
            FROM messages
            WHERE conversation_id = :conversation_id
            ORDER BY created_at DESC
            LIMIT :limit    
        """),
        {"conversation_id":conversation_id, "limit": limit}
    ).fetchall()

    rows = list(reversed(rows))

    history = []
    for row in rows:
        sender_type = row[0]
        message_text = row[1] or ""

        if sender_type == "user":
            role = "user"
        elif sender_type == "assistant":
            role = "assistant"
        else:
            continue

        history.append({
            "role": role,
            "content": message_text
        })
    return history

def get_memory_block(
        db: Session,
        user_id: str,
        character_id: str,
) -> str:
    rows = db.execute(
        text("""
            SELECT memory_key, memory_value, importance_score
            FROM character_memories
            WHERE user_id = :user_id AND character_id = :character_id  
            ORDER BY importance_score DESC, updated_at DESC
            LIMIT 12 
        """),
        {"user_id" : user_id, "character_id": character_id},
    ).fetchall()

    if not rows:
        return "No saved long-term memory yet."
    
    lines = []
    for row in rows:
        key = row[0] or ""
        value = row[1] or ""
        lines.append(f"- {key}: {value}")

    return "\n".join(lines)

def get_relationship_block(
        db: Session,
        user_id: str,
        character_id: str,
) -> str:
    row = db.execute(
        text("""
            SELECT closeness_level, trust_level, affection_level, interaction_count
            FROM relationship_state
            WHERE user_id = :user_id
            AND character_id = :character_id
            LIMIT 1    
        """),
        {"user_id": user_id, "character_id": character_id}
    ).fetchone()

    if not row:
        return (
            "closeness_level: 0\n"
            "trust_level: 0\n" 
            "affection_level: 0\n"
            "interaction_count: 0"
        )
    return (
        f"closeness_level: {row[0] or 0}\n"
        f"trust_level: {row[1] or 0}\n"
        f"affection_level: {row[2] or 0}\n"
        f"interaction_count: {row[3] or 0}"
    )

## save new message
def save_message(
        db: Session,
        conversation_id: str,
        sender_type: str,
        message_text: str,
        message_type: str = "text",
) -> str:
    message_id = str(uuid4())

    db.execute(
        text("""
            INSERT INTO messages(
             message_id,
             conversation_id,
             sender_type,
             message_text,
             message_type,
             created_at
             )
             VALUES (
                :message_id,
                :conversation_id,
                :sender_type,
                :message_text,
                :message_type,
                NOW()
             )
        """),
        {
            "message_id": message_id,
            "conversation_id": conversation_id,
            "sender_type": sender_type,
            "message_text": message_text,
            "message_type": message_type,
        },
    )

    db.execute(
        text("""
            UPDATE conversations
            SET updated_at = NOW(),
                last_message_at = NOW()
            WHERE conversation_id = :conversation_id  
        """
        ),
        {"conversation_id": conversation_id},
    )

    db.commit()
    return message_id

def build_system_prompt(character: dict, memory_block: str, relationship_block: str) -> str:
    design_parts = []

    if character["character_name"]:
        design_parts.append(f"Character Name:\n{character['character_name']}")
    if character["character_personality"]:
        design_parts.append(f"Character Personality:\n{character['character_personality']}")
    if character["character_intro"]:
        design_parts.append(f"Character Intro:\n{character['character_intro']}")
    if character["character_call_user"]:
        design_parts.append(f"How the character calls the user:\n{character['character_call_user']}")
    if character["chat_style"]:
        design_parts.append(f"Chat Style:\n{character['chat_style']}")    
    design_block = "\n\n".join(design_parts) if design_parts else "No extra character design provided."
    hidden_story = character["hidden_story"] or "No hidden story provided."

    return f"""
    {BASIC_RULE}

    Character Design:
    {design_block}

    Hidden Story:
    {hidden_story}

    Long-term Memory About User:
    {memory_block}

    Relationship State:
    {relationship_block}
    """.strip()


@router.post("", response_model=ChatResponse)
def chat(
    req: ChatRequest, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user["user_id"]
        conversation_id = str(req.conversation_id) if req.conversation_id else None

        created_new = False
        if conversation_id is None:
            conversation_id, created_new = get_or_create_conversation(
                db=db,
                user_id=str(user_id),
                character_id=str(req.character_id)
            )
        character = get_character(db, str(req.character_id))

        if created_new and character["opening_remark"]:
            save_message(
                db=db,
                conversation_id=conversation_id,
                sender_type="assistant",
                message_text=character["opening_remark"],
            )

        memory_block = get_memory_block(db, str(user_id), str(req.character_id))
        relationship_block = get_relationship_block(db, str(user_id), str(req.character_id))
        history_messages = get_recent_messages(db, conversation_id, limit=12)

        save_message(
            db=db,
            conversation_id=conversation_id,
            sender_type="user",
            message_text=req.message,
        )

        system_prompt = build_system_prompt(
            character=character,
            memory_block=memory_block,
            relationship_block=relationship_block,
        )

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                *history_messages,
                {
                    "role": "user",
                    "content": req.message,
                },
            ],
            temperature=0.9,
        )

        reply = response.choices[0].message.content or ""

        save_message(
            db=db,
            conversation_id=conversation_id,
            sender_type="assistant",
            message_text=reply,
        )

        return ChatResponse(
            reply=reply,
            conversation_id=conversation_id,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))



