from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import HTTPException, status
from pathlib import Path
from app.models.project import Project
from app.models.user import User
from app.features.projects.schemas import ProjectCreate, ProjectUpdate, ChunkingConfigUpdate
from app.features.documents.utils import DocumentProcessor


class ProjectService:
    @staticmethod
    async def create_project(db: AsyncSession, project_data: ProjectCreate, user: User):
        db_project = Project(
            name=project_data.name,
            description=project_data.description,
            chunking_strategy=project_data.chunking_strategy,
            chunking_config=project_data.chunking_config,
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
    
    @staticmethod
    async def update_chunking_config(
        db: AsyncSession, 
        project_id: int, 
        config_data: ChunkingConfigUpdate, 
        user: User
    ):
        """Update project's chunking configuration"""
        project = await ProjectService.get_project_by_id(db, project_id, user)
        
        # Validate chunking strategy
        available_strategies = list(DocumentProcessor.CHUNK_STRATEGIES.keys())
        if config_data.chunking_strategy not in available_strategies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid chunking strategy. Available strategies: {available_strategies}"
            )
        
        project.chunking_strategy = config_data.chunking_strategy
        project.chunking_config = config_data.chunking_config
        
        await db.commit()
        await db.refresh(project)
        
        return project
    
    @staticmethod
    async def get_chunking_strategies():
        """Get available chunking strategies and their configurations"""
        return {
            "strategies": DocumentProcessor.CHUNK_STRATEGIES,
            "recommendations": {
                "research": "semantic",
                "legal": "sentence", 
                "technical": "recursive",
                "code": "token",
                "general": "sentence"
            }
        }
    
    @staticmethod
    async def analyze_project_content(db: AsyncSession, project_id: int, user: User):
        """Analyze project content and suggest optimal chunking strategy"""
        project = await ProjectService.get_project_by_id(db, project_id, user)
        
        # Get project documents for analysis
        from app.models.document import Document
        result = await db.execute(
            select(Document.mime_type, Document.file_path)
            .where(Document.project_id == project_id)
        )
        documents = result.all()
        
        if not documents:
            return {
                "suggested_strategy": "sentence",
                "confidence": 0.5,
                "reason": "No documents to analyze, using safe default"
            }
        
        # Extract file types
        file_types = [Path(doc.file_path).suffix.lower() for doc in documents]
        
        # Suggest strategy based on content analysis
        suggested_strategy = DocumentProcessor.get_optimal_chunking_strategy(
            project_type=project.description,
            file_types=file_types
        )
        
        # Calculate confidence based on file type uniformity
        most_common_type = max(set(file_types), key=file_types.count)
        uniformity = file_types.count(most_common_type) / len(file_types)
        confidence = min(0.9, 0.5 + uniformity * 0.4)
        
        return {
            "suggested_strategy": suggested_strategy,
            "confidence": confidence,
            "file_analysis": {
                "total_files": len(documents),
                "file_types": list(set(file_types)),
                "most_common_type": most_common_type
            },
            "reason": f"Based on project type '{project.description or 'general'}' and file types {list(set(file_types))}"
        }