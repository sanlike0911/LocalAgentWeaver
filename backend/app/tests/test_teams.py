import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.project import Project
from app.models.team import Team, Agent


class TestTeamManagement:
    """チーム管理機能のテストクラス"""

    @pytest.mark.asyncio
    async def test_create_agent(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
    ):
        """エージェント作成のテスト"""
        agent_data = {
            "name": "テストエージェント",
            "role": "プログラミング専門家",
            "system_prompt": "あなたはプログラミングの専門家です。"
        }

        response = await client.post("/api/agents", json=agent_data, headers=auth_headers)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == agent_data["name"]
        assert data["role"] == agent_data["role"]
        assert data["system_prompt"] == agent_data["system_prompt"]
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_get_all_agents(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_agent: Agent,
    ):
        """全エージェント取得のテスト"""
        response = await client.get("/api/agents", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(agent["id"] == sample_agent.id for agent in data)

    @pytest.mark.asyncio
    async def test_get_agent_by_id(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_agent: Agent,
    ):
        """エージェント詳細取得のテスト"""
        response = await client.get(f"/api/agents/{sample_agent.id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == sample_agent.id
        assert data["name"] == sample_agent.name
        assert data["role"] == sample_agent.role

    @pytest.mark.asyncio
    async def test_update_agent(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_agent: Agent,
    ):
        """エージェント更新のテスト"""
        update_data = {
            "name": "更新されたエージェント",
            "role": "更新された役割"
        }

        response = await client.put(
            f"/api/agents/{sample_agent.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["role"] == update_data["role"]

    @pytest.mark.asyncio
    async def test_delete_agent(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_agent: Agent,
    ):
        """エージェント削除のテスト"""
        response = await client.delete(f"/api/agents/{sample_agent.id}", headers=auth_headers)
        assert response.status_code == 204

        # 削除確認
        response = await client.get(f"/api/agents/{sample_agent.id}", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_team(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_project: Project,
        sample_agent: Agent,
    ):
        """チーム作成のテスト"""
        team_data = {
            "name": "開発チーム",
            "description": "ソフトウェア開発を担当するチーム",
            "project_id": sample_project.id,
            "agent_ids": [sample_agent.id]
        }

        response = await client.post("/api/teams", json=team_data, headers=auth_headers)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == team_data["name"]
        assert data["description"] == team_data["description"]
        assert data["project_id"] == sample_project.id
        assert len(data["agents"]) == 1
        assert data["agents"][0]["id"] == sample_agent.id

    @pytest.mark.asyncio
    async def test_get_teams_by_project(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_project: Project,
        sample_team: Team,
    ):
        """プロジェクト別チーム取得のテスト"""
        response = await client.get(
            f"/api/projects/{sample_project.id}/teams",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(team["id"] == sample_team.id for team in data)

    @pytest.mark.asyncio
    async def test_get_team_by_id(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_team: Team,
    ):
        """チーム詳細取得のテスト"""
        response = await client.get(f"/api/teams/{sample_team.id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == sample_team.id
        assert data["name"] == sample_team.name

    @pytest.mark.asyncio
    async def test_update_team(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_team: Team,
        sample_agent: Agent,
    ):
        """チーム更新のテスト"""
        update_data = {
            "name": "更新されたチーム",
            "description": "更新された説明",
            "agent_ids": [sample_agent.id]
        }

        response = await client.put(
            f"/api/teams/{sample_team.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]

    @pytest.mark.asyncio
    async def test_delete_team(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_team: Team,
    ):
        """チーム削除のテスト"""
        response = await client.delete(f"/api/teams/{sample_team.id}", headers=auth_headers)
        assert response.status_code == 204

        # 削除確認
        response = await client.get(f"/api/teams/{sample_team.id}", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_team_without_project_access(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
    ):
        """アクセス権のないプロジェクトでのチーム作成エラーテスト"""
        team_data = {
            "name": "テストチーム",
            "project_id": 99999,  # 存在しないプロジェクトID
            "agent_ids": []
        }

        response = await client.post("/api/teams", json=team_data, headers=auth_headers)
        assert response.status_code == 404
        
        data = response.json()
        assert "Project not found" in data["detail"]


class TestTeamPresets:
    """チーム・エージェントプリセット機能のテストクラス"""

    @pytest.mark.asyncio
    async def test_get_agent_presets(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """エージェントプリセット一覧取得のテスト"""
        response = await client.get("/api/presets/agents", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # 最初のプリセットの構造を確認
        first_preset = data[0]
        assert "name" in first_preset
        assert "role" in first_preset
        assert "system_prompt" in first_preset
        assert "description" in first_preset
        assert "category" in first_preset

    @pytest.mark.asyncio
    async def test_get_agent_presets_by_category(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """カテゴリ別エージェントプリセット取得のテスト"""
        response = await client.get("/api/presets/agents?category=development", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        # developmentカテゴリのプリセットのみが返されることを確認
        for preset in data:
            assert preset["category"] == "development"

    @pytest.mark.asyncio
    async def test_get_team_presets(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """チームプリセット一覧取得のテスト"""
        response = await client.get("/api/presets/teams", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # 最初のプリセットの構造を確認
        first_preset = data[0]
        assert "name" in first_preset
        assert "description" in first_preset
        assert "agents" in first_preset
        assert "category" in first_preset

    @pytest.mark.asyncio
    async def test_get_preset_categories(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """プリセットカテゴリ一覧取得のテスト"""
        response = await client.get("/api/presets/categories", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "agents" in data
        assert "teams" in data
        assert isinstance(data["agents"], list)
        assert isinstance(data["teams"], list)

    @pytest.mark.asyncio
    async def test_instantiate_agent_preset(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
    ):
        """エージェントプリセットからエージェント作成のテスト"""
        preset_name = "シニアデベロッパー"
        response = await client.post(
            f"/api/presets/agents/{preset_name}/instantiate",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == preset_name
        assert "role" in data
        assert "system_prompt" in data
        assert "id" in data

    @pytest.mark.asyncio
    async def test_instantiate_team_preset(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_project: Project,
    ):
        """チームプリセットからチーム作成のテスト"""
        preset_name = "開発チーム"
        response = await client.post(
            f"/api/presets/teams/{preset_name}/instantiate",
            params={"project_id": sample_project.id},
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == preset_name
        assert data["project_id"] == sample_project.id
        assert len(data["agents"]) > 0

    @pytest.mark.asyncio
    async def test_instantiate_nonexistent_agent_preset(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """存在しないエージェントプリセットでのエラーテスト"""
        preset_name = "存在しないプリセット"
        response = await client.post(
            f"/api/presets/agents/{preset_name}/instantiate",
            headers=auth_headers
        )
        assert response.status_code == 404

        data = response.json()
        assert "not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_instantiate_nonexistent_team_preset(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_project: Project,
    ):
        """存在しないチームプリセットでのエラーテスト"""
        preset_name = "存在しないチーム"
        response = await client.post(
            f"/api/presets/teams/{preset_name}/instantiate",
            params={"project_id": sample_project.id},
            headers=auth_headers
        )
        assert response.status_code == 404

        data = response.json()
        assert "not found" in data["detail"]