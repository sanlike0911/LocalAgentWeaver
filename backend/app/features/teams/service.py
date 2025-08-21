from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.models.team import Team, Agent
from app.models.project import Project
from . import schemas
from fastapi import HTTPException, status


class TeamService:
    @staticmethod
    async def create_team(db: AsyncSession, team_data: schemas.TeamCreate) -> Team:
        # プロジェクトの存在確認
        project_result = await db.execute(select(Project).where(Project.id == team_data.project_id))
        project = project_result.scalar_one_or_none()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # 新しいチームを作成
        db_team = Team(
            name=team_data.name,
            description=team_data.description,
            project_id=team_data.project_id
        )

        # エージェントが指定されている場合は関連付け
        if team_data.agent_ids:
            agent_result = await db.execute(
                select(Agent).where(Agent.id.in_(team_data.agent_ids))
            )
            agents = agent_result.scalars().all()
            db_team.agents = list(agents)

        db.add(db_team)
        await db.commit()
        await db.refresh(db_team)
        
        # エージェントも含めて返す
        result = await db.execute(
            select(Team).options(selectinload(Team.agents)).where(Team.id == db_team.id)
        )
        return result.scalar_one()

    @staticmethod
    async def get_teams_by_project(db: AsyncSession, project_id: int) -> List[Team]:
        result = await db.execute(
            select(Team)
            .options(selectinload(Team.agents))
            .where(Team.project_id == project_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_team(db: AsyncSession, team_id: int) -> Optional[Team]:
        result = await db.execute(
            select(Team)
            .options(selectinload(Team.agents))
            .where(Team.id == team_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_team(db: AsyncSession, team_id: int, team_data: schemas.TeamUpdate) -> Team:
        result = await db.execute(
            select(Team)
            .options(selectinload(Team.agents))
            .where(Team.id == team_id)
        )
        db_team = result.scalar_one_or_none()
        if not db_team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )

        # チーム情報の更新
        if team_data.name is not None:
            db_team.name = team_data.name
        if team_data.description is not None:
            db_team.description = team_data.description

        # エージェントの関連付けを更新
        if team_data.agent_ids is not None:
            agent_result = await db.execute(
                select(Agent).where(Agent.id.in_(team_data.agent_ids))
            )
            agents = agent_result.scalars().all()
            db_team.agents = list(agents)

        await db.commit()
        await db.refresh(db_team)
        
        # 更新されたチームを再取得
        result = await db.execute(
            select(Team)
            .options(selectinload(Team.agents))
            .where(Team.id == team_id)
        )
        return result.scalar_one()

    @staticmethod
    async def delete_team(db: AsyncSession, team_id: int) -> bool:
        result = await db.execute(select(Team).where(Team.id == team_id))
        db_team = result.scalar_one_or_none()
        if not db_team:
            return False

        await db.delete(db_team)
        await db.commit()
        return True


class AgentService:
    @staticmethod
    async def create_agent(db: AsyncSession, agent_data: schemas.AgentCreate) -> Agent:
        db_agent = Agent(
            name=agent_data.name,
            role=agent_data.role,
            system_prompt=agent_data.system_prompt
        )
        db.add(db_agent)
        await db.commit()
        await db.refresh(db_agent)
        return db_agent

    @staticmethod
    async def get_all_agents(db: AsyncSession) -> List[Agent]:
        result = await db.execute(select(Agent))
        return list(result.scalars().all())

    @staticmethod
    async def get_agent(db: AsyncSession, agent_id: int) -> Optional[Agent]:
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_agent(db: AsyncSession, agent_id: int, agent_data: schemas.AgentUpdate) -> Agent:
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        db_agent = result.scalar_one_or_none()
        if not db_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )

        if agent_data.name is not None:
            db_agent.name = agent_data.name
        if agent_data.role is not None:
            db_agent.role = agent_data.role
        if agent_data.system_prompt is not None:
            db_agent.system_prompt = agent_data.system_prompt

        await db.commit()
        await db.refresh(db_agent)
        return db_agent

    @staticmethod
    async def delete_agent(db: AsyncSession, agent_id: int) -> bool:
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        db_agent = result.scalar_one_or_none()
        if not db_agent:
            return False

        await db.delete(db_agent)
        await db.commit()
        return True