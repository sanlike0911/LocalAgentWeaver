from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    chunking_strategy: Optional[str] = "sentence"
    chunking_config: Optional[Dict[str, Any]] = {}


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    chunking_strategy: Optional[str] = None
    chunking_config: Optional[Dict[str, Any]] = None


class ChunkingConfigUpdate(BaseModel):
    chunking_strategy: str
    chunking_config: Optional[Dict[str, Any]] = {}


class Project(ProjectBase):
    id: int
    owner_id: int
    chunking_strategy: Optional[str]
    chunking_config: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectList(BaseModel):
    projects: list[Project]
    total: int