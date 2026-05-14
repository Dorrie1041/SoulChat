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
import json

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

MEMORY_EXTRACT_PROMPT = """
You are a memory extraction agent for an AI companion app.

Extract only useful long-term memories about the user from the latest user message.

Return ONLY valid JSON.

Format:
{
  "memories": [
    {
      "memory_key": "short_key",
      "memory_value": "specific user fact",
      "importance_score": 1
    }
  ]
}

Rules:
- Only save facts that may be useful in future conversations.
- Do not save temporary or useless information.
- Do not invent facts.
- importance_score must be 1 to 5.
- If there is nothing useful, return {"memories": []}.
"""

RELATIONSIP_EVAL_PROMPT = """
You are a relationship state evaluator for an AI companion app.

Analyze the latest user message and assistant reply.
Return ONLY valid JSON.

Format:
{
  "closeness_delta": 0,
  "trust_delta": 0,
  "affection_delta": 0,
  "mood": "neutral",
  "reason": "short reason"
}

Rules:
- Deltas must be integers from -2 to 3.
- closeness_delta increases when user shares daily life or personal feelings.
- trust_delta increases when user is vulnerable, asks for comfort, or receives support.
- affection_delta increases when user is romantic, playful, caring, or flirty.
- Use negative deltas only if user is rejecting, angry, uncomfortable, or distancing.
- Do not exaggerate changes.
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
            WHERE user_id = :user_id AND character_id = :character_id
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

        update_relationship_state(
            db=db,
            user_id=user_id,
            character_id=req.character_id,
        )

        memories = extract_memories_from_chat(user_message=req.message, 
                                              assistant_reply=reply)
        save_extracted_memories(
            db=db,
            user_id=str(user_id),
            character_id=str(req.character_id),
            memories=memories,
        )

        # Relationship evaluation should be after saving messages and memories, to ensure it has the most complete context, and the relationship change can be triggered by both user message and assistant reply
        relationship_state = evaluate_relationship_change(
            user_message=req.message,
            assistant_reply=reply,
            relationship_state=relationship_block,
        )

        # Update relationship state based on the evaluation result, so that the change can be reflected in the next conversation immediately. The relationship change is triggered by both user message and assistant reply, which means even if the user doesn't say anything that directly expresses emotion or affection, but the assistant's reply is good enough to make the user feel closer or more trusting, the relationship state can still be improved.
        update_relationship_state(
            db=db,
            user_id=str(user_id),
            character_id=str(req.character_id),
            closeness_delta=relationship_state["closeness_delta"],
            trust_delta=relationship_state["trust_delta"],
            affection_delta=relationship_state["affection_delta"],
            mood=relationship_state["mood"],
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
    
def evaluate_relationship_change(
        user_message: str,
        assistant_reply: str,
        relationship_state: str,
) -> str:
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": RELATIONSIP_EVAL_PROMPT,
            },
            {
                "role": "user",
                "content": f"""
                User Message: {user_message}
                Assistant Reply: {assistant_reply}
                Current Relationship State:
                {relationship_state}
                """,
            },
        ],
        temperature=0.2,
    )

    raw_text = response.choices[0].message.content or "{}"

    try:
        data = json.loads(raw_text)
    except Exception:
        return {
            "closeness_delta": 1,
            "trust_delta": 0,
            "affection_delta": 0,
            "mood": "neutral",
            "reason": "fallback",
        }
    return {
        "closeness_delta": max(-2, min(3, int(data.get("closeness_delta", 0)))),
        "trust_delta": max(-2, min(3, int(data.get("trust_delta", 0)))),
        "affection_delta": max(-2, min(3, int(data.get("affection_delta", 0)))),
        "mood": str(data.get("mood", "neutral"))[:50],
        "reason": str(data.get("reason", "fallback"))[:255],
    }


def get_relationship_stage(closeness: int, trust: int, affection: int) -> str:
    avg = (closeness + trust + affection) / 3

    if avg < 10:
        return "stranger"
    if avg < 30:
        return "familiar"
    if avg < 60:
        return "close"
    if avg < 85:
        return "intimate"
    return "deeply_bonded"

# Regenerate a specific message in the conversation, and update all messages after it accordingly
def update_relationship_state(
        db: Session,
        user_id: str,
        character_id: str,
        closeness_delta: int,
        trust_delta: int,
        affection_delta: int,
        mood: str,
) -> None:
    existing = db.execute(
        text("""
             SELECT state_id,
                    closeness_level,
                    trust_level,
                    affection_level,
                    interaction_count
             FROM relationship_state
             WHERE user_id = :user_id 
             AND character_id = :character_id
             LIMIT 1
        """),
        {"user_id": user_id, "character_id": character_id},
    ).fetchone()

    if existing:
        new_closeness = max(0, min(100, int(existing[1] or 0)) + closeness_delta)
        new_trust = max(0, min(100, int(existing[2] or 0)) + trust_delta)
        new_affection = max(0, min(100, int(existing[3] or 0)) + affection_delta)
        new_interaction_count = (existing[4] or 0) + 1
        new_stage = get_relationship_stage(new_closeness, new_trust, new_affection)

        db.execute(
            text("""
                 UPDATE relationship_state
                 SET closeness_level = :closeness_level,
                     trust_level = :trust_level,
                     affection_level = :affection_level,
                     interaction_count = :interaction_count,
                     last_interaction_at = NOW(),
                     updated_at = NOW()
                 WHERE user_id = :user_id AND character_id = :character_id
            """),
            {
                "character_id": character_id,
                "user_id": user_id,
                "closeness_level": new_closeness,
                "trust_level": new_trust,
                "affection_level": new_affection,
                "interaction_count": new_interaction_count,
                "current_mood": mood,
                "relationship_stage": new_stage,
            },
        )
    else:
        closeness_level = max(0, min(100, closeness_delta))
        trust_level = max(0, min(100, trust_delta))
        affection_level = max(0, min(100, affection_delta))
        stage = get_relationship_stage(closeness_level, trust_level, affection_level)

        db.execute(
            text("""
                INSERT INTO relationship_state (
                state_id,
                user_id,
                character_id,
                closeness_level,
                trust_level,
                affection_level,
                interaction_count,
                current_mood,
                relationship_stage,
                last_interaction_at,
                updated_at
                )
                VALUES (
                    :state_id,
                    :user_id,
                    :character_id,
                    :closeness_level,
                    :trust_level,
                    :affection_level,
                    1,
                    :current_mood,
                    :relationship_stage,
                    NOW(),
                    NOW()
                )
            """),
            {
                "state_id": str(uuid4()),
                "character_id": character_id,
                "user_id": user_id,
                "closeness_level": closeness_level,
                "trust_level": trust_level,
                "affection_level": affection_level,
                "current_mood": mood,
                "relationship_stage": stage,
            },
        )
    
    db.commit()


# save specified message, and all messages after it, into memory, then regenerate the specified message with new content
def extract_memories_from_chat(
        user_message: str,
        assistant_reply: str,
) -> list[dict]:
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": MEMORY_EXTRACT_PROMPT,
            },
            {
                "role": "user",
                "content": f"""
                User Message: {user_message}
                Assistant Reply: {assistant_reply}
                """,
            },
        ],
        temperature=0.2,
    )

    raw_text = response.choices[0].message.content or "{\"memories\": []}"

    try: 
        data = json.loads(raw_text)
        memories = data.get("memories", [])
        if isinstance(memories, list):
            return memories
        return []
    except Exception:
        return []


def save_extracted_memories(
        db: Session,
        user_id: str,
        character_id: str,
        memories: list[dict],
) -> None:
    for memory in memories:
        memory_key = memory.get("memory_key", "")
        memory_value = memory.get("memory_value", "")
        importance_score = memory.get("importance_score", 1)

        if not memory_key or not memory_value:
            continue

        importance_score = max(1, min(5, importance_score))

        existing = db.execute(
            text("""
                SELECT memory_id
                FROM character_memories
                WHERE user_id = :user_id 
                 AND character_id = :character_id 
                 AND memory_key = :memory_key
                LIMIT 1
            """),
            {
                "user_id": user_id,
                "character_id": character_id,
                "memory_key": memory_key,
            },
        ).fetchone()

        if existing:
            db. execute(
            text("""
                UPDATE character_memories
                SET memory_value = :memory_value,
                    importance_score = :importance_score,
                    updated_at = NOW()
                WHERE memory_id = :memory_id
            """),
            {
                "memory_id": str(existing[0]),
                "memory_value": memory_value,
                "importance_score": importance_score,
            },
        )
        else:
            db.execute(
                text("""
                    INSERT INTO character_memories (
                        memory_id,
                        user_id,
                        character_id,
                        memory_key,
                        memory_value,
                        importance_score,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        :memory_id,
                        :user_id,
                        :character_id,
                        :memory_key,
                        :memory_value,
                        :importance_score,
                        NOW(),
                        NOW()
                    )
                """),
                {
                    "memory_id": str(uuid4()),
                    "user_id": user_id,
                    "character_id": character_id,
                    "memory_key": memory_key,
                    "memory_value": memory_value,
                    "importance_score": importance_score,
                },
            )
    db.commit()

