import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from fastapi import HTTPException

from app.features.documents.utils import DocumentProcessor

# LlamaIndex imports - optional for testing
try:
    from llama_index.core.schema import Document as LlamaDocument
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LlamaDocument = None
    LLAMAINDEX_AVAILABLE = False


class TestDocumentProcessorEnhanced:
    """Test enhanced DocumentProcessor with additional file format support"""
    
    def test_allowed_extensions_updated(self):
        """Test that ALLOWED_EXTENSIONS includes new formats"""
        expected_extensions = {'.pdf', '.txt', '.md', '.docx', '.xlsx', '.xls', '.pptx'}
        assert DocumentProcessor.ALLOWED_EXTENSIONS == expected_extensions
    
    def test_file_format_classification(self):
        """Test classification of file formats for processing"""
        assert '.pdf' in DocumentProcessor.LLAMAINDEX_SUPPORTED
        assert '.txt' in DocumentProcessor.LLAMAINDEX_SUPPORTED
        assert '.md' in DocumentProcessor.LLAMAINDEX_SUPPORTED
        assert '.docx' in DocumentProcessor.LLAMAINDEX_SUPPORTED
        
        assert '.xlsx' in DocumentProcessor.CUSTOM_PARSER_REQUIRED
        assert '.xls' in DocumentProcessor.CUSTOM_PARSER_REQUIRED
        assert '.pptx' in DocumentProcessor.CUSTOM_PARSER_REQUIRED
    
    def test_validate_file_new_formats(self):
        """Test file validation with new supported formats"""
        # Test Excel files
        mock_excel_file = Mock()
        mock_excel_file.filename = "test.xlsx"
        mock_excel_file.size = 1024
        DocumentProcessor.validate_file(mock_excel_file)  # Should not raise
        
        # Test PowerPoint files
        mock_pptx_file = Mock()
        mock_pptx_file.filename = "presentation.pptx"
        mock_pptx_file.size = 2048
        DocumentProcessor.validate_file(mock_pptx_file)  # Should not raise
        
        # Test unsupported format
        mock_unsupported_file = Mock()
        mock_unsupported_file.filename = "test.mp4"
        with pytest.raises(HTTPException) as exc_info:
            DocumentProcessor.validate_file(mock_unsupported_file)
        assert exc_info.value.status_code == 400
    
    @patch('app.features.documents.utils.load_workbook')
    def test_extract_excel_text(self, mock_workbook):
        """Test Excel text extraction"""
        # Mock Excel workbook structure
        mock_worksheet = Mock()
        mock_worksheet.iter_rows.return_value = [
            ("Header1", "Header2", "Header3"),
            ("Data1", "Data2", "Data3"),
            ("", None, "Data6")
        ]
        
        mock_wb = Mock()
        mock_wb.sheetnames = ["Sheet1"]
        mock_wb.__getitem__.return_value = mock_worksheet
        mock_workbook.return_value = mock_wb
        
        result = DocumentProcessor._extract_excel_text("test.xlsx")
        
        assert "[Sheet: Sheet1]" in result
        assert "Header1\tHeader2\tHeader3" in result
        assert "Data1\tData2\tData3" in result
    
    @patch('app.features.documents.utils.Presentation')
    def test_extract_pptx_text(self, mock_presentation_class):
        """Test PowerPoint text extraction"""
        # Mock PowerPoint structure
        mock_shape1 = Mock()
        mock_shape1.text = "Title Slide"
        mock_shape2 = Mock()
        mock_shape2.text = "Content here"
        
        mock_slide = Mock()
        mock_slide.shapes = [mock_shape1, mock_shape2]
        
        mock_presentation = Mock()
        mock_presentation.slides = [mock_slide]
        mock_presentation_class.return_value = mock_presentation
        
        result = DocumentProcessor._extract_pptx_text("test.pptx")
        
        assert "[Slide 1]" in result
        assert "Title Slide" in result
        assert "Content here" in result
    
    def test_read_text_content_excel_extension(self):
        """Test that read_text_content handles Excel files by extension"""
        with patch.object(DocumentProcessor, '_extract_excel_text') as mock_extract:
            mock_extract.return_value = "Excel content"
            
            result = DocumentProcessor.read_text_content("test.xlsx", "application/unknown")
            
            assert result == "Excel content"
            mock_extract.assert_called_once_with("test.xlsx")
    
    def test_read_text_content_pptx_extension(self):
        """Test that read_text_content handles PowerPoint files by extension"""
        with patch.object(DocumentProcessor, '_extract_pptx_text') as mock_extract:
            mock_extract.return_value = "PowerPoint content"
            
            result = DocumentProcessor.read_text_content("test.pptx", "application/unknown")
            
            assert result == "PowerPoint content"
            mock_extract.assert_called_once_with("test.pptx")
    
    @patch('app.features.documents.utils.SimpleDirectoryReader')
    def test_create_llamaindex_documents_mixed_formats(self, mock_reader):
        """Test creating LlamaIndex documents with mixed file formats"""
        # Mock SimpleDirectoryReader
        if LLAMAINDEX_AVAILABLE:
            mock_doc = Mock(spec=LlamaDocument)
        else:
            mock_doc = Mock()
        mock_reader_instance = Mock()
        mock_reader_instance.load_data.return_value = [mock_doc]
        mock_reader.return_value = mock_reader_instance
        
        # Mock custom parser methods
        with patch.object(DocumentProcessor, 'get_mime_type') as mock_mime, \
             patch.object(DocumentProcessor, 'read_text_content') as mock_read:
            
            mock_mime.return_value = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            mock_read.return_value = "Excel content"
            
            file_paths = ["test.pdf", "test.xlsx"]
            documents = DocumentProcessor.create_llamaindex_documents(
                file_paths, 
                metadata={"project_id": 1}
            )
            
            # Should have documents from both LlamaIndex and custom parser
            assert len(documents) >= 2
            
            # Verify SimpleDirectoryReader was called with PDF file
            mock_reader.assert_called_once_with(input_files=["test.pdf"])
            
            # Verify custom parser was called for Excel file
            mock_read.assert_called_once()
    
    @patch('app.features.documents.utils.SimpleDirectoryReader')
    def test_create_llamaindex_documents_fallback(self, mock_reader):
        """Test fallback to custom processing when LlamaIndex fails"""
        # Mock SimpleDirectoryReader to raise exception
        mock_reader_instance = Mock()
        mock_reader_instance.load_data.side_effect = Exception("LlamaIndex failed")
        mock_reader.return_value = mock_reader_instance
        
        with patch.object(DocumentProcessor, 'get_mime_type') as mock_mime, \
             patch.object(DocumentProcessor, 'read_text_content') as mock_read:
            
            mock_mime.return_value = "application/pdf"
            mock_read.return_value = "PDF content"
            
            file_paths = ["test.pdf"]
            documents = DocumentProcessor.create_llamaindex_documents(file_paths)
            
            # Should still return documents via fallback
            assert len(documents) == 1
            if LLAMAINDEX_AVAILABLE:
                assert isinstance(documents[0], LlamaDocument)
                assert documents[0].text == "PDF content"
            else:
                assert isinstance(documents[0], dict)
                assert documents[0]["text"] == "PDF content"
    
    def test_create_llamaindex_documents_empty_list(self):
        """Test handling empty file list"""
        documents = DocumentProcessor.create_llamaindex_documents([])
        assert documents == []
    
    @patch('app.features.documents.utils.SimpleDirectoryReader')
    def test_create_llamaindex_documents_with_metadata(self, mock_reader):
        """Test that metadata is properly included in documents"""
        mock_doc = Mock(spec=LlamaDocument)
        mock_reader_instance = Mock()
        mock_reader_instance.load_data.return_value = [mock_doc]
        mock_reader.return_value = mock_reader_instance
        
        file_paths = ["test.txt"]
        metadata = {"project_id": 123, "custom_field": "test"}
        documents = DocumentProcessor.create_llamaindex_documents(file_paths, metadata)
        
        # SimpleDirectoryReader should have been called
        mock_reader.assert_called_once_with(input_files=file_paths)
        assert len(documents) == 1


