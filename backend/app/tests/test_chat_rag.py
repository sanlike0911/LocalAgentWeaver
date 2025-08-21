import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch
from app.models.user import User
from app.models.project import Project
from app.models.team import Team, Agent
from app.models.document import Document, DocumentChunk


class TestRAGChat:
    """RAG機能付きチャットのテストクラス"""

    @pytest.mark.asyncio
    async def test_rag_chat_without_documents(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_project: Project,
    ):
        """ドキュメントなしでのRAGチャットテスト"""
        chat_data = {
            "message": "LocalAgentWeaverについて教えて",
            "project_id": sample_project.id,
            "provider": "ollama",
            "model": "llama3"
        }

        with patch('app.features.chat.service.ChatService.send_message_to_llm') as mock_llm:
            mock_llm.return_value = {
                "message": "申し訳ございませんが、参照ドキュメントが見つかりません。",
                "provider": "ollama",
                "model": "llama3",
                "usage": {}
            }

            response = await client.post(
                "/api/chat/send-rag",
                json=chat_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert data["provider"] == "ollama"

    @pytest.mark.asyncio
    async def test_rag_chat_with_documents(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_project: Project,
        sample_document_with_chunks: Document,
    ):
        """ドキュメントありでのRAGチャットテスト"""
        chat_data = {
            "message": "プロジェクトの概要を教えて",
            "project_id": sample_project.id,
            "provider": "ollama",
            "model": "llama3"
        }

        with patch('app.features.chat.service.ChatService.send_message_to_llm') as mock_llm:
            mock_llm.return_value = {
                "message": "参照ドキュメントによると、LocalAgentWeaverは...",
                "provider": "ollama",
                "model": "llama3",
                "usage": {}
            }

            response = await client.post(
                "/api/chat/send-rag",
                json=chat_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            
            # LLMサービスが適切に呼ばれたことを確認
            mock_llm.assert_called_once()
            call_args = mock_llm.call_args[0][0]
            assert "【参照ドキュメント】" in call_args.message

    @pytest.mark.asyncio
    async def test_rag_chat_with_team(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_project: Project,
        sample_team_with_agents: Team,
    ):
        """チーム情報を含むRAGチャットテスト"""
        chat_data = {
            "message": "技術的な質問があります",
            "project_id": sample_project.id,
            "team_id": sample_team_with_agents.id,
            "provider": "ollama",
            "model": "llama3"
        }

        with patch('app.features.chat.service.ChatService.send_message_to_llm') as mock_llm:
            mock_llm.return_value = {
                "message": "技術チームとして回答いたします...",
                "provider": "ollama",
                "model": "llama3",
                "usage": {}
            }

            response = await client.post(
                "/api/chat/send-rag",
                json=chat_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            
            # チーム情報が含まれていることを確認
            call_args = mock_llm.call_args[0][0]
            assert "【チーム情報】" in call_args.message
            assert sample_team_with_agents.name in call_args.message

    @pytest.mark.asyncio
    async def test_rag_chat_with_documents_and_team(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_project: Project,
        sample_team_with_agents: Team,
        sample_document_with_chunks: Document,
    ):
        """ドキュメントとチーム情報の両方を含むRAGチャットテスト"""
        chat_data = {
            "message": "プロジェクトの技術スタックについて詳しく教えて",
            "project_id": sample_project.id,
            "team_id": sample_team_with_agents.id,
            "provider": "lm_studio",
            "model": "codellama"
        }

        with patch('app.features.chat.service.ChatService.send_message_to_llm') as mock_llm:
            mock_llm.return_value = {
                "message": "技術スタックについて、参考ドキュメントと専門チームの知識を基に回答します...",
                "provider": "lm_studio",
                "model": "codellama",
                "usage": {"total_tokens": 150, "prompt_tokens": 100, "completion_tokens": 50}
            }

            response = await client.post(
                "/api/chat/send-rag",
                json=chat_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert data["provider"] == "lm_studio"
            assert data["model"] == "codellama"
            
            # 両方のコンテキストが含まれていることを確認
            call_args = mock_llm.call_args[0][0]
            assert "【チーム情報】" in call_args.message
            assert "【参照ドキュメント】" in call_args.message

    @pytest.mark.asyncio
    async def test_rag_chat_llm_error(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_project: Project,
    ):
        """LLMエラー時のRAGチャットテスト"""
        chat_data = {
            "message": "テスト質問",
            "project_id": sample_project.id,
            "provider": "ollama",
            "model": "llama3"
        }

        with patch('app.features.chat.service.ChatService.send_message_to_llm') as mock_llm:
            mock_llm.side_effect = Exception("LLM connection failed")

            response = await client.post(
                "/api/chat/send-rag",
                json=chat_data,
                headers=auth_headers
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "RAGチャット処理エラー" in data["detail"]

    @pytest.mark.asyncio
    async def test_rag_chat_invalid_project(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
    ):
        """存在しないプロジェクトでのRAGチャットエラーテスト"""
        chat_data = {
            "message": "テスト質問",
            "project_id": 99999,  # 存在しないプロジェクトID
            "provider": "ollama",
            "model": "llama3"
        }

        response = await client.post(
            "/api/chat/send-rag",
            json=chat_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_rag_chat_invalid_team(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_project: Project,
    ):
        """存在しないチームを指定したRAGチャットテスト"""
        chat_data = {
            "message": "テスト質問",
            "project_id": sample_project.id,
            "team_id": 99999,  # 存在しないチームID
            "provider": "ollama",
            "model": "llama3"
        }

        with patch('app.features.chat.service.ChatService.send_message_to_llm') as mock_llm:
            mock_llm.return_value = {
                "message": "回答内容",
                "provider": "ollama",
                "model": "llama3",
                "usage": {}
            }

            response = await client.post(
                "/api/chat/send-rag",
                json=chat_data,
                headers=auth_headers
            )
            
            # チームが存在しなくても処理は継続される（チーム情報なしで実行）
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_prompt_construction_with_multiple_chunks(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_project: Project,
    ):
        """複数チャンクでのプロンプト構築テスト"""
        # 複数のドキュメントチャンクを含むケース
        chat_data = {
            "message": "詳細な情報を教えて",
            "project_id": sample_project.id,
            "provider": "ollama",
            "model": "llama3"
        }

        # 複数のアクティブなドキュメントチャンクをモック
        with patch('app.features.documents.service.DocumentService.get_active_documents_content') as mock_docs:
            mock_docs.return_value = [
                "第1章: システム概要 - LocalAgentWeaverは...",
                "第2章: アーキテクチャ - システムは3層構造で...",
                "第3章: 機能説明 - 主な機能として..."
            ]
            
            with patch('app.features.chat.service.ChatService.send_message_to_llm') as mock_llm:
                mock_llm.return_value = {
                    "message": "複数の文書を参照して回答します...",
                    "provider": "ollama",
                    "model": "llama3",
                    "usage": {}
                }

                response = await client.post(
                    "/api/chat/send-rag",
                    json=chat_data,
                    headers=auth_headers
                )
                
                assert response.status_code == 200
                
                # 複数の文書が参照されていることを確認
                call_args = mock_llm.call_args[0][0]
                assert "[文書1]" in call_args.message
                assert "[文書2]" in call_args.message
                assert "[文書3]" in call_args.message