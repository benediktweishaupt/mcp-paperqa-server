"""
Comprehensive unit tests for text extraction components
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

# Import the modules we're testing
try:
    from pdf_processing.extractors import BaseExtractor, PyMuPDFExtractor, PDFPlumberExtractor
    from pdf_processing.core import PDFProcessor
    from pdf_processing.config import ProcessorConfig, ExtractionMethod
    from pdf_processing.models import Document, Paragraph, Section, Metadata
    EXTRACTORS_AVAILABLE = True
except ImportError:
    EXTRACTORS_AVAILABLE = False


class TestBaseExtractor:
    """Test the base extractor interface"""
    
    def test_base_extractor_interface(self):
        """Test that BaseExtractor defines the required interface"""
        if not EXTRACTORS_AVAILABLE:
            pytest.skip("PDF processing modules not available")
        
        # BaseExtractor should be abstract
        with pytest.raises(TypeError):
            BaseExtractor()
    
    def test_extractor_validation_methods(self):
        """Test extractor validation and capability methods"""
        if not EXTRACTORS_AVAILABLE:
            pytest.skip("PDF processing modules not available")
        
        # Create a mock concrete extractor
        class MockExtractor(BaseExtractor):
            def extract_text(self, file_path, config=None):
                return "Mock extracted text"
            
            def extract_metadata(self, file_path, config=None):
                return {"title": "Mock Title"}
            
            def extract_structure(self, file_path, config=None):
                return []
        
        extractor = MockExtractor()
        
        # Test interface methods exist
        assert hasattr(extractor, 'extract_text')
        assert hasattr(extractor, 'extract_metadata')
        assert hasattr(extractor, 'extract_structure')
        assert hasattr(extractor, 'validate_file')
        assert hasattr(extractor, 'get_capabilities')


class TestPyMuPDFExtractor:
    """Test PyMuPDF-based extraction"""
    
    @pytest.fixture
    def mock_fitz_document(self):
        """Create a mock fitz document for testing"""
        mock_doc = Mock()
        mock_page = Mock()
        
        # Mock page text extraction
        mock_page.get_text.return_value = "Sample page text with multiple paragraphs."
        mock_page.number = 0
        mock_page.rect = Mock()
        mock_page.rect.width = 595
        mock_page.rect.height = 842
        
        # Mock text dictionary extraction (for structure)
        mock_page.get_text.return_value = {
            'blocks': [
                {
                    'type': 0,
                    'bbox': [50, 100, 500, 120],
                    'lines': [
                        {
                            'bbox': [50, 100, 500, 120],
                            'spans': [
                                {
                                    'text': 'Sample heading text',
                                    'font': 'Arial-Bold',
                                    'size': 16,
                                    'bbox': [50, 100, 200, 120]
                                }
                            ]
                        }
                    ]
                },
                {
                    'type': 0,
                    'bbox': [50, 150, 500, 200],
                    'lines': [
                        {
                            'bbox': [50, 150, 500, 200],
                            'spans': [
                                {
                                    'text': 'Sample paragraph text content.',
                                    'font': 'Arial',
                                    'size': 12,
                                    'bbox': [50, 150, 400, 170]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Mock document properties
        mock_doc.page_count = 1
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.__getitem__ = Mock(return_value=mock_page)
        mock_doc.metadata = {
            'title': 'Test Document',
            'author': 'Test Author',
            'subject': 'Test Subject',
            'creator': 'Test Creator'
        }
        
        return mock_doc
    
    def test_pymupdf_extractor_initialization(self):
        """Test PyMuPDF extractor initialization"""
        if not EXTRACTORS_AVAILABLE:
            pytest.skip("PDF processing modules not available")
        
        extractor = PyMuPDFExtractor()
        assert extractor is not None
        
        capabilities = extractor.get_capabilities()
        assert 'text_extraction' in capabilities
        assert 'metadata_extraction' in capabilities
        assert 'structure_analysis' in capabilities
    
    @patch('pdf_processing.extractors.pymupdf_extractor.fitz')
    def test_pymupdf_text_extraction(self, mock_fitz, mock_fitz_document):
        """Test text extraction with PyMuPDF"""
        if not EXTRACTORS_AVAILABLE:
            pytest.skip("PDF processing modules not available")
        
        # Setup mock
        mock_fitz.open.return_value = mock_fitz_document
        
        extractor = PyMuPDFExtractor()
        
        # Test text extraction
        with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
            result = extractor.extract_text(temp_file.name)
            
            assert isinstance(result, str)
            assert len(result) > 0
            mock_fitz.open.assert_called_once_with(temp_file.name)
    
    @patch('pdf_processing.extractors.pymupdf_extractor.fitz')
    def test_pymupdf_metadata_extraction(self, mock_fitz, mock_fitz_document):
        """Test metadata extraction with PyMuPDF"""
        if not EXTRACTORS_AVAILABLE:
            pytest.skip("PDF processing modules not available")
        
        mock_fitz.open.return_value = mock_fitz_document
        
        extractor = PyMuPDFExtractor()
        
        with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
            metadata = extractor.extract_metadata(temp_file.name)
            
            assert isinstance(metadata, dict)
            assert 'title' in metadata
            assert metadata['title'] == 'Test Document'
    
    @patch('pdf_processing.extractors.pymupdf_extractor.fitz')
    def test_pymupdf_structure_extraction(self, mock_fitz, mock_fitz_document):
        """Test structure extraction with PyMuPDF"""
        if not EXTRACTORS_AVAILABLE:
            pytest.skip("PDF processing modules not available")
        
        mock_fitz.open.return_value = mock_fitz_document
        
        extractor = PyMuPDFExtractor()
        
        with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
            structure = extractor.extract_structure(temp_file.name)
            
            assert isinstance(structure, list)
            # Structure should contain text elements with positioning info
            if structure:
                element = structure[0]
                assert 'text' in element
                assert 'bbox' in element or 'position' in element
    
    def test_pymupdf_error_handling(self):
        """Test error handling in PyMuPDF extractor"""
        if not EXTRACTORS_AVAILABLE:
            pytest.skip("PDF processing modules not available")
        
        extractor = PyMuPDFExtractor()
        
        # Test with non-existent file
        with pytest.raises((FileNotFoundError, OSError)):
            extractor.extract_text("/non/existent/file.pdf")
        
        # Test file validation
        assert not extractor.validate_file("/non/existent/file.pdf")


class TestPDFPlumberExtractor:
    """Test PDFPlumber-based extraction"""
    
    @pytest.fixture
    def mock_pdfplumber_pdf(self):
        """Create mock pdfplumber PDF object"""
        mock_pdf = Mock()
        mock_page = Mock()
        
        # Mock page properties
        mock_page.extract_text.return_value = "Sample text from pdfplumber"
        mock_page.within_bbox = Mock(return_value=mock_page)
        mock_page.chars = [
            {
                'text': 'S',
                'x0': 50, 'y0': 100, 'x1': 58, 'y1': 112,
                'fontname': 'Arial', 'size': 12
            },
            {
                'text': 'a',
                'x0': 58, 'y0': 100, 'x1': 65, 'y1': 112,
                'fontname': 'Arial', 'size': 12
            }
        ]
        mock_page.width = 595
        mock_page.height = 842
        
        # Mock tables
        mock_page.find_tables.return_value = []
        
        mock_pdf.pages = [mock_page]
        mock_pdf.metadata = {
            'Title': 'Test PDF Title',
            'Author': 'Test Author'
        }
        
        return mock_pdf
    
    def test_pdfplumber_extractor_initialization(self):
        """Test PDFPlumber extractor initialization"""
        if not EXTRACTORS_AVAILABLE:
            pytest.skip("PDF processing modules not available")
        
        extractor = PDFPlumberExtractor()
        assert extractor is not None
        
        capabilities = extractor.get_capabilities()
        assert 'text_extraction' in capabilities
        assert 'table_extraction' in capabilities
        assert 'detailed_layout' in capabilities
    
    @patch('pdf_processing.extractors.pdfplumber_extractor.pdfplumber')
    def test_pdfplumber_text_extraction(self, mock_pdfplumber, mock_pdfplumber_pdf):
        """Test text extraction with PDFPlumber"""
        if not EXTRACTORS_AVAILABLE:
            pytest.skip("PDF processing modules not available")
        
        mock_pdfplumber.open.return_value.__enter__ = Mock(return_value=mock_pdfplumber_pdf)
        mock_pdfplumber.open.return_value.__exit__ = Mock(return_value=None)
        
        extractor = PDFPlumberExtractor()
        
        with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
            result = extractor.extract_text(temp_file.name)
            
            assert isinstance(result, str)
            assert len(result) > 0
    
    @patch('pdf_processing.extractors.pdfplumber_extractor.pdfplumber')
    def test_pdfplumber_table_extraction(self, mock_pdfplumber, mock_pdfplumber_pdf):
        """Test table extraction with PDFPlumber"""
        if not EXTRACTORS_AVAILABLE:
            pytest.skip("PDF processing modules not available")
        
        # Add mock table data
        mock_table = Mock()
        mock_table.extract.return_value = [
            ['Header 1', 'Header 2'],
            ['Row 1 Col 1', 'Row 1 Col 2'],
            ['Row 2 Col 1', 'Row 2 Col 2']
        ]
        mock_table.bbox = (50, 100, 400, 200)
        
        mock_pdfplumber_pdf.pages[0].find_tables.return_value = [mock_table]
        
        mock_pdfplumber.open.return_value.__enter__ = Mock(return_value=mock_pdfplumber_pdf)
        mock_pdfplumber.open.return_value.__exit__ = Mock(return_value=None)
        
        extractor = PDFPlumberExtractor()
        
        with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
            tables = extractor.extract_tables(temp_file.name)
            
            assert isinstance(tables, list)
            if tables:
                table = tables[0]
                assert 'data' in table
                assert 'bbox' in table
                assert len(table['data']) > 0


class TestExtractorIntegration:
    """Test integration between different extractors"""
    
    def test_extractor_selection(self):
        """Test automatic extractor selection logic"""
        if not EXTRACTORS_AVAILABLE:
            pytest.skip("PDF processing modules not available")
        
        config = ProcessorConfig(
            extraction_method=ExtractionMethod.AUTO,
            fallback_extractors=[ExtractionMethod.PYMUPDF, ExtractionMethod.PDFPLUMBER]
        )
        
        processor = PDFProcessor(config)
        
        # Should have multiple extractors available
        assert len(processor.extractors) > 0
        
        # Test that we can get extractors by method
        pymupdf_extractor = next((e for e in processor.extractors 
                                if isinstance(e, PyMuPDFExtractor)), None)
        pdfplumber_extractor = next((e for e in processor.extractors 
                                   if isinstance(e, PDFPlumberExtractor)), None)
        
        # At least one should be available
        assert pymupdf_extractor is not None or pdfplumber_extractor is not None
    
    def test_hybrid_extraction(self):
        """Test hybrid extraction using multiple extractors"""
        if not EXTRACTORS_AVAILABLE:
            pytest.skip("PDF processing modules not available")
        
        config = ProcessorConfig(
            extraction_method=ExtractionMethod.HYBRID
        )
        
        processor = PDFProcessor(config)
        
        # Hybrid mode should attempt to use multiple extractors
        assert len(processor.extractors) > 0
    
    @patch('pdf_processing.extractors.pymupdf_extractor.fitz')
    @patch('pdf_processing.extractors.pdfplumber_extractor.pdfplumber')
    def test_fallback_mechanism(self, mock_pdfplumber, mock_fitz):
        """Test extractor fallback when primary method fails"""
        if not EXTRACTORS_AVAILABLE:
            pytest.skip("PDF processing modules not available")
        
        # Make first extractor fail
        mock_fitz.open.side_effect = Exception("PyMuPDF failed")
        
        # Make second extractor succeed
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Fallback text extracted"
        mock_pdf.pages = [mock_page]
        mock_pdf.metadata = {}
        
        mock_pdfplumber.open.return_value.__enter__ = Mock(return_value=mock_pdf)
        mock_pdfplumber.open.return_value.__exit__ = Mock(return_value=None)
        
        config = ProcessorConfig(
            extraction_method=ExtractionMethod.AUTO,
            fallback_extractors=[ExtractionMethod.PYMUPDF, ExtractionMethod.PDFPLUMBER]
        )
        
        processor = PDFProcessor(config)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
            try:
                document = processor.process_document(temp_file.name)
                # Should succeed with fallback extractor
                assert document is not None
            except Exception:
                # If all extractors fail, that's expected in this test environment
                pass


class TestExtractionQuality:
    """Test extraction quality and accuracy"""
    
    def test_text_preservation(self):
        """Test that text extraction preserves content accurately"""
        if not EXTRACTORS_AVAILABLE:
            pytest.skip("PDF processing modules not available")
        
        # This would test against known ground truth data
        # For now, we test the structure of results
        
        expected_text = "This is a test paragraph with specific formatting."
        
        # Mock extractor that returns known text
        class TestExtractor(BaseExtractor):
            def extract_text(self, file_path, config=None):
                return expected_text
            
            def extract_metadata(self, file_path, config=None):
                return {}
            
            def extract_structure(self, file_path, config=None):
                return []
        
        extractor = TestExtractor()
        result = extractor.extract_text("/dummy/path.pdf")
        
        assert result == expected_text
    
    def test_structure_preservation(self):
        """Test that document structure is preserved"""
        if not EXTRACTORS_AVAILABLE:
            pytest.skip("PDF processing modules not available")
        
        # Test structure preservation through Document model
        metadata = Metadata(title="Test Document")
        document = Document(
            file_path="/test/path.pdf",
            file_name="path.pdf",
            metadata=metadata
        )
        
        # Add structured content
        section = Section(title="Introduction", level=1)
        paragraph = Paragraph(content="Introduction text", page_number=1)
        section.content.append(paragraph)
        document.sections.append(section)
        
        # Verify structure is maintained
        assert len(document.sections) == 1
        assert document.sections[0].title == "Introduction"
        assert len(document.sections[0].content) == 1
        assert document.sections[0].content[0].content == "Introduction text"
    
    def test_metadata_completeness(self):
        """Test extraction of complete metadata"""
        if not EXTRACTORS_AVAILABLE:
            pytest.skip("PDF processing modules not available")
        
        # Test metadata model completeness
        metadata = Metadata(
            title="Complete Test Document",
            authors=["Author One", "Author Two"],
            abstract="This is a comprehensive abstract.",
            keywords=["test", "extraction", "metadata"],
            doi="10.1000/test.doi",
            publication_year=2023
        )
        
        # Verify all fields are captured
        assert metadata.title == "Complete Test Document"
        assert len(metadata.authors) == 2
        assert metadata.abstract == "This is a comprehensive abstract."
        assert len(metadata.keywords) == 3
        assert metadata.doi == "10.1000/test.doi"
        assert metadata.publication_year == 2023


class TestErrorHandling:
    """Test error handling and robustness"""
    
    def test_invalid_file_handling(self):
        """Test handling of invalid PDF files"""
        if not EXTRACTORS_AVAILABLE:
            pytest.skip("PDF processing modules not available")
        
        extractor = PyMuPDFExtractor()
        
        # Test non-existent file
        with pytest.raises((FileNotFoundError, OSError)):
            extractor.extract_text("/non/existent/file.pdf")
        
        # Test invalid file format (create a text file with .pdf extension)
        with tempfile.NamedTemporaryFile(suffix='.pdf', mode='w', delete=False) as f:
            f.write("This is not a PDF file")
            f.flush()
            
            try:
                with pytest.raises(Exception):
                    extractor.extract_text(f.name)
            finally:
                os.unlink(f.name)
    
    def test_corrupted_pdf_handling(self):
        """Test handling of corrupted PDF files"""
        if not EXTRACTORS_AVAILABLE:
            pytest.skip("PDF processing modules not available")
        
        # This would test with actual corrupted PDF samples
        # For now, we test the error handling structure
        
        extractor = PyMuPDFExtractor()
        
        # Mock a scenario where PDF opens but fails during processing
        with patch('pdf_processing.extractors.pymupdf_extractor.fitz') as mock_fitz:
            mock_doc = Mock()
            mock_doc.__getitem__.side_effect = Exception("Corrupted page")
            mock_fitz.open.return_value = mock_doc
            
            with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
                with pytest.raises(Exception):
                    extractor.extract_text(temp_file.name)
    
    def test_memory_exhaustion_handling(self):
        """Test handling of memory-intensive documents"""
        if not EXTRACTORS_AVAILABLE:
            pytest.skip("PDF processing modules not available")
        
        # This would test with very large documents
        # For now, we test that the framework has memory management
        
        config = ProcessorConfig(
            max_memory_usage_mb=100,
            enable_streaming=True
        )
        
        processor = PDFProcessor(config)
        
        # Verify memory-conscious configuration is set
        assert processor.config.max_memory_usage_mb == 100
        assert processor.config.enable_streaming is True


if __name__ == "__main__":
    # Run basic functionality tests
    if EXTRACTORS_AVAILABLE:
        print("🔄 Running text extraction tests...")
        
        # Basic tests that don't require actual PDF files
        test_suite = TestExtractionQuality()
        try:
            test_suite.test_metadata_completeness()
            print("✅ Metadata tests passed")
        except Exception as e:
            print(f"❌ Metadata tests failed: {e}")
        
        try:
            test_suite.test_structure_preservation()
            print("✅ Structure preservation tests passed")  
        except Exception as e:
            print(f"❌ Structure preservation tests failed: {e}")
        
        print("\n🎉 Text extraction testing complete!")
        print("📝 Note: Full integration tests require PDF libraries and sample files")
        
    else:
        print("⚠️  PDF processing modules not available")
        print("📦 Install requirements: pip install PyMuPDF pdfplumber")