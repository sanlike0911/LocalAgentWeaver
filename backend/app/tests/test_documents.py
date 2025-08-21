import pytest
import io
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.project import Project
from app.models.document import Document
from unittest.mock import patch


class TestDocumentManagement:
    """ドキュメント管理機能のテストクラス"""

    @pytest.mark.asyncio
    async def test_upload_document_text(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_project: Project,
    ):
        """テキストファイルアップロードのテスト"""
        # テストファイルを作成
        file_content = "これはテストドキュメントです。\nLocalAgentWeaverのテスト用文書です。"
        file_data = ("test.txt", io.BytesIO(file_content.encode()), "text/plain")

        response = await client.post(
            f"/api/projects/{sample_project.id}/documents/upload",
            files={"file": file_data},
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["original_filename"] == "test.txt"
        assert data["mime_type"] == "text/plain"
        assert data["file_size"] == len(file_content.encode())
        assert "ファイルのアップロードが完了しました" in data["message"]

    @pytest.mark.asyncio
    async def test_upload_document_invalid_extension(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_project: Project,
    ):
        """無効な拡張子のファイルアップロードエラーテスト"""
        file_content = "invalid file content"
        file_data = ("test.exe", io.BytesIO(file_content.encode()), "application/octet-stream")

        response = await client.post(
            f"/api/projects/{sample_project.id}/documents/upload",
            files={"file": file_data},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "サポートされていないファイル形式" in data["detail"]

    @pytest.mark.asyncio
    async def test_upload_document_too_large(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_project: Project,
    ):
        """ファイルサイズ上限超過のテスト"""
        # 31MBのファイルを模擬
        large_content = "x" * (31 * 1024 * 1024)
        file_data = ("large.txt", io.BytesIO(large_content.encode()), "text/plain")

        response = await client.post(
            f"/api/projects/{sample_project.id}/documents/upload",
            files={"file": file_data},
            headers=auth_headers
        )
        
        assert response.status_code == 413
        data = response.json()
        assert "ファイルサイズが上限" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_documents_by_project(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_project: Project,
        sample_document: Document,
    ):
        """プロジェクト別ドキュメント一覧取得のテスト"""
        response = await client.get(
            f"/api/projects/{sample_project.id}/documents",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(doc["id"] == sample_document.id for doc in data)

    @pytest.mark.asyncio
    async def test_get_document_by_id(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_document: Document,
    ):
        """ドキュメント詳細取得のテスト"""
        response = await client.get(
            f"/api/documents/{sample_document.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_document.id
        assert data["original_filename"] == sample_document.original_filename

    @pytest.mark.asyncio
    async def test_update_document_status(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_document: Document,
    ):
        """ドキュメントステータス更新のテスト"""
        update_data = {"is_active": False}

        response = await client.put(
            f"/api/documents/{sample_document.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == False

    @pytest.mark.asyncio
    async def test_delete_document(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_document: Document,
    ):
        """ドキュメント削除のテスト"""
        response = await client.delete(
            f"/api/documents/{sample_document.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204

        # 削除確認
        response = await client.get(
            f"/api/documents/{sample_document.id}",
            headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_processing_status(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_project: Project,
        sample_document: Document,
    ):
        """ドキュメント処理状況取得のテスト"""
        response = await client.get(
            f"/api/projects/{sample_project.id}/documents/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        status = next((s for s in data if s["document_id"] == sample_document.id), None)
        assert status is not None
        assert status["filename"] == sample_document.original_filename
        assert "processed" in status

    @pytest.mark.asyncio
    async def test_upload_markdown_document(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        sample_project: Project,
    ):
        """Markdownファイルアップロードのテスト"""
        file_content = """# テストドキュメント
        
## 概要
これはテスト用のMarkdownドキュメントです。

## 詳細
LocalAgentWeaverの機能テスト用の文書として使用されます。

### 機能一覧
- ドキュメントアップロード
- RAG機能
- チーム管理
"""
        file_data = ("test.md", io.BytesIO(file_content.encode()), "text/markdown")

        response = await client.post(
            f"/api/projects/{sample_project.id}/documents/upload",
            files={"file": file_data},
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["original_filename"] == "test.md"
        assert data["mime_type"] == "text/markdown"

    @pytest.mark.asyncio
    async def test_upload_to_nonexistent_project(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
    ):
        """存在しないプロジェクトへのファイルアップロードエラーテスト"""
        file_content = "test content"
        file_data = ("test.txt", io.BytesIO(file_content.encode()), "text/plain")

        response = await client.post(
            "/api/projects/99999/documents/upload",  # 存在しないプロジェクトID
            files={"file": file_data},
            headers=auth_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "プロジェクトが見つかりません" in data["detail"]