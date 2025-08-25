import pytest
from app.features.documents.utils import DocumentProcessor


class TestIntelligentChunking:
    """Test intelligent chunking functionality"""
    
    @pytest.fixture
    def sample_content(self):
        """Sample content for testing chunking"""
        return """
        This is a sample document for testing intelligent chunking capabilities.
        
        ## Introduction
        The document contains multiple sections with different content types.
        This includes technical documentation, research findings, and general text.
        
        ## Technical Section
        Here we have code examples and technical specifications.
        The system should handle these appropriately based on the chunking strategy.
        
        ## Research Findings
        Academic content requires different handling compared to technical documentation.
        Long sentences and complex structures need careful consideration.
        The semantic meaning should be preserved across chunk boundaries.
        
        ## Conclusion
        The intelligent chunking system adapts to content type and project requirements.
        This ensures optimal performance for retrieval-augmented generation tasks.
        """
    
    def test_default_chunking(self, sample_content):
        """Test default chunking strategy"""
        chunks = DocumentProcessor.chunk_text(sample_content, strategy='default')
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(chunk.strip() for chunk in chunks)  # No empty chunks
    
    def test_sentence_chunking(self, sample_content):
        """Test sentence-based chunking"""
        chunks = DocumentProcessor.chunk_text(
            sample_content, 
            strategy='sentence',
            chunk_size=200,
            overlap=20
        )
        assert len(chunks) > 0
        # Sentence chunking should produce more, smaller chunks
        assert len(chunks) >= 3
    
    def test_recursive_chunking(self, sample_content):
        """Test recursive character-based chunking"""
        chunks = DocumentProcessor.chunk_text(
            sample_content,
            strategy='recursive',
            chunk_size=300,
            overlap=50
        )
        assert len(chunks) > 0
        # Should respect markdown structure
        for chunk in chunks:
            # Should not break in the middle of headers
            if '##' in chunk:
                lines = chunk.split('\n')
                for line in lines:
                    if line.startswith('##'):
                        # Header should not be orphaned
                        header_index = lines.index(line)
                        assert header_index < len(lines) - 1 or chunk == chunks[-1]
    
    def test_optimal_strategy_selection(self):
        """Test automatic strategy selection based on project type"""
        # Research project should prefer semantic chunking
        strategy = DocumentProcessor.get_optimal_chunking_strategy(
            project_type="Academic Research Project"
        )
        assert strategy == 'semantic'
        
        # Legal project should prefer sentence chunking
        strategy = DocumentProcessor.get_optimal_chunking_strategy(
            project_type="Legal Contract Analysis"
        )
        assert strategy == 'sentence'
        
        # Technical project should prefer recursive chunking
        strategy = DocumentProcessor.get_optimal_chunking_strategy(
            project_type="Technical Documentation"
        )
        assert strategy == 'recursive'
        
        # Code project should prefer token chunking
        strategy = DocumentProcessor.get_optimal_chunking_strategy(
            project_type="Software Development"
        )
        assert strategy == 'token'
        
        # Default case
        strategy = DocumentProcessor.get_optimal_chunking_strategy(
            project_type="General Project"
        )
        assert strategy == 'sentence'  # Safe default
    
    def test_file_type_based_strategy(self):
        """Test strategy selection based on file types"""
        # Majority PDFs should use sentence chunking
        strategy = DocumentProcessor.get_optimal_chunking_strategy(
            file_types=['.pdf', '.pdf', '.pdf', '.docx']
        )
        assert strategy == 'sentence'
        
        # Significant markdown should use recursive
        strategy = DocumentProcessor.get_optimal_chunking_strategy(
            file_types=['.md', '.md', '.pdf', '.txt']
        )
        assert strategy == 'recursive'
        
        # Majority Word docs should use sentence
        strategy = DocumentProcessor.get_optimal_chunking_strategy(
            file_types=['.docx', '.docx', '.pdf']
        )
        assert strategy == 'sentence'
    
    def test_chunking_strategies_config(self):
        """Test that chunking strategy configurations are properly defined"""
        assert 'sentence' in DocumentProcessor.CHUNK_STRATEGIES
        assert 'semantic' in DocumentProcessor.CHUNK_STRATEGIES
        assert 'token' in DocumentProcessor.CHUNK_STRATEGIES
        assert 'recursive' in DocumentProcessor.CHUNK_STRATEGIES
        assert 'default' in DocumentProcessor.CHUNK_STRATEGIES
        
        # Verify required parameters for each strategy
        sentence_config = DocumentProcessor.CHUNK_STRATEGIES['sentence']
        assert 'chunk_size' in sentence_config
        assert 'chunk_overlap' in sentence_config
        
        semantic_config = DocumentProcessor.CHUNK_STRATEGIES['semantic']
        assert 'buffer_size' in semantic_config
        assert 'percentile_cutoff' in semantic_config
    
    def test_empty_content_handling(self):
        """Test handling of empty or whitespace content"""
        assert DocumentProcessor.chunk_text("") == []
        assert DocumentProcessor.chunk_text("   ") == []
        assert DocumentProcessor.chunk_text("\n\n\n") == []
    
    def test_japanese_content_chunking(self):
        """Test chunking with Japanese content"""
        japanese_content = """
        これは日本語のテストコンテンツです。インテリジェントチャンキング機能のテストを行います。
        
        ## セクション1
        日本語の文書は句読点や改行の処理が重要です。文の境界を正確に判断する必要があります。
        
        ## セクション2  
        長い文章も適切に分割される必要があります。意味的なまとまりを保持しながら、適切なサイズのチャンクを作成します。
        """
        
        chunks = DocumentProcessor.chunk_text(
            japanese_content,
            strategy='sentence',
            chunk_size=100
        )
        
        assert len(chunks) > 0
        # Should handle Japanese punctuation
        for chunk in chunks:
            assert isinstance(chunk, str)
            assert chunk.strip()
    
    def test_fallback_behavior(self):
        """Test fallback behavior when LlamaIndex is not available"""
        # Test that fallback works when intelligent chunking fails
        content = "This is test content for fallback behavior testing."
        
        # Should not raise exception even with advanced strategy
        chunks = DocumentProcessor.chunk_text(
            content,
            strategy='nonexistent_strategy'
        )
        
        assert len(chunks) > 0
        assert chunks[0] == content.strip()  # Should fall back to basic chunking