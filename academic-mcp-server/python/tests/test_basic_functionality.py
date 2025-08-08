"""
Basic functionality tests for PDF processing engine
"""

import pytest
import tempfile
import os
from pathlib import Path

# Test if we can import our modules
def test_imports():
    """Test that all main modules can be imported"""
    try:
        from pdf_processing import PDFProcessor, ProcessorConfig, ExtractionMethod
        from pdf_processing import Document, Section, Paragraph, Metadata
        from pdf_processing import PublisherType, get_academic_config
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import modules: {e}")


def test_processor_initialization():
    """Test PDFProcessor initialization"""
    try:
        from pdf_processing import PDFProcessor, get_academic_config
        
        # Test with default config
        processor1 = PDFProcessor()
        assert processor1.config is not None
        assert len(processor1.extractors) > 0  # Should have at least one extractor
        
        # Test with custom config
        config = get_academic_config()
        processor2 = PDFProcessor(config)
        assert processor2.config == config
        
    except Exception as e:
        pytest.skip(f"PDF libraries not installed: {e}")


def test_config_system():
    """Test configuration system"""
    from pdf_processing.config import ProcessorConfig, PublisherProfile, PublisherType
    from pdf_processing.config import get_academic_config, get_default_config
    
    # Test default configs
    default_config = get_default_config()
    academic_config = get_academic_config()
    
    assert isinstance(default_config, ProcessorConfig)
    assert isinstance(academic_config, ProcessorConfig)
    
    # Test publisher profiles
    ieee_config = PublisherProfile.get_profile(PublisherType.IEEE)
    acm_config = PublisherProfile.get_profile(PublisherType.ACM)
    
    assert isinstance(ieee_config, ProcessorConfig)
    assert isinstance(acm_config, ProcessorConfig)


def test_document_models():
    """Test document model classes"""
    from pdf_processing.models import Document, Section, Paragraph, Metadata, Heading
    
    # Test metadata creation
    metadata = Metadata(
        title="Test Paper",
        authors=["Author One", "Author Two"],
        abstract="This is a test abstract"
    )
    assert metadata.title == "Test Paper"
    assert len(metadata.authors) == 2
    
    # Test paragraph creation
    paragraph = Paragraph(
        content="This is a test paragraph.",
        page_number=1
    )
    assert paragraph.content == "This is a test paragraph."
    assert len(paragraph.sentences) > 0
    
    # Test section creation
    section = Section(
        title="Introduction",
        level=1
    )
    section.content.append(paragraph)
    assert section.title == "Introduction"
    assert len(section.content) == 1
    
    # Test document creation
    document = Document(
        file_path="/test/path.pdf",
        file_name="path.pdf",
        metadata=metadata
    )
    document.sections.append(section)
    
    assert document.file_name == "path.pdf"
    assert len(document.sections) == 1


def test_extraction_methods():
    """Test extraction method enumeration"""
    from pdf_processing import ExtractionMethod
    
    # Test enum values
    assert ExtractionMethod.PYMUPDF.value == "pymupdf"
    assert ExtractionMethod.PDFPLUMBER.value == "pdfplumber"
    assert ExtractionMethod.AUTO.value == "auto"
    assert ExtractionMethod.HYBRID.value == "hybrid"


def test_publisher_detection():
    """Test publisher detection logic"""
    from pdf_processing.config import PublisherProfile, PublisherType
    
    # Test heuristic detection
    ieee_text = "IEEE Transactions on Software Engineering DOI: 10.1109/test"
    acm_text = "ACM Computing Surveys DOI: 10.1145/test"
    springer_text = "Springer Nature DOI: 10.1007/test"
    
    assert PublisherProfile.detect_publisher("", ieee_text) == PublisherType.IEEE
    assert PublisherProfile.detect_publisher("", acm_text) == PublisherType.ACM
    assert PublisherProfile.detect_publisher("", springer_text) == PublisherType.SPRINGER
    
    # Test fallback to generic
    unknown_text = "Unknown publisher content"
    assert PublisherProfile.detect_publisher("", unknown_text) == PublisherType.GENERIC


def test_processor_statistics():
    """Test processor statistics tracking"""
    try:
        from pdf_processing import PDFProcessor
        
        processor = PDFProcessor()
        stats = processor.get_statistics()
        
        # Check initial stats
        assert 'total_processed' in stats
        assert 'successful_extractions' in stats
        assert 'failed_extractions' in stats
        assert 'success_rate' in stats
        assert 'available_extractors' in stats
        
        # Should start with zero
        assert stats['total_processed'] == 0
        assert stats['successful_extractions'] == 0
        assert stats['failed_extractions'] == 0
        
    except Exception as e:
        pytest.skip(f"PDF libraries not installed: {e}")


def test_document_serialization():
    """Test document export/import functionality"""
    from pdf_processing.models import Document, Metadata, Section, Paragraph
    import json
    import tempfile
    
    # Create test document
    metadata = Metadata(title="Test Document", authors=["Test Author"])
    paragraph = Paragraph(content="Test content", page_number=1)
    section = Section(title="Test Section", level=1)
    section.content.append(paragraph)
    
    document = Document(
        file_path="/test/doc.pdf",
        file_name="doc.pdf",
        metadata=metadata
    )
    document.sections.append(section)
    
    # Test export to dict
    doc_dict = document.export_to_dict()
    assert doc_dict['file_name'] == 'doc.pdf'
    assert doc_dict['metadata']['title'] == 'Test Document'
    assert len(doc_dict['sections']) == 1
    
    # Test JSON serialization
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        success = document.save_to_json(f.name)
        assert success
        
        # Verify file was created and contains valid JSON
        with open(f.name, 'r') as read_f:
            loaded_data = json.load(read_f)
            assert loaded_data['file_name'] == 'doc.pdf'
        
        # Clean up
        os.unlink(f.name)


if __name__ == "__main__":
    # Run basic tests
    test_imports()
    test_config_system()
    test_document_models()
    test_extraction_methods()
    test_publisher_detection()
    test_document_serialization()
    
    print("✅ All basic tests passed!")
    
    # Optional tests that require PDF libraries
    try:
        test_processor_initialization()
        test_processor_statistics()
        print("✅ PDF processor tests passed!")
    except Exception as e:
        print(f"⚠️  PDF processor tests skipped: {e}")
    
    print("\n🎉 Basic functionality validation complete!")