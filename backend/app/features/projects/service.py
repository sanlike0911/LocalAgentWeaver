from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import HTTPException, status
from app.models.project import Project
from app.models.user import User
from app.features.projects.schemas import ProjectCreate, ProjectUpdate


class ProjectService:
    @staticmethod
    async def create_project(db: AsyncSession, project_data: ProjectCreate, user: User):
        db_project = Project(
            name=project_data.name,
            description=project_data.description,
            owner_id=user.id
        )
        
        db.add(db_project)
        await db.commit()
        await db.refresh(db_project)
        
        return db_project
    
    @staticmethod
    async def get_user_projects(db: AsyncSession, user: User):
        result = await db.execute(
            select(Project).where(Project.owner_id == user.id).order_by(Project.updated_at.desc())
        )
        projects = result.scalars().all()
        return {"projects": projects, "total": len(projects)}
    
    @staticmethod
    async def get_project_by_id(db: AsyncSession, project_id: int, user: User):
        result = await db.execute(
            select(Project).where(
                Project.id == project_id,
                Project.owner_id == user.id
            )
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return project
    
    @staticmethod
    async def update_project(db: AsyncSession, project_id: int, project_data: ProjectUpdate, user: User):
        project = await ProjectService.get_project_by_id(db, project_id, user)
        
        update_data = project_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)
        
        await db.commit()
        await db.refresh(project)
        
        return project
    
    @staticmethod
    async def delete_project(db: AsyncSession, project_id: int, user: User):
        project = await ProjectService.get_project_by_id(db, project_id, user)
        
        await db.execute(delete(Project).where(Project.id == project_id))
        await db.commit()
        
        return {"message": "Project deleted successfully"}