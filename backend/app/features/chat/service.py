import httpx
import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.features.chat.schemas import (
    ChatRequest, ChatResponse, LLMProvider, ChatMessage,
    ModelInfo, ModelListResponse, InstallProgress, InstallTaskStatus,
    ModelDeleteResponse
)
from app.features.documents.service import DocumentService
from app.models.team import Team, Agent
from sqlalchemy import select
from sqlalchemy.orm import selectinload


# In-memory storage for background tasks (In production, use Redis or DB)
install_tasks: Dict[str, InstallProgress] = {}


class ChatService:
    @staticmethod
    async def send_message_with_rag(
        db: AsyncSession,
        chat_request: ChatRequest,
        project_id: int,
        team_id: Optional[int] = None
    ) -> ChatResponse:
        """RAG機能を使用してメッセージをLLMに送信"""
        try:
            # アクティブなドキュメントのコンテキストを取得
            document_context = await DocumentService.get_active_documents_content(db, project_id)
            
            # チーム情報を取得してエージェントのシステムプロンプトを適用
            team_context = await ChatService._get_team_context(db, team_id) if team_id else ""
            
            # コンテキストを含むプロンプトを構築
            enhanced_message = await ChatService._build_context_aware_prompt(
                chat_request.message,
                document_context,
                team_context
            )
            
            # 拡張されたリクエストを作成
            enhanced_request = ChatRequest(
                message=enhanced_message,
                model=chat_request.model,
                provider=chat_request.provider,
                context=chat_request.context
            )
            
            return await ChatService.send_message_to_llm(enhanced_request)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"RAGチャット処理エラー: {str(e)}"
            )

    @staticmethod
    async def _get_team_context(db: AsyncSession, team_id: int) -> str:
        """チームのエージェント情報からコンテキストを構築"""
        result = await db.execute(
            select(Team)
            .options(selectinload(Team.agents))
            .where(Team.id == team_id)
        )
        team = result.scalar_one_or_none()
        
        if not team:
            return ""
        
        context_parts = [f"チーム: {team.name}"]
        if team.description:
            context_parts.append(f"チームの役割: {team.description}")
        
        if team.agents:
            context_parts.append("エージェント構成:")
            for agent in team.agents:
                context_parts.append(f"- {agent.name}: {agent.role}")
                if agent.system_prompt:
                    context_parts.append(f"  システムプロンプト: {agent.system_prompt}")
        
        return "\n".join(context_parts)

    @staticmethod
    async def _build_context_aware_prompt(
        user_message: str,
        document_chunks: List[str],
        team_context: str
    ) -> str:
        """ドキュメントとチーム情報を含むプロンプトを構築"""
        prompt_parts = []
        
        # システムプロンプト
        prompt_parts.append("あなたは以下の情報を活用して質問に答えるAIアシスタントです。")
        
        # チーム情報
        if team_context:
            prompt_parts.append("\n【チーム情報】")
            prompt_parts.append(team_context)
        
        # ドキュメント情報
        if document_chunks:
            prompt_parts.append("\n【参照ドキュメント】")
            for i, chunk in enumerate(document_chunks[:10], 1):  # 最大10チャンクまで
                prompt_parts.append(f"[文書{i}] {chunk[:500]}...")  # チャンクを500文字に制限
        
        # ユーザーメッセージ
        prompt_parts.append(f"\n【質問】\n{user_message}")
        
        # 回答指示
        prompt_parts.append(
            "\n【回答指示】\n"
            "- 参照ドキュメントの情報を活用して回答してください\n"
            "- 情報が不足している場合は、その旨を明記してください\n"
            "- 回答の根拠となった文書番号を示してください"
        )
        
        return "\n".join(prompt_parts)

    @staticmethod
    async def send_message_to_llm(chat_request: ChatRequest) -> ChatResponse:
        """Send message to the specified LLM provider"""
        try:
            if chat_request.provider == LLMProvider.OLLAMA:
                return await ChatService._send_to_ollama(chat_request)
            elif chat_request.provider == LLMProvider.LM_STUDIO:
                return await ChatService._send_to_lm_studio(chat_request)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported LLM provider: {chat_request.provider}"
                )
        except httpx.ConnectError as e:
            provider_name = chat_request.provider.value
            if provider_name == "ollama":
                url = settings.OLLAMA_BASE_URL
                suggestion = "Ollamaが起動していることを確認してください。`docker-compose --profile ollama up -d` または `ollama serve` を実行してください。"
            else:
                url = settings.LM_STUDIO_BASE_URL
                suggestion = "LM Studioが起動していることを確認してください。"
            
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to connect to {provider_name} at {url}. {suggestion} Error: {str(e)}"
            )
        except httpx.TimeoutException as e:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"LLM provider request timed out: {str(e)}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to connect to LLM provider: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing chat request: {str(e)}"
            )
    
    @staticmethod
    async def _send_to_ollama(chat_request: ChatRequest) -> ChatResponse:
        """Send message to Ollama"""
        url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        
        payload = {
            "model": chat_request.model,
            "prompt": chat_request.message,
            "stream": False
        }
        
        if chat_request.context:
            payload["context"] = chat_request.context
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                return ChatResponse(
                    message=result.get("response", ""),
                    provider="ollama",
                    model=chat_request.model,
                    usage={
                        "total_duration": result.get("total_duration"),
                        "load_duration": result.get("load_duration"),
                        "prompt_eval_count": result.get("prompt_eval_count"),
                        "eval_count": result.get("eval_count")
                    }
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Model '{chat_request.model}' not found. Please install the model first using: ollama pull {chat_request.model}"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Ollama API error {e.response.status_code}: {e.response.text}"
                    )
    
    @staticmethod
    async def _send_to_lm_studio(chat_request: ChatRequest) -> ChatResponse:
        """Send message to LM Studio"""
        url = f"{settings.LM_STUDIO_BASE_URL}/v1/chat/completions"
        
        messages = [{"role": "user", "content": chat_request.message}]
        
        payload = {
            "model": chat_request.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2048,
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            message_content = result["choices"][0]["message"]["content"]
            
            return ChatResponse(
                message=message_content,
                provider="lm_studio",
                model=chat_request.model,
                usage=result.get("usage", {})
            )
    
    @staticmethod
    def create_chat_message(role: str, content: str) -> ChatMessage:
        """Create a chat message with timestamp"""
        return ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.utcnow()
        )
    
    @staticmethod
    async def check_ollama_health() -> Dict[str, Any]:
        """Check Ollama connectivity and available models"""
        try:
            url = f"{settings.OLLAMA_BASE_URL}/api/tags"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                result = response.json()
                models = [model["name"] for model in result.get("models", [])]
                
                return {
                    "status": "healthy",
                    "url": settings.OLLAMA_BASE_URL,
                    "models": models
                }
        except httpx.ConnectError:
            return {
                "status": "unreachable",
                "url": settings.OLLAMA_BASE_URL,
                "message": "Ollamaに接続できません。サービスが起動していることを確認してください。"
            }
        except Exception as e:
            return {
                "status": "error",
                "url": settings.OLLAMA_BASE_URL,
                "message": str(e)
            }
    
    @staticmethod
    async def check_lm_studio_health() -> Dict[str, Any]:
        """Check LM Studio connectivity and available models"""
        try:
            url = f"{settings.LM_STUDIO_BASE_URL}/v1/models"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                result = response.json()
                models = [model["id"] for model in result.get("data", [])]
                
                return {
                    "status": "healthy",
                    "url": settings.LM_STUDIO_BASE_URL,
                    "models": models
                }
        except httpx.ConnectError:
            return {
                "status": "unreachable",
                "url": settings.LM_STUDIO_BASE_URL,
                "message": "LM Studioに接続できません。アプリケーションが起動していることを確認してください。"
            }
        except Exception as e:
            return {
                "status": "error",
                "url": settings.LM_STUDIO_BASE_URL,
                "message": str(e)
            }
    
    # Model Management Methods
    @staticmethod
    async def get_models(provider: LLMProvider) -> ModelListResponse:
        """Get list of installed models for a provider"""
        if provider == LLMProvider.OLLAMA:
            return await ChatService._get_ollama_models()
        elif provider == LLMProvider.LM_STUDIO:
            return await ChatService._get_lm_studio_models()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {provider}"
            )
    
    @staticmethod
    async def _get_ollama_models() -> ModelListResponse:
        """Get Ollama models list"""
        try:
            url = f"{settings.OLLAMA_BASE_URL}/api/tags"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                result = response.json()
                models = []
                
                for model_data in result.get("models", []):
                    # Convert size to human readable format if it's a number
                    size = model_data.get("size")
                    if isinstance(size, int):
                        # Convert bytes to human readable format
                        if size >= 1024**3:
                            size = f"{size / (1024**3):.1f}GB"
                        elif size >= 1024**2:
                            size = f"{size / (1024**2):.1f}MB"
                        elif size >= 1024:
                            size = f"{size / 1024:.1f}KB"
                        else:
                            size = f"{size}B"
                    
                    model_info = ModelInfo(
                        name=model_data.get("name", ""),
                        size=size,
                        modified=datetime.fromisoformat(model_data["modified_at"].replace("Z", "+00:00")) if model_data.get("modified_at") else None,
                        digest=model_data.get("digest"),
                        details=model_data.get("details")
                    )
                    models.append(model_info)
                
                return ModelListResponse(provider="ollama", models=models)
                
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to get Ollama models: {str(e)}"
            )
    
    @staticmethod
    async def _get_lm_studio_models() -> ModelListResponse:
        """Get LM Studio models list"""
        try:
            url = f"{settings.LM_STUDIO_BASE_URL}/v1/models"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                result = response.json()
                models = []
                
                for model_data in result.get("data", []):
                    model_info = ModelInfo(
                        name=model_data.get("id", ""),
                        details={"object": model_data.get("object"), "owned_by": model_data.get("owned_by")}
                    )
                    models.append(model_info)
                
                return ModelListResponse(provider="lm_studio", models=models)
                
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to get LM Studio models: {str(e)}"
            )
    
    @staticmethod
    async def install_model(model_name: str, provider: LLMProvider) -> str:
        """Start model installation and return task ID"""
        task_id = str(uuid.uuid4())
        
        if provider == LLMProvider.OLLAMA:
            # Create install task
            install_tasks[task_id] = InstallProgress(
                task_id=task_id,
                model_name=model_name,
                provider=provider.value,
                status=InstallTaskStatus.PENDING,
                message="Installation queued",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Start background installation
            asyncio.create_task(ChatService._install_ollama_model(task_id, model_name))
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model installation not supported for provider: {provider}"
            )
        
        return task_id
    
    @staticmethod
    async def _install_ollama_model(task_id: str, model_name: str):
        """Background task for Ollama model installation"""
        try:
            # Update status to running
            install_tasks[task_id].status = InstallTaskStatus.RUNNING
            install_tasks[task_id].message = f"Installing {model_name}..."
            install_tasks[task_id].updated_at = datetime.utcnow()
            
            url = f"{settings.OLLAMA_BASE_URL}/api/pull"
            payload = {"name": model_name}
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                # Update status to completed
                install_tasks[task_id].status = InstallTaskStatus.COMPLETED
                install_tasks[task_id].progress = 1.0
                install_tasks[task_id].message = f"Model {model_name} installed successfully"
                install_tasks[task_id].updated_at = datetime.utcnow()
                
        except Exception as e:
            # Update status to failed
            install_tasks[task_id].status = InstallTaskStatus.FAILED
            install_tasks[task_id].message = f"Installation failed: {str(e)}"
            install_tasks[task_id].updated_at = datetime.utcnow()
    
    @staticmethod
    def get_install_progress(task_id: str) -> InstallProgress:
        """Get installation progress by task ID"""
        if task_id not in install_tasks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Install task not found"
            )
        return install_tasks[task_id]
    
    @staticmethod
    async def delete_model(model_name: str, provider: LLMProvider) -> ModelDeleteResponse:
        """Delete a model"""
        if provider == LLMProvider.OLLAMA:
            return await ChatService._delete_ollama_model(model_name)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model deletion not supported for provider: {provider}"
            )
    
    @staticmethod
    async def _delete_ollama_model(model_name: str) -> ModelDeleteResponse:
        """Delete Ollama model"""
        try:
            url = f"{settings.OLLAMA_BASE_URL}/api/delete"
            payload = {"name": model_name}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request("DELETE", url, json=payload)
                response.raise_for_status()
                
                return ModelDeleteResponse(
                    success=True,
                    message=f"Model {model_name} deleted successfully"
                )
                
        except Exception as e:
            return ModelDeleteResponse(
                success=False,
                message=f"Failed to delete model {model_name}: {str(e)}"
            )