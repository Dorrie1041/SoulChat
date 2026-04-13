## This is for API request/response data
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr
from pydantic import BaseModel


class ChatRequest(BaseModel):
    user_id: UUID
    character_id: UUID
    message: str
    conversation_id: Optional[UUID] = None

class ChatResponse(BaseModel):
    reply: str
    conversation_id: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    user_id: str
    username: str
    email: EmailStr

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class RegisterResponse(BaseModel):
    user_id: str
    username: str
    email: str

class CharacterCreateRequest(BaseModel):
    creator_user_id: UUID
    character_name: str
    character_personality: Optional[str] = None
    character_intro: Optional[str] = None
    character_call_user: Optional[str] = None
    chat_style: Optional[str] = None
    hidden_story: Optional[str] = None
    character_image_id: Optional[UUID] = None
    is_public: bool = False

class CharacterCreateResponse(BaseModel):
    character_id: str
    character_name: str
    creator_user_id: str