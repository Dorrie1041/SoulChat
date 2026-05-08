## This is for API request/response data
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    user_id: str
    username: str
    email: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    username: str
    email: str


class CharacterCreateRequest(BaseModel):
    character_name: str
    character_personality: Optional[str] = None
    character_intro: Optional[str] = None
    character_call_user: Optional[str] = None
    chat_style: Optional[str] = None
    hidden_story: Optional[str] = None
    character_image_id: Optional[UUID] = None
    is_public: bool = False
    opening_remark: Optional[str] = None


class CharacterCreateResponse(BaseModel):
    character_id: str
    character_name: str
    creator_user_id: str
    opening_remark: Optional[str] = None


class ChatRequest(BaseModel):
    character_id: UUID
    message: str
    conversation_id: Optional[UUID] = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str

class CharacterItemResponse(BaseModel):
    character_id: str
    character_name: str
    character_personality: Optional[str] = None
    character_intro: Optional[str] = None
    character_call_user: Optional[str] = None
    chat_style: Optional[str] = None
    hidden_story: Optional[str] = None
    opening_remark: Optional[str] = None
    character_image_id: Optional[str] = None
    character_image_url: Optional[str] = None
    is_public: bool
    creator_user_id: str

class CharacterDetailResponse(BaseModel):
    character_id: str
    character_name: str
    character_personality: Optional[str] = None
    character_intro: Optional[str] = None
    character_call_user: Optional[str] = None
    chat_style: Optional[str] = None
    hidden_story: Optional[str] = None
    opening_remark: Optional[str] = None
    character_image_id: Optional[str] = None
    character_image_url: Optional[str] = None
    is_public: bool
    creator_user_id: str

class CharacterUpdateRequest(BaseModel):
    character_name: str
    character_personality: Optional[str] = None
    character_intro: Optional[str] = None
    character_call_user: Optional[str] = None
    chat_style: Optional[str] = None
    hidden_story: Optional[str] = None
    opening_remark: Optional[str] = None
    character_image_id: Optional[str] = None
    is_public: bool

class ConversationItemResponse(BaseModel):
    conversation_id: str
    character_id: str
    character_name: str
    last_message: Optional[str] = None
    last_message_at: Optional[str] = None

class MessageItemResponse(BaseModel):
    message_id: str
    conversation_id: str
    sender_type: str
    message_text: Optional[str] = None
    message_type: str
    created_at: Optional[str] = None

class MessageRegenerateRequest(BaseModel):
    new_message: str

class MessageRegenerateResponse(BaseModel):
    reply: str
    conversation_id: str
    user_message_id: str
    assistant_message_id: str

class MeResponse(BaseModel):
    user_id: str
    username: Optional[str] = None
    email: str
    role: Optional[str] = None
    persona_preference: Optional[str] = None
    created_at: Optional[str] = None

class MeUpdateRequest(BaseModel):
    username: Optional[str] = None
    persona_preference: Optional[str] = None


class ImageUploadResponse(BaseModel):
    image_id: str
    storage_path: str
    public_url: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    uploaded_by_user_id: str


class ImageItemResponse(BaseModel):
    image_id: str
    storage_path: str
    public_url: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    uploaded_by_user_id: str
    created_at: str