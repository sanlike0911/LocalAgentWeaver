import os
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path

from sqlalchemy import select

# LlamaIndex imports - optional for now
try:
    from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings
    from llama_index.llms.ollama import Ollama
    from llama_index.embeddings.ollama import OllamaEmbedding
    from llama_index.vector_stores.lancedb import LanceDBVectorStore
    from llama_index.core.node_parser import SentenceSplitter
    import lancedb
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.document import Document
from app.features.documents.utils import DocumentProcessor


class LlamaIndexRAGService:
    """
    RAG service using LlamaIndex with LanceDB vector store.
    Provides methods for building/updating indices and querying them.
    """
    
    @staticmethod
    def get_project_store_dir(project_id: int) -> Path:
        """
        Get the directory path for a project's vector store.
        
        Args:
            project_id: The ID of the project
            
        Returns:
            Path object for the project's vector store directory
        """
        base_dir = Path(settings.LANCE_DB_DIR)
        return base_dir / f"project_{project_id}"
    
    @staticmethod
    def build_or_update_index(project_id: int) -> None:
        """
        Build or update the vector index for a project.
        
        Args:
            project_id: The ID of the project to build/update the index for
        """
        if not LLAMAINDEX_AVAILABLE:
            print(f"LlamaIndex not available - skipping index build for project {project_id}")
            return
        # Create base directory if it doesn't exist
        base_dir = Path(settings.LANCE_DB_DIR)
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Get project directory
        project_dir = LlamaIndexRAGService.get_project_store_dir(project_id)
        
        # If directory exists, remove it for a clean rebuild
        if project_dir.exists():
            shutil.rmtree(project_dir)
        
        # Create project directory
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Get all active documents for the project
        # Use synchronous database access since this method runs in a thread
        files = []
        try:
            # Create synchronous session from async engine
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            
            # Create synchronous engine from async engine URL
            sync_url = str(AsyncSessionLocal.bind.url).replace('+asyncpg', '')
            sync_engine = create_engine(sync_url)
            SyncSessionLocal = sessionmaker(bind=sync_engine)
            
            with SyncSessionLocal() as session:
                # Get all active and processed documents
                result = session.execute(
                    select(Document.file_path).where(
                        Document.project_id == project_id,
                        Document.is_active == True,
                        Document.processed == True
                    )
                )
                
                # Collect file paths that exist
                for row in result:
                    file_path = row[0]
                    if os.path.exists(file_path):
                        files.append(file_path)
        except Exception as e:
            print(f"Error fetching documents for project {project_id}: {str(e)}")
            raise
        
        # If no files, return early
        if not files:
            return
        
        try:
            # Load documents using enhanced DocumentProcessor
            docs = DocumentProcessor.create_llamaindex_documents(
                files, 
                metadata={"project_id": project_id}
            )
            if not docs:
                return
            
            # Initialize LanceDB connection
            db = lancedb.connect(str(project_dir))
            
            # Configure models and node parser
            Settings.embed_model = OllamaEmbedding(
                model=settings.OLLAMA_EMBEDDING_MODEL,
                base_url=settings.OLLAMA_BASE_URL
            )
            
            # Configure intelligent chunking with SentenceSplitter
            Settings.node_parser = SentenceSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
                separator=" ",
                paragraph_separator=settings.PARAGRAPH_SEPARATOR,
                secondary_chunking_regex="[^,.;。！？]+[,.;。！？]?",
            )
            
            # Create vector store
            vector_store = LanceDBVectorStore(db=db, table_name="index")
            
            # Create index with optimized settings
            VectorStoreIndex.from_documents(
                docs,
                storage_context=StorageContext.from_defaults(vector_store=vector_store),
                show_progress=True
            )
            
            # Persistence is implicit in LanceDB
            
        except Exception as e:
            # Clean up on failure
            if project_dir.exists():
                shutil.rmtree(project_dir, ignore_errors=True)
            print(f"Error building index for project {project_id}: {str(e)}")
            raise
    
    @staticmethod
    def query(project_id: int, question: str, model_name: str) -> str:
        """
        Query the vector index for a project.
        
        Args:
            project_id: The ID of the project to query
            question: The query string
            model_name: The name of the LLM model to use
            
        Returns:
            String response from the LLM
        """
        if not LLAMAINDEX_AVAILABLE:
            return "LlamaIndex機能は現在利用できません。"
        # Get project directory
        project_dir = LlamaIndexRAGService.get_project_store_dir(project_id)
        
        # Check if project directory exists
        if not project_dir.exists():
            return "このプロジェクトにはインデックスがありません。"
        
        # Initialize LanceDB connection
        db = lancedb.connect(str(project_dir))
        
        # Check if index exists
        if "index" not in db.table_names():
            return "関連ドキュメントがありません。"
        
        try:
            # Create vector store
            vector_store = LanceDBVectorStore(db=db, table_name="index")
            
            # Configure models
            Settings.embed_model = OllamaEmbedding(
                model=settings.OLLAMA_EMBEDDING_MODEL,
                base_url=settings.OLLAMA_BASE_URL
            )
            
            Settings.llm = Ollama(
                model=model_name,
                base_url=settings.OLLAMA_BASE_URL
            )
            
            # Load index from vector store
            index = VectorStoreIndex.from_vector_store(vector_store)
            
            # Create query engine
            query_engine = index.as_query_engine(similarity_top_k=5)
            
            # Run query
            response = query_engine.query(question)
            
            # Return response as string
            return str(response.response)
            
        except Exception as e:
            print(f"Error querying index for project {project_id}: {str(e)}")
            return f"検索エラーが発生しました: {str(e)}"