class TestDocumentProcessorErrorHandling:
    """Test error handling for new file formats"""
    
    @patch('app.features.documents.utils.load_workbook')
    def test_extract_excel_text_error_handling(self, mock_workbook):
        """Test Excel extraction error handling"""
        mock_workbook.side_effect = Exception("Excel file corrupted")
        
        with pytest.raises(RuntimeError) as exc_info:
            DocumentProcessor._extract_excel_text("corrupted.xlsx")
        
        assert "Excelテキスト抽出エラー" in str(exc_info.value)
    
    @patch('app.features.documents.utils.Presentation')
    def test_extract_pptx_text_error_handling(self, mock_presentation):
        """Test PowerPoint extraction error handling"""
        mock_presentation.side_effect = Exception("PowerPoint file corrupted")
        
        with pytest.raises(RuntimeError) as exc_info:
            DocumentProcessor._extract_pptx_text("corrupted.pptx")
        
        assert "PowerPointテキスト抽出エラー" in str(exc_info.value)
    
    def test_read_text_content_unsupported_mime_type(self):
        """Test handling of unsupported MIME types"""
        with pytest.raises(HTTPException) as exc_info:
            DocumentProcessor.read_text_content("test.unknown", "application/unknown")
        
        assert exc_info.value.status_code == 500
        assert "ファイルの内容読み取りエラー" in exc_info.value.detail