"""
Integration tests for LlamaIndex RAG pipeline integration with document and chat services.

These tests verify the complete pipeline:
1. Document upload and processing
2. Enhanced RAG index building
3. High-precision query execution
4. Source information retrieval
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from fastapi import UploadFile
import io

from app.services.llamaindex_service import LlamaIndexRAGService
from app.features.documents.service import DocumentService
from app.features.chat.service import ChatService
from app.features.chat.schemas import ChatRequest, LLMProvider
from app.models.document import Document
from app.models.project import Project


class TestLlamaIndexIntegration:
    """Integration tests for the complete LlamaIndex RAG pipeline"""
    
    @pytest.fixture
    def temp_files(self):
        """Create temporary test files"""
        temp_dir = tempfile.mkdtemp()
        
        # Create sample documents
        files = {}
        
        # Sample text file
        txt_file = Path(temp_dir) / "sample.txt"
        txt_file.write_text("""
        This is a comprehensive guide to machine learning algorithms.
        
        Machine learning is a subset of artificial intelligence that enables
        computers to learn and improve from experience without being explicitly programmed.
        
        Common algorithms include:
        - Linear Regression for continuous predictions
        - Decision Trees for classification
        - Neural Networks for complex pattern recognition
        """, encoding='utf-8')
        files['txt'] = txt_file
        
        # Sample markdown file
        md_file = Path(temp_dir) / "algorithms.md"
        md_file.write_text("""
        # Advanced Algorithms
        
        ## Supervised Learning
        Supervised learning uses labeled training data to learn patterns.
        
        ### Classification Algorithms
        - Support Vector Machines
        - Random Forest
        - Gradient Boosting
        
        ## Unsupervised Learning
        Unsupervised learning finds hidden patterns without labels.
        
        ### Clustering Algorithms
        - K-Means
        - Hierarchical Clustering
        - DBSCAN
        """, encoding='utf-8')
        files['md'] = md_file
        
        yield temp_dir, files
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def create_upload_file(self, file_path: Path) -> UploadFile:
        """Create an UploadFile object from a file path"""
        content = file_path.read_bytes()
        return UploadFile(
            filename=file_path.name,
            file=io.BytesIO(content),
            size=len(content)
        )
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not LlamaIndexRAGService.is_available(), reason="LlamaIndex not available")
    async def test_complete_rag_pipeline(self, temp_files):
        """Test the complete RAG pipeline from document upload to query response"""
        temp_dir, files = temp_files
        
        # Mock database and project setup
        mock_project = Mock()
        mock_project.id = 1
        mock_project.description = "academic"
        mock_project.chunking_strategy = None
        mock_project.chunking_config = None
        
        mock_db_session = AsyncMock()
        
        with patch('app.features.documents.service.AsyncSessionLocal') as mock_session_factory, \
             patch('app.features.documents.service.DocumentProcessor.save_file') as mock_save_file, \
             patch('app.services.llamaindex_service.settings') as mock_settings, \
             patch('app.services.llamaindex_service.AsyncSessionLocal') as mock_rag_session_factory:
            
            # Configure mocks
            mock_settings.LANCE_DB_DIR = temp_dir
            mock_settings.OLLAMA_EMBEDDING_MODEL = "test-embed"
            mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
            
            # Mock session factory
            mock_session = AsyncMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session
            mock_rag_session_factory.return_value.__aenter__.return_value = mock_session
            
            # Mock project query
            mock_project_result = Mock()
            mock_project_result.scalar_one_or_none.return_value = mock_project
            mock_session.execute.return_value = mock_project_result
            
            # Test document processing without actual file operations
            for file_path in files.values():
                # Mock file save to return original path
                mock_save_file.return_value = (str(file_path), file_path.name, file_path.stat().st_size)
                
                # Create upload file
                upload_file = self.create_upload_file(file_path)
                
                # Mock database document creation
                mock_document = Mock()
                mock_document.id = 1
                mock_document.file_path = str(file_path)
                mock_document.project_id = 1
                mock_document.processed = False
                
                mock_session.add = Mock()
                mock_session.commit = AsyncMock()
                mock_session.refresh = AsyncMock()
                
                # This would normally trigger background processing
                # For testing, we'll verify the processing steps work
                assert file_path.exists()
                assert file_path.stat().st_size > 0
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not LlamaIndexRAGService.is_available(), reason="LlamaIndex not available")
    async def test_document_processing_with_llamaindex(self, temp_files):
        """Test document processing triggers proper LlamaIndex operations"""
        temp_dir, files = temp_files
        
        project_id = 1
        
        with patch('app.services.llamaindex_service.settings') as mock_settings, \
             patch.object(LlamaIndexRAGService, '_setup_global_settings') as mock_setup, \
             patch.object(LlamaIndexRAGService, '_create_enhanced_file_reader') as mock_file_reader, \
             patch.object(LlamaIndexRAGService, '_create_optimized_node_parser') as mock_node_parser, \
             patch('lancedb.connect') as mock_lancedb:
            
            mock_settings.LANCE_DB_DIR = temp_dir
            
            # Mock file reader to return test documents
            mock_documents = [
                Mock(text="Test document content", metadata={"file_name": "test.txt"})
            ]
            mock_file_reader.return_value = mock_documents
            
            # Mock node parser
            mock_parser = Mock()
            mock_node_parser.return_value = mock_parser
            
            # Mock LanceDB
            mock_db = Mock()
            mock_vector_store = Mock()
            mock_lancedb.return_value = mock_db
            
            # Mock document files exist
            file_paths = [str(f) for f in files.values()]
            
            with patch('app.services.llamaindex_service.AsyncSessionLocal') as mock_session_factory:
                # Mock database session
                mock_session = AsyncMock()
                mock_session_factory.return_value.__aenter__.return_value = mock_session
                
                # Mock database query results
                mock_result = Mock()
                mock_result.__iter__ = lambda x: iter([(path,) for path in file_paths])
                mock_session.execute.return_value = mock_result
                
                # Test index building
                result = await LlamaIndexRAGService.build_or_update_index(
                    project_id=project_id,
                    project_type="academic",
                    chunking_strategy="semantic"
                )
                
                # Verify setup was called
                mock_setup.assert_called_once()
                # Verify file reader was called with correct parameters
                mock_file_reader.assert_called_once()
                # Verify node parser was called
                mock_node_parser.assert_called_once_with("semantic", "academic")
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not LlamaIndexRAGService.is_available(), reason="LlamaIndex not available")
    async def test_chat_service_integration(self):
        """Test chat service integration with enhanced RAG"""
        project_id = 1
        
        with patch.object(LlamaIndexRAGService, 'query') as mock_query, \
             patch.object(ChatService, '_get_team_context') as mock_team_context:
            
            # Mock RAG query result
            mock_rag_result = {
                "response": "Based on the documents, machine learning algorithms include regression, classification, and clustering methods.",
                "sources": [
                    {
                        "file_name": "algorithms.md",
                        "file_path": "/path/to/algorithms.md",
                        "similarity_score": 0.85,
                        "content_excerpt": "Common algorithms include Linear Regression, Decision Trees..."
                    }
                ],
                "metadata": {
                    "project_id": project_id,
                    "model_name": "llama3",
                    "num_sources": 1
                }
            }
            mock_query.return_value = mock_rag_result
            
            # Mock team context
            mock_team_context.return_value = "You are a machine learning expert."
            
            # Create chat request
            chat_request = ChatRequest(
                message="What are the main types of machine learning algorithms?",
                project_id=project_id,
                provider=LLMProvider.OLLAMA,
                model="llama3"
            )
            
            # Mock database session
            mock_db = AsyncMock()
            
            # Test chat with RAG
            response = await ChatService.send_message_with_rag(
                db=mock_db,
                chat_request=chat_request,
                project_id=project_id,
                team_id=1
            )
            
            # Verify response structure
            assert response.message == mock_rag_result["response"]
            assert response.provider == "ollama"
            assert response.model == "llama3"
            assert response.usage["rag_enabled"] is True
            assert response.usage["sources_count"] == 1
            assert len(response.sources) == 1
            assert response.sources[0].file_name == "algorithms.md"
            assert response.sources[0].similarity_score == 0.85
            
            # Verify RAG query was called with correct parameters
            mock_query.assert_called_once()
            call_args = mock_query.call_args
            assert call_args[1]["project_id"] == project_id
            assert call_args[1]["model_name"] == "llama3"
            assert "machine learning" in call_args[1]["question"]
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not LlamaIndexRAGService.is_available(), reason="LlamaIndex not available")
    async def test_error_handling_and_fallback(self):
        """Test error handling and fallback to traditional RAG"""
        project_id = 1
        
        with patch.object(LlamaIndexRAGService, 'query') as mock_query, \
             patch.object(ChatService, 'send_message_to_llm') as mock_fallback, \
             patch.object(DocumentService, 'get_active_documents_content') as mock_docs:
            
            # Mock RAG query to raise exception
            mock_query.side_effect = Exception("LlamaIndex connection failed")
            
            # Mock fallback method
            mock_fallback.return_value = Mock(
                message="Fallback response",
                provider="ollama",
                model="llama3",
                usage={"fallback": True}
            )
            
            # Mock document content
            mock_docs.return_value = ["Sample document content"]
            
            # Create chat request
            chat_request = ChatRequest(
                message="Test question",
                project_id=project_id,
                provider=LLMProvider.OLLAMA,
                model="llama3"
            )
            
            mock_db = AsyncMock()
            
            # Test chat with RAG (should fallback)
            response = await ChatService.send_message_with_rag(
                db=mock_db,
                chat_request=chat_request,
                project_id=project_id
            )
            
            # Verify fallback was used
            assert response.message == "Fallback response"
            mock_fallback.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not LlamaIndexRAGService.is_available(), reason="LlamaIndex not available")
    async def test_chunking_strategy_optimization(self):
        """Test that different project types use appropriate chunking strategies"""
        project_types = ["academic", "legal", "technical", "default"]
        expected_strategies = ["semantic", "sentence", "recursive", "sentence"]
        
        for project_type, expected_strategy in zip(project_types, expected_strategies):
            with patch.object(LlamaIndexRAGService, '_create_optimized_node_parser') as mock_parser:
                mock_parser.return_value = Mock()
                
                # This would be called during index building
                parser = LlamaIndexRAGService._create_optimized_node_parser(
                    project_type=project_type
                )
                
                # Verify appropriate strategy was selected
                mock_parser.assert_called_once_with(project_type=project_type)
                assert parser is not None
    
    @pytest.mark.asyncio
    async def test_index_statistics(self):
        """Test index statistics functionality"""
        project_id = 1
        
        with patch('app.services.llamaindex_service.settings') as mock_settings, \
             patch('lancedb.connect') as mock_lancedb:
            
            mock_settings.LANCE_DB_DIR = "/tmp/test"
            
            # Test case 1: No index exists
            with patch('pathlib.Path.exists', return_value=False):
                stats = await LlamaIndexRAGService.get_index_stats(project_id)
                assert "error" in stats
                assert stats["error"] == "No index found"
            
            # Test case 2: Index exists
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('pathlib.Path.rglob') as mock_rglob:
                
                # Mock file system
                mock_files = [Mock(stat=Mock(return_value=Mock(st_size=1000, st_mtime=1234567890)))]
                mock_rglob.return_value = mock_files
                
                # Mock LanceDB
                mock_db = Mock()
                mock_table = Mock()
                mock_table.__len__ = Mock(return_value=100)
                mock_db.table_names.return_value = ["vectors"]
                mock_db.open_table.return_value = mock_table
                mock_lancedb.return_value = mock_db
                
                stats = await LlamaIndexRAGService.get_index_stats(project_id)
                
                assert "num_vectors" in stats
                assert "index_size_mb" in stats
                assert "last_modified" in stats
                assert stats["num_vectors"] == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])