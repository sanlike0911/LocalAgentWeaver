from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from fastapi import UploadFile, HTTPException, status
from app.models.document import Document, DocumentChunk
from app.models.project import Project
from . import schemas
from .utils import DocumentProcessor
import asyncio


class DocumentService:
    @staticmethod
    async def upload_document(
        db: AsyncSession, 
        project_id: int, 
        file: UploadFile
    ) -> Document:
        # プロジェクトの存在確認
        project_result = await db.execute(select(Project).where(Project.id == project_id))
        project = project_result.scalar_one_or_none()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="プロジェクトが見つかりません"
            )

        # ファイルのバリデーション
        DocumentProcessor.validate_file(file)

        # ファイルの保存
        file_path, unique_filename, file_size = await DocumentProcessor.save_file(file)
        mime_type = DocumentProcessor.get_mime_type(file.filename)

        # データベースに保存
        db_document = Document(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            project_id=project_id,
            is_active=True,
            processed=False
        )

        try:
            db.add(db_document)
            await db.commit()
            await db.refresh(db_document)

            # バックグラウンドでドキュメント処理を開始
            asyncio.create_task(
                DocumentService._process_document_background(db, db_document.id)
            )

            return db_document

        except Exception as e:
            # エラー時はアップロードファイルを削除
            DocumentProcessor.delete_file(file_path)
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"ドキュメントの保存に失敗しました: {str(e)}"
            )

    @staticmethod
    async def _process_document_background(db: AsyncSession, document_id: int):
        try:
            # ドキュメントを取得
            result = await db.execute(select(Document).where(Document.id == document_id))
            document = result.scalar_one_or_none()
            if not document:
                return

            # テキスト内容を抽出
            content = DocumentProcessor.read_text_content(document.file_path, document.mime_type)
            
            # チャンクに分割
            chunks = DocumentProcessor.chunk_text(content)

            # チャンクをデータベースに保存
            for i, chunk_content in enumerate(chunks):
                chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=i,
                    content=chunk_content
                )
                db.add(chunk)

            # ドキュメントを処理済みに更新
            document.processed = True
            await db.commit()

        except Exception as e:
            # エラーログを出力（実際の実装では適切なロガーを使用）
            print(f"ドキュメント処理エラー (ID: {document_id}): {str(e)}")
            await db.rollback()

    @staticmethod
    async def get_documents_by_project(db: AsyncSession, project_id: int) -> List[Document]:
        result = await db.execute(
            select(Document)
            .options(selectinload(Document.chunks))
            .where(Document.project_id == project_id)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_document(db: AsyncSession, document_id: int) -> Optional[Document]:
        result = await db.execute(
            select(Document)
            .options(selectinload(Document.chunks))
            .where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_document(
        db: AsyncSession, 
        document_id: int, 
        document_data: schemas.DocumentUpdate
    ) -> Document:
        result = await db.execute(select(Document).where(Document.id == document_id))
        db_document = result.scalar_one_or_none()
        if not db_document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ドキュメントが見つかりません"
            )

        if document_data.is_active is not None:
            db_document.is_active = document_data.is_active

        await db.commit()
        await db.refresh(db_document)
        return db_document

    @staticmethod
    async def delete_document(db: AsyncSession, document_id: int) -> bool:
        result = await db.execute(select(Document).where(Document.id == document_id))
        db_document = result.scalar_one_or_none()
        if not db_document:
            return False

        # ファイルシステムからファイルを削除
        DocumentProcessor.delete_file(db_document.file_path)

        # データベースから削除
        await db.delete(db_document)
        await db.commit()
        return True

    @staticmethod
    async def get_active_documents_content(db: AsyncSession, project_id: int) -> List[str]:
        """プロジェクトのアクティブなドキュメントのチャンク内容を取得"""
        result = await db.execute(
            select(DocumentChunk)
            .join(Document)
            .where(
                Document.project_id == project_id,
                Document.is_active == True,
                Document.processed == True
            )
            .order_by(Document.id, DocumentChunk.chunk_index)
        )
        
        chunks = result.scalars().all()
        return [chunk.content for chunk in chunks]

    @staticmethod
    async def get_processing_status(db: AsyncSession, project_id: int) -> List[schemas.DocumentProcessingStatus]:
        """プロジェクトのドキュメント処理状況を取得"""
        result = await db.execute(
            select(Document)
            .options(selectinload(Document.chunks))
            .where(Document.project_id == project_id)
            .order_by(Document.created_at.desc())
        )
        documents = result.scalars().all()
        
        status_list = []
        for doc in documents:
            status = schemas.DocumentProcessingStatus(
                document_id=doc.id,
                filename=doc.original_filename,
                processed=doc.processed,
                chunk_count=len(doc.chunks),
                file_size=doc.file_size,
                created_at=doc.created_at
            )
            status_list.append(status)
        
        return status_list