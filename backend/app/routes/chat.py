from fastapi import APIRouter
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest):
    return ChatResponse(reply=f"You said: {req.message}")

