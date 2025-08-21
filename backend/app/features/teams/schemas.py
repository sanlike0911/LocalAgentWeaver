from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime


class AgentBase(BaseModel):
    name: str
    role: str
    system_prompt: Optional[str] = None


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    system_prompt: Optional[str] = None


class Agent(AgentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None


class TeamCreate(TeamBase):
    project_id: int
    agent_ids: Optional[List[int]] = []


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    agent_ids: Optional[List[int]] = None


class Team(TeamBase):
    id: int
    project_id: int
    agents: List[Agent] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True