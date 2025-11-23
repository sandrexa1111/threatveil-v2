from fastapi import APIRouter, Depends

from ..schemas import ChatRequest, ChatResponse
from ..services.llm_service import chat_completion

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    message = await chat_completion(body.prompt)
    return ChatResponse(message=message)
