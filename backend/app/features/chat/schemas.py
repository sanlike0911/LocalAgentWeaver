from pydantic import BaseModel
from typing import Optional, Dict, Any, List
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
    model: str = "llama3.2:1b"
    context: Optional[str] = None


class RAGChatRequest(BaseModel):
    message: str
    project_id: int
    team_id: Optional[int] = None
    provider: LLMProvider = LLMProvider.OLLAMA
    model: str = "llama3.2:1b"
    context: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    provider: str
    model: str
    usage: Optional[Dict[str, Any]] = None


class ChatHistory(BaseModel):
    project_id: int
    messages: list[ChatMessage]


# Model Management Schemas
class ModelInfo(BaseModel):
    name: str
    size: Optional[Any] = None  # Can be string or int depending on provider
    modified: Optional[datetime] = None
    digest: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ModelListResponse(BaseModel):
    provider: str
    models: List[ModelInfo]


class ModelInstallRequest(BaseModel):
    model_name: str
    provider: LLMProvider = LLMProvider.OLLAMA


class InstallTaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InstallProgress(BaseModel):
    task_id: str
    model_name: str
    provider: str
    status: InstallTaskStatus
    progress: Optional[float] = None  # 0.0 to 1.0
    message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class InstallTaskResponse(BaseModel):
    task_id: str
    message: str


class ModelDeleteResponse(BaseModel):
    success: bool
    message: str


class InstallCancelResponse(BaseModel):
    success: bool
    message: str
    task_id: str