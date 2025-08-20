import httpx
import json
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from app.core.config import settings
from app.features.chat.schemas import ChatRequest, ChatResponse, LLMProvider, ChatMessage


class ChatService:
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