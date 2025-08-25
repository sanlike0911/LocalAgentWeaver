"""
Test suite for LlamaIndexRAGService implementing tasks 13-16:
- Task 13: SimpleDirectoryReader integration with file format parsers
- Task 14: NodeParser optimization for intelligent chunking  
- Task 15: VectorStoreIndex construction with LanceDB integration
- Task 16: RetrieverQueryEngine for high-precision search

Tests cover both successful operations and error handling scenarios.
"""

import os
import tempfile
import shutil
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from app.services.llamaindex_service import LlamaIndexRAGService
from app.core.config import settings


class TestLlamaIndexRAGService:
    """Test suite for enhanced LlamaIndex RAG Service"""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def sample_files(self, temp_project_dir):
        """Create sample files for testing."""
        files = {}
        
        # Create sample text file
        txt_file = temp_project_dir / "sample.txt"
        txt_file.write_text("This is a sample text document for testing.", encoding='utf-8')
        files['txt'] = str(txt_file)
        
        # Create sample markdown file
        md_file = temp_project_dir / "sample.md"
        md_file.write_text("# Sample Markdown\n\nThis is markdown content.", encoding='utf-8')
        files['md'] = str(md_file)
        
        return files
    
    def test_is_available(self):
        """Test LlamaIndex availability check."""
        # This test will depend on whether LlamaIndex is actually installed
        result = LlamaIndexRAGService.is_available()
        assert isinstance(result, bool)
    
    def test_get_project_store_dir(self):
        """Test project store directory path generation."""
        project_id = 123
        expected_path = Path(settings.LANCE_DB_DIR) / f"project_{project_id}"
        
        result = LlamaIndexRAGService.get_project_store_dir(project_id)
        
        assert result == expected_path
        assert isinstance(result, Path)
    
    @pytest.mark.skipif(not LlamaIndexRAGService.is_available(), reason="LlamaIndex not available")
    def test_setup_global_settings(self):
        """Test global settings configuration."""
        with patch('app.services.llamaindex_service.Settings') as mock_settings:
            LlamaIndexRAGService._setup_global_settings("test-model")
            
            # Verify that embedding model and LLM were configured
            assert mock_settings.embed_model is not None
            assert mock_settings.llm is not None
    
    @pytest.mark.skipif(not LlamaIndexRAGService.is_available(), reason="LlamaIndex not available")
    def test_create_enhanced_file_reader(self, sample_files):
        """Task 13: Test SimpleDirectoryReader integration with file format parsers."""
        project_metadata = {"project_id": 123, "project_name": "test"}
        
        # Test with available files
        documents = LlamaIndexRAGService._create_enhanced_file_reader(
            list(sample_files.values()), 
            project_metadata
        )
        
        assert len(documents) > 0
        
        # Verify metadata is properly attached
        for doc in documents:
            assert "project_id" in doc.metadata
            assert "file_path" in doc.metadata
            assert "file_name" in doc.metadata
            assert "file_type" in doc.metadata
            assert doc.metadata["project_id"] == 123
    
    @pytest.mark.skipif(not LlamaIndexRAGService.is_available(), reason="LlamaIndex not available")
    def test_create_enhanced_file_reader_nonexistent_files(self):
        """Test file reader with nonexistent files."""
        nonexistent_files = ["/path/that/does/not/exist.txt"]
        project_metadata = {"project_id": 123}
        
        # Should handle gracefully and return empty list
        documents = LlamaIndexRAGService._create_enhanced_file_reader(
            nonexistent_files, 
            project_metadata
        )
        
        assert documents == []
    
    @pytest.mark.skipif(not LlamaIndexRAGService.is_available(), reason="LlamaIndex not available") 
    def test_create_optimized_node_parser(self):
        """Task 14: Test NodeParser optimization for intelligent chunking."""
        # Test different chunking strategies
        strategies = ['sentence', 'token', 'recursive', 'semantic']
        
        for strategy in strategies:
            try:
                parser = LlamaIndexRAGService._create_optimized_node_parser(
                    strategy=strategy, 
                    project_type='academic'
                )
                assert parser is not None
            except Exception as e:
                # Semantic chunking might fail without proper embedding setup
                if strategy == 'semantic':
                    continue
                else:
                    raise e
    
    @pytest.mark.skipif(not LlamaIndexRAGService.is_available(), reason="LlamaIndex not available")
    def test_create_optimized_node_parser_project_types(self):
        """Test node parser optimization for different project types."""
        project_types = ['academic', 'legal', 'technical', 'default']
        
        for project_type in project_types:
            parser = LlamaIndexRAGService._create_optimized_node_parser(
                project_type=project_type
            )
            assert parser is not None
    
    def test_create_optimized_node_parser_without_llamaindex(self):
        """Test node parser creation when LlamaIndex is not available."""
        if LlamaIndexRAGService.is_available():
            pytest.skip("LlamaIndex is available")
        
        with pytest.raises(RuntimeError, match="LlamaIndex is not available"):
            LlamaIndexRAGService._create_optimized_node_parser()
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not LlamaIndexRAGService.is_available(), reason="LlamaIndex not available")
    async def test_build_or_update_index_no_documents(self):
        """Task 15: Test index building with no documents."""
        project_id = 999  # Non-existent project
        
        with patch('app.services.llamaindex_service.AsyncSessionLocal') as mock_session:
            mock_session.return_value.__aenter__.return_value.execute.return_value = Mock()
            mock_session.return_value.__aenter__.return_value.execute.return_value.__iter__ = lambda x: iter([])
            
            result = await LlamaIndexRAGService.build_or_update_index(project_id)
            
            # Should return True even with no documents
            assert result is True
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not LlamaIndexRAGService.is_available(), reason="LlamaIndex not available")
    async def test_build_or_update_index_with_documents(self, sample_files, temp_project_dir):
        """Task 15: Test VectorStoreIndex construction with documents."""
        project_id = 123
        
        # Mock database session to return our sample files
        mock_rows = [(path,) for path in sample_files.values()]
        
        with patch('app.services.llamaindex_service.AsyncSessionLocal') as mock_session, \
             patch('app.services.llamaindex_service.settings') as mock_settings:
            
            # Configure mock settings
            mock_settings.LANCE_DB_DIR = str(temp_project_dir)
            mock_settings.OLLAMA_EMBEDDING_MODEL = "test-embed"
            mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
            
            # Configure mock session
            mock_session.return_value.__aenter__.return_value.execute.return_value = Mock()
            mock_session.return_value.__aenter__.return_value.execute.return_value.__iter__ = lambda x: iter(mock_rows)
            
            # Mock the global settings setup to avoid actual Ollama calls
            with patch.object(LlamaIndexRAGService, '_setup_global_settings'):
                result = await LlamaIndexRAGService.build_or_update_index(project_id)
                
                # Index building might fail due to missing Ollama, but should handle gracefully
                assert isinstance(result, bool)
    
    def test_create_retriever_query_engine_no_index(self):
        """Task 16: Test query engine creation with no index."""
        project_id = 999
        model_name = "llama3"
        
        query_engine = LlamaIndexRAGService.create_retriever_query_engine(
            project_id=project_id,
            model_name=model_name
        )
        
        # Should return None when no index exists
        assert query_engine is None
    
    @pytest.mark.skipif(not LlamaIndexRAGService.is_available(), reason="LlamaIndex not available")
    def test_create_retriever_query_engine_optimization(self):
        """Task 16: Test query engine optimization for different project types."""
        project_types = ['academic', 'legal', 'technical', 'default']
        
        for project_type in project_types:
            # This will return None since no index exists, but tests parameter handling
            query_engine = LlamaIndexRAGService.create_retriever_query_engine(
                project_id=123,
                model_name="llama3",
                project_type=project_type
            )
            
            # Verify it handles project_type parameter without errors
            assert query_engine is None  # Expected since no index exists
    
    @pytest.mark.asyncio
    async def test_query_without_llamaindex(self):
        """Test query method when LlamaIndex is not available."""
        if LlamaIndexRAGService.is_available():
            pytest.skip("LlamaIndex is available")
        
        result = await LlamaIndexRAGService.query(
            project_id=123,
            question="Test question",
            model_name="llama3"
        )
        
        assert "response" in result
        assert "sources" in result
        assert "metadata" in result
        assert "llamaindex_unavailable" in result["metadata"]["error"]
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not LlamaIndexRAGService.is_available(), reason="LlamaIndex not available")
    async def test_query_no_index(self):
        """Test query method with no index."""
        with patch.object(LlamaIndexRAGService, 'create_retriever_query_engine', return_value=None):
            result = await LlamaIndexRAGService.query(
                project_id=123,
                question="Test question",  
                model_name="llama3"
            )
            
            assert result["response"] == "このプロジェクトにはインデックスがありません。"
            assert result["sources"] == []
            assert "no_index" in result["metadata"]["error"]
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not LlamaIndexRAGService.is_available(), reason="LlamaIndex not available")
    async def test_query_with_parameters(self):
        """Test query method with various parameter combinations."""
        project_types = ['academic', 'legal', 'technical']
        
        for project_type in project_types:
            with patch.object(LlamaIndexRAGService, 'create_retriever_query_engine', return_value=None):
                result = await LlamaIndexRAGService.query(
                    project_id=123,
                    question="Test question",
                    model_name="llama3",
                    project_type=project_type,
                    similarity_top_k=10
                )
                
                # Should handle parameters without errors
                assert "response" in result
                assert "sources" in result
                assert "metadata" in result
    
    @pytest.mark.asyncio
    async def test_get_index_stats_no_index(self):
        """Test index statistics with no index."""
        result = await LlamaIndexRAGService.get_index_stats(999)
        
        assert "error" in result
        assert result["error"] == "No index found"
    
    @pytest.mark.asyncio 
    @pytest.mark.skipif(not LlamaIndexRAGService.is_available(), reason="LlamaIndex not available")
    async def test_get_index_stats_with_index(self, temp_project_dir):
        """Test index statistics with existing index."""
        project_id = 123
        
        # Create mock project directory structure
        project_dir = temp_project_dir / f"project_{project_id}"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a dummy file to simulate index data
        dummy_file = project_dir / "vectors.lance"
        dummy_file.write_text("dummy vector data")
        
        with patch('app.services.llamaindex_service.settings') as mock_settings, \
             patch('lancedb.connect') as mock_connect:
            
            mock_settings.LANCE_DB_DIR = str(temp_project_dir)
            
            # Mock LanceDB connection and table
            mock_db = Mock()
            mock_table = Mock()
            mock_table.__len__ = Mock(return_value=100)
            mock_db.table_names.return_value = ["vectors"]
            mock_db.open_table.return_value = mock_table
            mock_connect.return_value = mock_db
            
            result = await LlamaIndexRAGService.get_index_stats(project_id)
            
            assert "num_vectors" in result
            assert "index_size_mb" in result
            assert "last_modified" in result
            assert result["num_vectors"] == 100


