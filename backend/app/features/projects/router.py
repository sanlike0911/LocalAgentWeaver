from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.features.auth.dependencies import get_current_user
from app.features.projects.schemas import Project, ProjectCreate, ProjectUpdate, ProjectList, ChunkingConfigUpdate
from app.features.projects.service import ProjectService
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new project"""
    return await ProjectService.create_project(db, project_data, current_user)


@router.get("/", response_model=ProjectList)
async def get_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all projects for the current user"""
    return await ProjectService.get_user_projects(db, current_user)


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific project by ID"""
    return await ProjectService.get_project_by_id(db, project_id, current_user)


@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a project"""
    return await ProjectService.update_project(db, project_id, project_data, current_user)


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a project"""
    return await ProjectService.delete_project(db, project_id, current_user)


@router.put("/{project_id}/chunking-config", response_model=Project)
async def update_chunking_config(
    project_id: int,
    config_data: ChunkingConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update project's chunking configuration"""
    return await ProjectService.update_chunking_config(db, project_id, config_data, current_user)


@router.get("/chunking/strategies")
async def get_chunking_strategies():
    """Get available chunking strategies and recommendations"""
    return await ProjectService.get_chunking_strategies()


@router.get("/{project_id}/chunking/analyze")
async def analyze_project_content(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze project content and suggest optimal chunking strategy"""
    return await ProjectService.analyze_project_content(db, project_id, current_user)