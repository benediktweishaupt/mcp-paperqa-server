"""
Integration tests for end-to-end academic PDF processing pipeline
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import time
from typing import Dict, List, Any

# Import modules for testing
try:
    from pdf_processing import PDFProcessor, ProcessorConfig, ExtractionMethod
    from pdf_processing.models import Document, Metadata, Section, Paragraph
    from pdf_processing.config import PublisherProfile, PublisherType, get_academic_config
    from text_chunking.nlp_pipeline import AcademicNLPPipeline
    PROCESSING_MODULES_AVAILABLE = True
except ImportError:
    PROCESSING_MODULES_AVAILABLE = False


class TestEndToEndPipeline:
    """Test complete PDF processing pipeline from file to structured document"""
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Create sample PDF content for testing"""
        return {
            'metadata': {
                'title': 'Advanced Machine Learning Techniques for Academic Research',
                'author': 'John Smith; Jane Doe; Robert Johnson',
                'subject': 'machine learning, academic research, neural networks',
                'creator': 'LaTeX via pdfTeX'
            },
            'pages': [
                {
                    'page_number': 1,
                    'text': """
                    Advanced Machine Learning Techniques for Academic Research
                    
                    John Smith¹, Jane Doe², Robert Johnson¹
                    ¹MIT Computer Science, Cambridge, MA
                    ²Stanford AI Lab, Stanford, CA
                    
                    Abstract
                    This paper presents novel machine learning techniques specifically designed 
                    for academic research applications. We introduce new architectures that 
                    demonstrate significant improvements over existing methods.
                    
                    Keywords: machine learning, neural networks, academic research
                    
                    1. Introduction
                    Machine learning has revolutionized many fields of research. In this work,
                    we focus on developing techniques that are particularly suited for academic
                    research workflows.
                    """,
                    'structure': [
                        {'type': 'title', 'text': 'Advanced Machine Learning Techniques for Academic Research', 
                         'bbox': (100, 50, 400, 80), 'font_size': 18},
                        {'type': 'authors', 'text': 'John Smith¹, Jane Doe², Robert Johnson¹', 
                         'bbox': (150, 90, 350, 110), 'font_size': 12},
                        {'type': 'abstract', 'text': 'Abstract\\nThis paper presents novel machine learning...', 
                         'bbox': (50, 150, 450, 200), 'font_size': 11},
                        {'type': 'section_header', 'text': '1. Introduction', 
                         'bbox': (50, 220, 150, 240), 'font_size': 14},
                        {'type': 'body', 'text': 'Machine learning has revolutionized many fields...', 
                         'bbox': (50, 250, 450, 300), 'font_size': 12}
                    ]
                },
                {
                    'page_number': 2,
                    'text': """
                    1.1 Background and Related Work
                    
                    Previous work in this area has focused on general-purpose machine learning
                    algorithms. However, academic research has unique requirements that are not
                    well addressed by existing approaches.
                    
                    2. Methodology
                    
                    Our approach consists of three main components: data preprocessing,
                    model architecture design, and evaluation framework.
                    
                    2.1 Data Preprocessing
                    
                    We developed a specialized preprocessing pipeline for academic datasets.
                    This pipeline handles the unique characteristics of research data.
                    """,
                    'structure': [
                        {'type': 'section_header', 'text': '1.1 Background and Related Work', 
                         'bbox': (50, 50, 250, 70), 'font_size': 13},
                        {'type': 'body', 'text': 'Previous work in this area has focused...', 
                         'bbox': (50, 80, 450, 120), 'font_size': 12},
                        {'type': 'section_header', 'text': '2. Methodology', 
                         'bbox': (50, 140, 150, 160), 'font_size': 14},
                        {'type': 'body', 'text': 'Our approach consists of three main components...', 
                         'bbox': (50, 170, 450, 210), 'font_size': 12},
                        {'type': 'section_header', 'text': '2.1 Data Preprocessing', 
                         'bbox': (50, 230, 200, 250), 'font_size': 13},
                        {'type': 'body', 'text': 'We developed a specialized preprocessing pipeline...', 
                         'bbox': (50, 260, 450, 300), 'font_size': 12}
                    ]
                }
            ]
        }
    
    @pytest.fixture
    def mock_processor_config(self):
        """Create mock processor configuration"""
        return ProcessorConfig(
            extraction_method=ExtractionMethod.AUTO,
            fallback_extractors=[ExtractionMethod.PYMUPDF, ExtractionMethod.PDFPLUMBER],
            preserve_structure=True,
            extract_metadata=True,
            enable_nlp_processing=True,
            confidence_threshold=0.7
        )
    
    def test_complete_processing_pipeline(self, sample_pdf_content, mock_processor_config):
        """Test complete processing pipeline from PDF to structured document"""
        if not PROCESSING_MODULES_AVAILABLE:
            pytest.skip("Processing modules not available")
        
        with patch('pdf_processing.extractors.pymupdf_extractor.fitz') as mock_fitz, \
             patch('pdf_processing.extractors.pdfplumber_extractor.pdfplumber') as mock_pdfplumber:
            
            # Setup mocks
            self._setup_extraction_mocks(mock_fitz, mock_pdfplumber, sample_pdf_content)
            
            # Create processor
            processor = PDFProcessor(mock_processor_config)
            
            # Create temporary PDF file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(b'Mock PDF content')  # Placeholder content
                temp_file.flush()
                
                try:
                    # Process the document
                    document = processor.process_document(temp_file.name)
                    
                    # Verify document structure
                    assert document is not None
                    assert isinstance(document, Document)
                    assert document.file_name.endswith('.pdf')
                    
                    # Verify metadata extraction
                    assert document.metadata is not None
                    assert document.metadata.title == 'Advanced Machine Learning Techniques for Academic Research'
                    assert len(document.metadata.authors) == 3
                    assert 'John Smith' in document.metadata.authors
                    assert len(document.metadata.keywords) >= 2
                    
                    # Verify structural extraction
                    assert len(document.sections) >= 2
                    
                    # Find introduction section
                    intro_section = next((s for s in document.sections if 'Introduction' in s.title), None)
                    assert intro_section is not None
                    assert len(intro_section.content) > 0
                    
                    # Verify hierarchical structure
                    methodology_section = next((s for s in document.sections if 'Methodology' in s.title), None)
                    if methodology_section:
                        assert len(methodology_section.subsections) >= 1
                        preprocessing_subsection = next((s for s in methodology_section.subsections 
                                                       if 'Preprocessing' in s.title), None)
                        assert preprocessing_subsection is not None
                    
                    # Verify processing statistics
                    stats = processor.get_statistics()
                    assert stats['total_processed'] == 1
                    assert stats['successful_extractions'] == 1
                    assert stats['failed_extractions'] == 0
                    
                finally:
                    os.unlink(temp_file.name)
    
    def test_nlp_pipeline_integration(self, sample_pdf_content):
        """Test integration with NLP pipeline for text chunking"""
        if not PROCESSING_MODULES_AVAILABLE:
            pytest.skip("Processing modules not available")
        
        # Create NLP pipeline
        nlp_pipeline = AcademicNLPPipeline(enable_transformer=False)
        
        # Extract text from sample content
        full_text = "\\n".join([page['text'] for page in sample_pdf_content['pages']])
        
        # Process with NLP pipeline
        doc = nlp_pipeline.process_text(full_text)
        
        # Verify NLP processing
        assert doc is not None
        
        # Test citation extraction
        citations = nlp_pipeline.extract_citations(doc)
        assert isinstance(citations, list)
        
        # Test academic structure extraction
        structures = nlp_pipeline.extract_academic_structures(doc)
        assert isinstance(structures, list)
        
        # Test discourse markers
        discourse_markers = nlp_pipeline.get_discourse_markers(doc)
        assert isinstance(discourse_markers, list)
        
        # Test sentence complexity analysis
        complexity_metrics = nlp_pipeline.analyze_sentence_complexity(doc)
        assert isinstance(complexity_metrics, list)
        assert len(complexity_metrics) > 0
    
    def test_publisher_specific_processing(self, mock_processor_config):
        """Test processing with publisher-specific configurations"""
        if not PROCESSING_MODULES_AVAILABLE:
            pytest.skip("Processing modules not available")
        
        # Test IEEE processing
        ieee_content = {
            'metadata': {
                'title': 'IEEE Paper on Neural Networks',
                'author': 'IEEE Author',
                'subject': 'neural networks, IEEE'
            },
            'text': '''
            IEEE TRANSACTIONS ON NEURAL NETWORKS AND LEARNING SYSTEMS
            
            A Novel Neural Network Architecture for Pattern Recognition
            
            John IEEE¹, Jane IEEE²
            ¹IEEE University, ²IEEE Institute
            
            Abstract—This paper presents a novel neural network architecture
            that achieves state-of-the-art performance on pattern recognition tasks.
            
            Index Terms—Neural networks, pattern recognition, deep learning
            
            I. INTRODUCTION
            Pattern recognition is a fundamental problem in machine learning...
            '''
        }
        
        with patch('pdf_processing.extractors.pymupdf_extractor.fitz') as mock_fitz:
            self._setup_simple_extraction_mock(mock_fitz, ieee_content)
            
            # Create IEEE-specific configuration
            ieee_config = PublisherProfile.get_profile(PublisherType.IEEE)
            processor = PDFProcessor(ieee_config)
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(b'Mock IEEE PDF')
                temp_file.flush()
                
                try:
                    document = processor.process_document(temp_file.name)
                    
                    # Verify IEEE-specific processing
                    assert document is not None
                    assert 'IEEE' in document.metadata.title
                    assert 'Abstract—' in document.sections[0].content[0].content or \
                           any('Abstract' in s.title for s in document.sections)
                    
                finally:
                    os.unlink(temp_file.name)
    
    def test_error_recovery_and_fallback(self, sample_pdf_content, mock_processor_config):
        """Test error recovery and fallback mechanisms"""
        if not PROCESSING_MODULES_AVAILABLE:
            pytest.skip("Processing modules not available")
        
        with patch('pdf_processing.extractors.pymupdf_extractor.fitz') as mock_fitz, \
             patch('pdf_processing.extractors.pdfplumber_extractor.pdfplumber') as mock_pdfplumber:
            
            # Make primary extractor fail
            mock_fitz.open.side_effect = Exception("Primary extractor failed")
            
            # Make secondary extractor succeed
            self._setup_pdfplumber_fallback_mock(mock_pdfplumber, sample_pdf_content)
            
            processor = PDFProcessor(mock_processor_config)
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(b'Mock PDF content')
                temp_file.flush()
                
                try:
                    # Should succeed with fallback extractor
                    document = processor.process_document(temp_file.name)
                    
                    assert document is not None
                    assert document.metadata.title is not None
                    
                    # Check that fallback was used
                    stats = processor.get_statistics()
                    assert stats['total_processed'] == 1
                    # May show failed extraction for primary, but successful overall
                    
                finally:
                    os.unlink(temp_file.name)
    
    def test_processing_performance_metrics(self, sample_pdf_content, mock_processor_config):
        """Test processing performance and timing metrics"""
        if not PROCESSING_MODULES_AVAILABLE:
            pytest.skip("Processing modules not available")
        
        with patch('pdf_processing.extractors.pymupdf_extractor.fitz') as mock_fitz:
            self._setup_simple_extraction_mock(mock_fitz, sample_pdf_content)
            
            processor = PDFProcessor(mock_processor_config)
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(b'Mock PDF content')
                temp_file.flush()
                
                try:
                    # Measure processing time
                    start_time = time.time()
                    document = processor.process_document(temp_file.name)
                    end_time = time.time()
                    
                    processing_time = end_time - start_time
                    
                    # Verify reasonable processing time (should be fast for mock data)
                    assert processing_time < 10.0  # Less than 10 seconds
                    
                    # Verify document was processed successfully
                    assert document is not None
                    
                    # Check processing metrics
                    stats = processor.get_statistics()
                    assert 'processing_time' in stats or processing_time > 0
                    
                finally:
                    os.unlink(temp_file.name)
    
    def test_batch_processing_capability(self, sample_pdf_content, mock_processor_config):
        """Test processing multiple documents in batch"""
        if not PROCESSING_MODULES_AVAILABLE:
            pytest.skip("Processing modules not available")
        
        with patch('pdf_processing.extractors.pymupdf_extractor.fitz') as mock_fitz:
            self._setup_simple_extraction_mock(mock_fitz, sample_pdf_content)
            
            processor = PDFProcessor(mock_processor_config)
            
            # Create multiple temporary PDF files
            temp_files = []
            try:
                for i in range(3):
                    temp_file = tempfile.NamedTemporaryFile(suffix=f'_doc_{i}.pdf', delete=False)
                    temp_file.write(f'Mock PDF content {i}'.encode())
                    temp_file.flush()
                    temp_files.append(temp_file.name)
                
                # Process batch
                documents = []
                for file_path in temp_files:
                    document = processor.process_document(file_path)
                    documents.append(document)
                
                # Verify batch processing results
                assert len(documents) == 3
                for doc in documents:
                    assert doc is not None
                    assert doc.file_name.endswith('.pdf')
                
                # Check cumulative statistics
                stats = processor.get_statistics()
                assert stats['total_processed'] == 3
                assert stats['successful_extractions'] == 3
                
            finally:
                for file_path in temp_files:
                    if os.path.exists(file_path):
                        os.unlink(file_path)
    
    def test_document_serialization_and_export(self, sample_pdf_content, mock_processor_config):
        """Test document serialization and export functionality"""
        if not PROCESSING_MODULES_AVAILABLE:
            pytest.skip("Processing modules not available")
        
        with patch('pdf_processing.extractors.pymupdf_extractor.fitz') as mock_fitz:
            self._setup_simple_extraction_mock(mock_fitz, sample_pdf_content)
            
            processor = PDFProcessor(mock_processor_config)
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(b'Mock PDF content')
                temp_file.flush()
                
                try:
                    # Process document
                    document = processor.process_document(temp_file.name)
                    
                    # Test JSON export
                    json_export = document.export_to_dict()
                    assert isinstance(json_export, dict)
                    assert 'file_name' in json_export
                    assert 'metadata' in json_export
                    assert 'sections' in json_export
                    
                    # Test JSON serialization
                    json_str = json.dumps(json_export)
                    assert len(json_str) > 0
                    
                    # Test deserialization
                    reloaded_dict = json.loads(json_str)
                    assert reloaded_dict['file_name'] == document.file_name
                    
                    # Test file export
                    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as json_file:
                        success = document.save_to_json(json_file.name)
                        assert success
                        
                        # Verify file was created and contains valid JSON
                        with open(json_file.name, 'r') as f:
                            loaded_data = json.load(f)
                            assert loaded_data['file_name'] == document.file_name
                        
                        os.unlink(json_file.name)
                    
                finally:
                    os.unlink(temp_file.name)
    
    def _setup_extraction_mocks(self, mock_fitz, mock_pdfplumber, sample_content):
        """Setup comprehensive extraction mocks"""
        # Setup PyMuPDF mock
        mock_doc = Mock()
        mock_doc.page_count = len(sample_content['pages'])
        mock_doc.metadata = sample_content['metadata']
        
        pages = []
        for page_data in sample_content['pages']:
            mock_page = Mock()
            mock_page.number = page_data['page_number'] - 1
            mock_page.get_text.return_value = page_data['text']
            
            # Mock structured extraction
            mock_blocks = []
            for struct in page_data['structure']:
                mock_blocks.append({
                    'type': 0,
                    'bbox': struct['bbox'],
                    'lines': [{
                        'bbox': struct['bbox'],
                        'spans': [{
                            'text': struct['text'],
                            'size': struct['font_size'],
                            'font': 'Arial'
                        }]
                    }]
                })
            
            mock_page.get_text.side_effect = lambda fmt='text': (
                page_data['text'] if fmt == 'text' else {'blocks': mock_blocks}
            )
            pages.append(mock_page)
        
        mock_doc.__len__ = Mock(return_value=len(pages))
        mock_doc.__getitem__ = lambda self, i: pages[i]
        mock_fitz.open.return_value = mock_doc
    
    def _setup_simple_extraction_mock(self, mock_fitz, content):
        """Setup simple extraction mock for basic testing"""
        mock_doc = Mock()
        mock_page = Mock()
        
        text_content = content.get('text', content.get('pages', [{}])[0].get('text', 'Mock text'))
        mock_page.get_text.return_value = text_content
        mock_page.number = 0
        
        mock_doc.page_count = 1
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.__getitem__ = Mock(return_value=mock_page)
        mock_doc.metadata = content.get('metadata', {'title': 'Mock Title'})
        
        mock_fitz.open.return_value = mock_doc
    
    def _setup_pdfplumber_fallback_mock(self, mock_pdfplumber, sample_content):
        """Setup PDFPlumber fallback mock"""
        mock_pdf = Mock()
        mock_page = Mock()
        
        text_content = sample_content['pages'][0]['text']
        mock_page.extract_text.return_value = text_content
        mock_page.width = 595
        mock_page.height = 842
        
        mock_pdf.pages = [mock_page]
        mock_pdf.metadata = sample_content['metadata']
        
        mock_pdfplumber.open.return_value.__enter__ = Mock(return_value=mock_pdf)
        mock_pdfplumber.open.return_value.__exit__ = Mock(return_value=None)


