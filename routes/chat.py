from fastapi import APIRouter
from models.chat_model import ChatRequest
from services.agent_service import handle_chat

router = APIRouter()

@router.post("/chat")
async def chat(req: ChatRequest):
    return await handle_chat(req)