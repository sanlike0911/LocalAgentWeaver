from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime


class ChatRequest(BaseModel):
    message: str
    project_id: int
    provider: LLMProvider = LLMProvider.OLLAMA
    model: str = "llama3"
    context: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    provider: str
    model: str
    usage: Optional[Dict[str, Any]] = None


class ChatHistory(BaseModel):
    project_id: int
    messages: list[ChatMessage]