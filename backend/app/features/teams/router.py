from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.features.auth.dependencies import get_current_user
from app.models.user import User
from . import schemas
from .service import TeamService, AgentService
from .presets import PresetService, AgentPreset, TeamPreset

router = APIRouter()


# チーム管理エンドポイント
@router.post("/teams", response_model=schemas.Team, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: schemas.TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await TeamService.create_team(db, team_data)


@router.get("/projects/{project_id}/teams", response_model=List[schemas.Team])
async def get_teams_by_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await TeamService.get_teams_by_project(db, project_id)


@router.get("/teams/{team_id}", response_model=schemas.Team)
async def get_team(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    team = await TeamService.get_team(db, team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    return team


@router.put("/teams/{team_id}", response_model=schemas.Team)
async def update_team(
    team_id: int,
    team_data: schemas.TeamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await TeamService.update_team(db, team_id, team_data)


@router.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = await TeamService.delete_team(db, team_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )


# エージェント管理エンドポイント
@router.post("/agents", response_model=schemas.Agent, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: schemas.AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await AgentService.create_agent(db, agent_data)


@router.get("/agents", response_model=List[schemas.Agent])
async def get_all_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await AgentService.get_all_agents(db)


@router.get("/agents/{agent_id}", response_model=schemas.Agent)
async def get_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    agent = await AgentService.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    return agent


@router.put("/agents/{agent_id}", response_model=schemas.Agent)
async def update_agent(
    agent_id: int,
    agent_data: schemas.AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await AgentService.update_agent(db, agent_id, agent_data)


@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = await AgentService.delete_agent(db, agent_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )


# プリセット管理エンドポイント
@router.get("/presets/agents", response_model=List[AgentPreset])
async def get_agent_presets(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """エージェントプリセット一覧を取得"""
    return PresetService.get_agent_presets(category)


@router.get("/presets/teams", response_model=List[TeamPreset])
async def get_team_presets(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """チームプリセット一覧を取得"""
    return PresetService.get_team_presets(category)


@router.get("/presets/categories")
async def get_preset_categories(
    current_user: User = Depends(get_current_user)
):
    """プリセットカテゴリ一覧を取得"""
    return PresetService.get_categories()


@router.post("/presets/agents/{preset_name}/instantiate", response_model=schemas.Agent)
async def instantiate_agent_preset(
    preset_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """エージェントプリセットからエージェントを作成"""
    try:
        preset = PresetService.get_agent_preset_by_name(preset_name)
        agent_data = schemas.AgentCreate(
            name=preset.name,
            role=preset.role,
            system_prompt=preset.system_prompt
        )
        return await AgentService.create_agent(db, agent_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/presets/teams/{preset_name}/instantiate", response_model=schemas.Team)
async def instantiate_team_preset(
    preset_name: str,
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """チームプリセットからチームを作成（エージェントも自動作成）"""
    try:
        team_preset = PresetService.get_team_preset_by_name(preset_name)
        
        # プリセットに含まれるエージェントを作成
        agent_ids = []
        for agent_name in team_preset.agents:
            agent_preset = PresetService.get_agent_preset_by_name(agent_name)
            agent_data = schemas.AgentCreate(
                name=agent_preset.name,
                role=agent_preset.role,
                system_prompt=agent_preset.system_prompt
            )
            agent = await AgentService.create_agent(db, agent_data)
            agent_ids.append(agent.id)
        
        # チームを作成
        team_data = schemas.TeamCreate(
            name=team_preset.name,
            description=team_preset.description,
            project_id=project_id,
            agent_ids=agent_ids
        )
        return await TeamService.create_team(db, team_data)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )