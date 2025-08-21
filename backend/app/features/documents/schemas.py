from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DocumentChunk(BaseModel):
    id: int
    chunk_index: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    filename: str
    is_active: bool = True


class DocumentCreate(BaseModel):
    project_id: int


class DocumentUpdate(BaseModel):
    is_active: Optional[bool] = None


class Document(DocumentBase):
    id: int
    original_filename: str
    file_size: int
    mime_type: str
    project_id: int
    processed: bool
    chunks: List[DocumentChunk] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentProcessingStatus(BaseModel):
    document_id: int
    filename: str
    processed: bool
    chunk_count: int
    file_size: int
    created_at: datetime


class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    message: str