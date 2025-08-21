from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.database import get_db
from app.features.auth.dependencies import get_current_user
from app.features.projects.service import ProjectService
from app.features.chat.schemas import (
    ChatRequest, ChatResponse, RAGChatRequest, LLMProvider,
    ModelListResponse, ModelInstallRequest, InstallTaskResponse,
    InstallProgress, ModelDeleteResponse, InstallCancelResponse
)
from app.features.chat.service import ChatService
from app.models.user import User
from app.core.model_config import model_config_manager

router = APIRouter()


@router.post("/send", response_model=ChatResponse)
async def send_chat_message(
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message to the LLM and get response"""
    try:
        # Verify user has access to the project
        await ProjectService.get_project_by_id(db, chat_request.project_id, current_user)
        
        # Send message to LLM
        response = await ChatService.send_message_to_llm(chat_request)
        
        # TODO: Store chat history in database/cache
        
        return response
    except Exception as e:
        # Log detailed error for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat error: {str(e)}"
        )


@router.post("/send-rag", response_model=ChatResponse)
async def send_rag_chat_message(
    chat_request: RAGChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """RAG機能を使用してメッセージを送信し、ドキュメントとチーム情報を活用した回答を得る"""
    # プロジェクトへのアクセス権限確認
    await ProjectService.get_project_by_id(db, chat_request.project_id, current_user)
    
    # ChatRequestに変換
    basic_chat_request = ChatRequest(
        message=chat_request.message,
        project_id=chat_request.project_id,
        provider=chat_request.provider,
        model=chat_request.model,
        context=chat_request.context
    )
    
    # RAG機能を使用してメッセージを送信
    response = await ChatService.send_message_with_rag(
        db, 
        basic_chat_request, 
        chat_request.project_id, 
        chat_request.team_id
    )
    
    # TODO: チャット履歴をデータベース/キャッシュに保存
    
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


@router.get("/health")
async def check_llm_health():
    """Check LLM provider connectivity"""
    health_status = {}
    
    try:
        # Check Ollama
        ollama_status = await ChatService.check_ollama_health()
        health_status["ollama"] = ollama_status
    except Exception as e:
        health_status["ollama"] = {"status": "error", "message": str(e)}
    
    try:
        # Check LM Studio
        lm_studio_status = await ChatService.check_lm_studio_health()
        health_status["lm_studio"] = lm_studio_status
    except Exception as e:
        health_status["lm_studio"] = {"status": "error", "message": str(e)}
    
    return health_status


@router.post("/test-send", response_model=ChatResponse)
async def test_chat_message(chat_request: ChatRequest):
    """Test endpoint for chat without authentication (temporary for debugging)"""
    # Send message to LLM without authentication check
    response = await ChatService.send_message_to_llm(chat_request)
    return response


# Test endpoints without authentication (temporary for debugging)

@router.get("/test/models", response_model=ModelListResponse)
async def test_get_models(provider: LLMProvider = LLMProvider.OLLAMA):
    """Test endpoint for getting models without authentication"""
    return await ChatService.get_models(provider)


@router.post("/test/models/install", response_model=InstallTaskResponse)
async def test_install_model(request: ModelInstallRequest):
    """Test endpoint for installing models without authentication"""
    task_id = await ChatService.install_model(request.model_name, request.provider)
    return InstallTaskResponse(
        task_id=task_id,
        message=f"Installation of {request.model_name} started. Use task_id to check progress."
    )


@router.get("/test/models/install/{task_id}", response_model=InstallProgress)
async def test_get_install_progress(task_id: str):
    """Test endpoint for getting install progress without authentication"""
    return ChatService.get_install_progress(task_id)


@router.post("/test/models/install/{task_id}/cancel", response_model=InstallCancelResponse)
async def test_cancel_install_task(task_id: str):
    """Test endpoint for canceling install tasks without authentication"""
    return await ChatService.cancel_install_task(task_id)


@router.delete("/test/models/{model_name}", response_model=ModelDeleteResponse)
async def test_delete_model(model_name: str, provider: LLMProvider = LLMProvider.OLLAMA):
    """Test endpoint for deleting models without authentication"""
    return await ChatService.delete_model(model_name, provider)


# Model Management Endpoints

@router.get("/models", response_model=ModelListResponse)
async def get_models(
    provider: LLMProvider = LLMProvider.OLLAMA,
    current_user: User = Depends(get_current_user)
):
    """Get list of installed models for a provider"""
    return await ChatService.get_models(provider)


@router.post("/models/install", response_model=InstallTaskResponse)
async def install_model(
    request: ModelInstallRequest,
    current_user: User = Depends(get_current_user)
):
    """Start model installation and return task ID"""
    task_id = await ChatService.install_model(request.model_name, request.provider)
    return InstallTaskResponse(
        task_id=task_id,
        message=f"Installation of {request.model_name} started. Use task_id to check progress."
    )


@router.get("/models/install/{task_id}", response_model=InstallProgress)
async def get_install_progress(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get installation progress by task ID"""
    return ChatService.get_install_progress(task_id)


@router.post("/models/install/{task_id}/cancel", response_model=InstallCancelResponse)
async def cancel_install_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel an ongoing model installation task"""
    return await ChatService.cancel_install_task(task_id)


@router.delete("/models/{model_name}", response_model=ModelDeleteResponse)
async def delete_model(
    model_name: str,
    provider: LLMProvider = LLMProvider.OLLAMA,
    current_user: User = Depends(get_current_user)
):
    """Delete a model"""
    return await ChatService.delete_model(model_name, provider)


@router.get("/models/presets")
async def get_model_presets(
    provider: LLMProvider = LLMProvider.OLLAMA,
    category: Optional[str] = None,
    recommended_only: bool = False
):
    """Get model presets from configuration file"""
    try:
        if recommended_only:
            models = model_config_manager.get_recommended_models(provider)
        elif category:
            models = model_config_manager.get_models_by_category(provider, category)
        else:
            models = model_config_manager.get_popular_models(provider)
        
        categories = model_config_manager.get_categories(provider)
        
        return {
            "provider": provider.value,
            "models": [model.dict() for model in models],
            "categories": {k: v.dict() for k, v in categories.items()},
            "metadata": model_config_manager.get_config().metadata
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model presets: {str(e)}"
        )


@router.post("/models/presets/reload")
async def reload_model_presets(
    current_user: User = Depends(get_current_user)
):
    """Reload model presets from configuration file"""
    success = model_config_manager.reload_config()
    if success:
        return {"message": "Model presets reloaded successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reload model presets"
        )