from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.features.auth.dependencies import get_current_user
from app.features.projects.service import ProjectService
from app.features.chat.schemas import ChatRequest, ChatResponse
from app.features.chat.service import ChatService
from app.models.user import User

router = APIRouter()


@router.post("/send", response_model=ChatResponse)
async def send_chat_message(
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message to the LLM and get response"""
    # Verify user has access to the project
    await ProjectService.get_project_by_id(db, chat_request.project_id, current_user)
    
    # Send message to LLM
    response = await ChatService.send_message_to_llm(chat_request)
    
    # TODO: Store chat history in database/cache
    
    return response


@router.get("/history/{project_id}")
async def get_chat_history(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get chat history for a project"""
    # Verify user has access to the project
    await ProjectService.get_project_by_id(db, project_id, current_user)
    
    # TODO: Implement chat history retrieval from database/cache
    return {"project_id": project_id, "messages": []}