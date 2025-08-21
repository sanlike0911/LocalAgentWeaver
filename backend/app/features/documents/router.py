from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.features.auth.dependencies import get_current_user
from app.models.user import User
from . import schemas
from .service import DocumentService

router = APIRouter()


@router.post("/projects/{project_id}/documents/upload", 
            response_model=schemas.DocumentUploadResponse, 
            status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = await DocumentService.upload_document(db, project_id, file)
    
    return schemas.DocumentUploadResponse(
        id=document.id,
        filename=document.filename,
        original_filename=document.original_filename,
        file_size=document.file_size,
        mime_type=document.mime_type,
        message="ファイルのアップロードが完了しました。バックグラウンドで処理中です。"
    )


@router.get("/projects/{project_id}/documents", response_model=List[schemas.Document])
async def get_documents_by_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await DocumentService.get_documents_by_project(db, project_id)


@router.get("/documents/{document_id}", response_model=schemas.Document)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = await DocumentService.get_document(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ドキュメントが見つかりません"
        )
    return document


@router.put("/documents/{document_id}", response_model=schemas.Document)
async def update_document(
    document_id: int,
    document_data: schemas.DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await DocumentService.update_document(db, document_id, document_data)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = await DocumentService.delete_document(db, document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ドキュメントが見つかりません"
        )


@router.get("/projects/{project_id}/documents/status", 
           response_model=List[schemas.DocumentProcessingStatus])
async def get_processing_status(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await DocumentService.get_processing_status(db, project_id)