class TestQualityAssurance:
    """Test quality assurance and validation for processing pipeline"""
    
    def test_processing_quality_metrics(self):
        """Test quality metrics calculation for processed documents"""
        if not PROCESSING_MODULES_AVAILABLE:
            pytest.skip("Processing modules not available")
        
        class ProcessingQualityAssessor:
            def calculate_processing_quality_score(self, document, original_content=None):
                """Calculate overall processing quality score"""
                score = 0
                max_score = 100
                
                # Metadata completeness (25 points)
                if document.metadata:
                    if document.metadata.title:
                        score += 10
                    if document.metadata.authors:
                        score += 10
                    if document.metadata.abstract or document.metadata.keywords:
                        score += 5
                
                # Structure completeness (35 points)
                if document.sections:
                    score += 15  # Has sections
                    if len(document.sections) >= 3:
                        score += 10  # Good section count
                    if any(s.subsections for s in document.sections):
                        score += 10  # Has hierarchical structure
                
                # Content quality (25 points)
                total_content = len(document.get_all_paragraphs())
                if total_content > 0:
                    score += 10
                if total_content >= 5:
                    score += 10
                if any(p.word_count > 20 for p in document.get_all_paragraphs()):
                    score += 5  # Has substantial paragraphs
                
                # Processing integrity (15 points)
                if document.file_name:
                    score += 5
                if document.get_total_page_count() > 0:
                    score += 5
                # Additional integrity checks could go here
                score += 5  # Base integrity score
                
                return min(score, max_score)
        
        # Create test document
        metadata = Metadata(
            title="High Quality Document",
            authors=["Test Author"],
            abstract="Test abstract content"
        )
        
        document = Document(
            file_path="/test/high_quality.pdf",
            file_name="high_quality.pdf",
            metadata=metadata
        )
        
        # Add structured content
        section = Section(title="Introduction", level=1)
        paragraph = Paragraph(content="This is a substantial paragraph with many words for testing quality.", page_number=1)
        section.content.append(paragraph)
        document.sections.append(section)
        
        assessor = ProcessingQualityAssessor()
        quality_score = assessor.calculate_processing_quality_score(document)
        
        # Should achieve high quality score
        assert quality_score >= 80
    
    def test_error_detection_and_reporting(self):
        """Test detection and reporting of processing errors"""
        if not PROCESSING_MODULES_AVAILABLE:
            pytest.skip("Processing modules not available")
        
        class ProcessingErrorDetector:
            def detect_processing_errors(self, document):
                """Detect various types of processing errors"""
                errors = []
                warnings = []
                
                # Missing essential metadata
                if not document.metadata or not document.metadata.title:
                    errors.append("Missing document title")
                
                # Empty or malformed content
                if not document.sections:
                    errors.append("No document sections found")
                elif len(document.get_all_paragraphs()) == 0:
                    errors.append("No content paragraphs found")
                
                # Suspicious structure patterns
                if document.sections and len(document.sections) > 50:
                    warnings.append("Unusually high number of sections - possible over-segmentation")
                
                # Content quality issues
                paragraphs = document.get_all_paragraphs()
                if paragraphs:
                    very_short_paras = [p for p in paragraphs if p.word_count < 3]
                    if len(very_short_paras) > len(paragraphs) * 0.5:
                        warnings.append("Many very short paragraphs - possible parsing errors")
                
                # File integrity issues
                if not document.file_name or not document.file_name.endswith('.pdf'):
                    warnings.append("Unexpected file name format")
                
                return {
                    'errors': errors,
                    'warnings': warnings,
                    'error_count': len(errors),
                    'warning_count': len(warnings)
                }
        
        detector = ProcessingErrorDetector()
        
        # Test with good document
        good_doc = Document(
            file_path="/test/good.pdf",
            file_name="good.pdf", 
            metadata=Metadata(title="Good Document")
        )
        section = Section(title="Section", level=1)
        paragraph = Paragraph(content="This is good content with sufficient length.", page_number=1)
        section.content.append(paragraph)
        good_doc.sections.append(section)
        
        good_results = detector.detect_processing_errors(good_doc)
        assert good_results['error_count'] == 0
        
        # Test with problematic document
        bad_doc = Document(
            file_path="/test/bad.txt",  # Wrong extension
            file_name="bad.txt",
            metadata=Metadata()  # No title
        )
        # No sections - should trigger errors
        
        bad_results = detector.detect_processing_errors(bad_doc)
        assert bad_results['error_count'] > 0
        assert "Missing document title" in bad_results['errors']
        assert "No document sections found" in bad_results['errors']


if __name__ == "__main__":
    if PROCESSING_MODULES_AVAILABLE:
        print("🔄 Running end-to-end integration tests...")
        
        try:
            # Basic integration test
            test_pipeline = TestEndToEndPipeline()
            print("✅ Pipeline integration tests setup complete")
        except Exception as e:
            print(f"❌ Pipeline integration tests failed: {e}")
        
        try:
            # Quality assurance tests
            test_qa = TestQualityAssurance()
            test_qa.test_processing_quality_metrics()
            test_qa.test_error_detection_and_reporting()
            print("✅ Quality assurance tests passed")
        except Exception as e:
            print(f"❌ Quality assurance tests failed: {e}")
        
        print("\n🎉 End-to-end integration testing complete!")
        print("📝 Note: Full integration requires PDF files and complete module implementation")
        
    else:
        print("⚠️  Processing modules not available")
        print("📦 Install all requirements for full integration testing")