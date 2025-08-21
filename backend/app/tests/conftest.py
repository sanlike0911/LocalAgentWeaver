import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from ..main import app
from ..core.database import get_db, Base
from ..models.user import User
from ..models.project import Project
from ..models.team import Team, Agent
from ..models.document import Document, DocumentChunk
from ..core.security import get_password_hash, create_access_token
from datetime import datetime
import tempfile
import os

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def client():
    Base.metadata.create_all(bind=engine)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session):
    """テスト用ユーザーを作成"""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """認証ヘッダーを作成"""
    access_token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def sample_project(db_session, test_user):
    """テスト用プロジェクトを作成"""
    project = Project(
        name="テストプロジェクト",
        description="テスト用のプロジェクトです",
        owner_id=test_user.id
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def sample_agent(db_session):
    """テスト用エージェントを作成"""
    agent = Agent(
        name="テストエージェント",
        role="プログラミング専門家",
        system_prompt="あなたはプログラミングの専門家です。"
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent


@pytest.fixture
def sample_team(db_session, sample_project):
    """テスト用チームを作成"""
    team = Team(
        name="開発チーム",
        description="ソフトウェア開発チーム",
        project_id=sample_project.id
    )
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)
    return team


@pytest.fixture
def sample_team_with_agents(db_session, sample_project, sample_agent):
    """エージェント付きのテスト用チームを作成"""
    team = Team(
        name="技術チーム",
        description="技術的な質問に答えるチーム",
        project_id=sample_project.id
    )
    team.agents = [sample_agent]
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)
    return team


@pytest.fixture
def sample_document(db_session, sample_project):
    """テスト用ドキュメントを作成"""
    # 一時ファイルを作成
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("これはテストドキュメントです。")
        temp_path = f.name

    document = Document(
        filename="test_doc.txt",
        original_filename="test.txt",
        file_path=temp_path,
        file_size=100,
        mime_type="text/plain",
        project_id=sample_project.id,
        is_active=True,
        processed=True
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    
    # テスト完了後にファイルを削除
    yield document
    
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def sample_document_with_chunks(db_session, sample_project):
    """チャンク付きのテスト用ドキュメントを作成"""
    # 一時ファイルを作成
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("LocalAgentWeaverはローカル環境で動作するAIエージェントプラットフォームです。")
        temp_path = f.name

    document = Document(
        filename="detailed_doc.txt",
        original_filename="detailed.txt",
        file_path=temp_path,
        file_size=200,
        mime_type="text/plain",
        project_id=sample_project.id,
        is_active=True,
        processed=True
    )
    db_session.add(document)
    db_session.flush()

    # ドキュメントチャンクを作成
    chunk1 = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        content="LocalAgentWeaverはローカル環境で動作するAIエージェントプラットフォームです。"
    )
    chunk2 = DocumentChunk(
        document_id=document.id,
        chunk_index=1,
        content="セキュアなドキュメント管理とRAG機能を提供します。"
    )
    
    db_session.add(chunk1)
    db_session.add(chunk2)
    db_session.commit()
    db_session.refresh(document)
    
    # テスト完了後にファイルを削除
    yield document
    
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass