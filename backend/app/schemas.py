## This is for API request/response data
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ChatRequest(BaseModel):
    user_id: UUID
    character_id: UUID
    message: str
    conversation_id: Optional[UUID] = None

class ChatResponse(BaseModel):
    reply: str
    conversation_id: str