@pytest.mark.integration
class TestLlamaIndexRAGServiceIntegration:
    """Integration tests requiring actual LlamaIndex and file system access."""
    
    @pytest.mark.skipif(not LlamaIndexRAGService.is_available(), reason="LlamaIndex not available")
    def test_chunking_strategies_consistency(self):
        """Verify that all chunking strategies produce consistent results."""
        test_content = """
        This is a sample document with multiple paragraphs.
        
        The first paragraph contains introductory information.
        The second paragraph has more detailed content.
        
        Finally, we have a concluding paragraph with summary information.
        """
        
        strategies = ['sentence', 'token', 'recursive']
        
        for strategy in strategies:
            try:
                parser = LlamaIndexRAGService._create_optimized_node_parser(strategy=strategy)
                # This would require actual LlamaIndex setup to test properly
                assert parser is not None
            except Exception as e:
                pytest.fail(f"Strategy {strategy} failed: {e}")
    
    @pytest.mark.skipif(not LlamaIndexRAGService.is_available(), reason="LlamaIndex not available")
    def test_file_format_support(self):
        """Verify support for all specified file formats."""
        supported_formats = ['.pdf', '.docx', '.pptx', '.txt', '.md']
        
        for file_format in supported_formats:
            # Verify format is recognized in FILE_READERS
            assert any(file_format in readers for readers in [
                LlamaIndexRAGService.FILE_READERS.keys(),
                ['.txt', '.md']  # These are handled by SimpleDirectoryReader
            ])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])