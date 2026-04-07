# record all table from database

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Integer, Date, TIMESTAMP
from sqlalchemy.sql import func
from app.db import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(Text)
    role = Column(String(20), default="user")
    persona_preference = Column(Text)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

class Character(Base):
    __tablename__ = "characters"

    character_id = Column(String, primary_key=True)
    creator_user_id = Column(String, ForeignKey("users.user_id"))
    character_name = Column(String(100), nullable=False)
    character_personality = Column(Text)
    character_intro = Column(Text)
    character_call_user = Column(String(100))
    chat_style = Column(Text)
    hidden_story = Column(Text)
    character_image_id = Column(String, ForeignKey("images.image_id"))
    is_public = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

class Image(Base):

    __tablename__ = "images"

    image_id = Column(String, primary_key=True)
    storage_path = Column(Text, nullable=False)
    public_url = Column(Text)
    mime_type = Column(String(100))
    file_size = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    uploaded_by_user_id = Column(String, ForeignKey("users.user_id"))
    created_id = Column(TIMESTAMP, nullable=False, server_default=func.now())

class Conversation(Base):
    __tablename__ = "conversations"

    conversation_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    character_id = Column(String, ForeignKey("characters.character_id"))
    title = Column(String(255))
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    last_message_at = Column(TIMESTAMP)

class Message(Base):
    __tablename__ = "messages"

    message_id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.conversation_id"))
    sender_type = Column(String(20), nullable=False)
    message_text = Column(Text)
    message_type = Column(String(20), default="text")
    created_id = Column(TIMESTAMP, nullable=False, server_default=func.now())


