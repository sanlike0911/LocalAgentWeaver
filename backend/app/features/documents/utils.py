import os
import uuid
import mimetypes
from pathlib import Path
from typing import List
from fastapi import UploadFile, HTTPException, status


class DocumentProcessor:
    ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.md', '.docx'}
    MAX_FILE_SIZE = 30 * 1024 * 1024  # 30MB
    UPLOAD_DIR = "uploads"

    @classmethod
    def validate_file(cls, file: UploadFile) -> None:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ファイル名が指定されていません"
            )

        # ファイル拡張子の確認
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in cls.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"サポートされていないファイル形式です。許可される拡張子: {', '.join(cls.ALLOWED_EXTENSIONS)}"
            )

        # ファイルサイズの確認 (content-lengthが利用可能な場合)
        if hasattr(file, 'size') and file.size and file.size > cls.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"ファイルサイズが上限（{cls.MAX_FILE_SIZE // (1024*1024)}MB）を超えています"
            )

    @classmethod
    async def save_file(cls, file: UploadFile) -> tuple[str, str, int]:
        # アップロードディレクトリの確保
        upload_path = Path(cls.UPLOAD_DIR)
        upload_path.mkdir(parents=True, exist_ok=True)

        # 一意なファイル名の生成
        file_extension = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_path / unique_filename

        # ファイルの保存とサイズ測定
        file_size = 0
        try:
            with open(file_path, "wb") as buffer:
                content = await file.read()
                file_size = len(content)
                
                # サイズ再確認
                if file_size > cls.MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"ファイルサイズが上限（{cls.MAX_FILE_SIZE // (1024*1024)}MB）を超えています"
                    )
                
                buffer.write(content)
        except Exception as e:
            # エラー時はファイルを削除
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"ファイルの保存中にエラーが発生しました: {str(e)}"
            )

        return str(file_path), unique_filename, file_size

    @classmethod
    def get_mime_type(cls, filename: str) -> str:
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'

    @classmethod
    def delete_file(cls, file_path: str) -> None:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass  # ファイル削除エラーは無視

    @classmethod
    def read_text_content(cls, file_path: str, mime_type: str) -> str:
        try:
            if mime_type in ['text/plain', 'text/markdown']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif mime_type == 'application/pdf':
                return cls._extract_pdf_text(file_path)
            else:
                raise ValueError(f"サポートされていないMIMEタイプ: {mime_type}")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"ファイルの内容読み取りエラー: {str(e)}"
            )

    @classmethod
    def _extract_pdf_text(cls, file_path: str) -> str:
        # PDF処理は今回の実装では簡略化
        # 実際の実装では pypdf や pdfplumber などのライブラリを使用
        return "PDFテキスト抽出は未実装です。"

    @classmethod
    def chunk_text(cls, content: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        if not content.strip():
            return []

        chunks = []
        start = 0
        content_length = len(content)

        while start < content_length:
            end = min(start + chunk_size, content_length)
            
            # 文の区切りを探す
            if end < content_length:
                # 改行、句読点で区切る
                for delimiter in ['\n\n', '\n', '。', '.']:
                    last_delimiter = content.rfind(delimiter, start, end)
                    if last_delimiter > start:
                        end = last_delimiter + len(delimiter)
                        break

            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = max(start + 1, end - overlap)

        return chunks