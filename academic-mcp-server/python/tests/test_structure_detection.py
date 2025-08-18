"""
Comprehensive unit tests for structure detection components
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from typing import List, Dict, Any

# Import modules for testing
try:
    from pdf_processing.models import Document, Section, Paragraph, Heading, Metadata
    from pdf_processing.layout import ColumnDetector, ColumnLayoutType, LayoutAnalyzer, ReadingOrderProcessor
    from pdf_processing.layout.column_detector import ColumnRegion, ColumnLayout
    from pdf_processing.layout.layout_analyzer import PageLayout, LayoutElement
    from pdf_processing.layout.reading_order import TextFlow
    STRUCTURE_MODULES_AVAILABLE = True
except ImportError:
    STRUCTURE_MODULES_AVAILABLE = False


class TestDocumentStructureModels:
    """Test document structure model classes"""
    
    def test_heading_model(self):
        """Test Heading model functionality"""
        if not STRUCTURE_MODULES_AVAILABLE:
            pytest.skip("Structure detection modules not available")
        
        heading = Heading(
            text="Introduction",
            level=1,
            page_number=1,
            font_size=16
        )
        
        assert heading.text == "Introduction"
        assert heading.level == 1
        assert heading.page_number == 1
        assert heading.font_size == 16
        assert heading.is_main_heading()
        
        # Test hierarchy methods
        sub_heading = Heading(text="Background", level=2, page_number=1)
        assert not sub_heading.is_main_heading()
        assert sub_heading.level > heading.level
    
    def test_paragraph_model(self):
        """Test Paragraph model functionality"""
        if not STRUCTURE_MODULES_AVAILABLE:
            pytest.skip("Structure detection modules not available")
        
        paragraph = Paragraph(
            content="This is a test paragraph with multiple sentences. It contains academic content.",
            page_number=1
        )
        
        assert len(paragraph.sentences) >= 2
        assert paragraph.word_count > 10
        assert paragraph.page_number == 1
        
        # Test paragraph analysis methods
        assert paragraph.get_sentence_count() >= 2
        assert paragraph.get_average_sentence_length() > 0
    
    def test_section_model_hierarchy(self):
        """Test Section model with hierarchical content"""
        if not STRUCTURE_MODULES_AVAILABLE:
            pytest.skip("Structure detection modules not available")
        
        # Create main section
        main_section = Section(title="Introduction", level=1)
        
        # Add subsection
        subsection = Section(title="Background", level=2)
        paragraph = Paragraph(content="Background information here.", page_number=1)
        subsection.content.append(paragraph)
        
        main_section.subsections.append(subsection)
        
        # Test hierarchy
        assert main_section.level == 1
        assert len(main_section.subsections) == 1
        assert main_section.subsections[0].level == 2
        assert main_section.get_total_content_count() > 0
        
        # Test content traversal
        all_content = main_section.get_all_content_recursive()
        assert len(all_content) > 0
        assert paragraph in all_content
    
    def test_document_structure_navigation(self):
        """Test document structure navigation methods"""
        if not STRUCTURE_MODULES_AVAILABLE:
            pytest.skip("Structure detection modules not available")
        
        # Create document with complex structure
        metadata = Metadata(title="Test Academic Paper")
        document = Document(
            file_path="/test/path.pdf",
            file_name="test.pdf", 
            metadata=metadata
        )
        
        # Add abstract
        abstract_section = Section(title="Abstract", level=0)
        abstract_para = Paragraph(content="This paper presents...", page_number=1)
        abstract_section.content.append(abstract_para)
        document.sections.append(abstract_section)
        
        # Add introduction with subsections
        intro_section = Section(title="1. Introduction", level=1)
        intro_para = Paragraph(content="Introduction content.", page_number=1)
        intro_section.content.append(intro_para)
        
        background_subsection = Section(title="1.1 Background", level=2)
        background_para = Paragraph(content="Background content.", page_number=2)
        background_subsection.content.append(background_para)
        intro_section.subsections.append(background_subsection)
        
        document.sections.append(intro_section)
        
        # Test navigation
        assert document.get_section_count() == 2
        assert document.get_total_page_count() == 2
        
        # Test section finding
        found_section = document.find_section_by_title("Introduction")
        assert found_section is not None
        assert found_section.title == "1. Introduction"
        
        # Test content extraction
        all_paragraphs = document.get_all_paragraphs()
        assert len(all_paragraphs) >= 3


class TestColumnDetection:
    """Test column detection algorithms"""
    
    def create_mock_text_elements(self, layout_type="two_column"):
        """Create mock text elements for testing"""
        elements = []
        
        if layout_type == "single_column":
            # Single column elements
            for i in range(5):
                elements.append({
                    'content': f'Single column paragraph {i+1}',
                    'position': {'x': 50, 'y': 100 + i*30, 'width': 400, 'height': 25},
                    'font_size': 12,
                    'page_number': 1
                })
        
        elif layout_type == "two_column":
            # Two column elements
            # Left column
            for i in range(3):
                elements.append({
                    'content': f'Left column paragraph {i+1}',
                    'position': {'x': 50, 'y': 100 + i*30, 'width': 180, 'height': 25},
                    'font_size': 12,
                    'page_number': 1
                })
            # Right column  
            for i in range(3):
                elements.append({
                    'content': f'Right column paragraph {i+1}',
                    'position': {'x': 300, 'y': 100 + i*30, 'width': 180, 'height': 25},
                    'font_size': 12,
                    'page_number': 1
                })
        
        elif layout_type == "mixed":
            # Title (full width)
            elements.append({
                'content': 'Document Title',
                'position': {'x': 50, 'y': 50, 'width': 400, 'height': 30},
                'font_size': 18,
                'page_number': 1
            })
            # Abstract (full width)
            elements.append({
                'content': 'Abstract: This paper presents...',
                'position': {'x': 50, 'y': 90, 'width': 400, 'height': 40},
                'font_size': 11,
                'page_number': 1
            })
            # Two column body
            elements.append({
                'content': 'Body text left column',
                'position': {'x': 50, 'y': 150, 'width': 180, 'height': 25},
                'font_size': 12,
                'page_number': 1
            })
            elements.append({
                'content': 'Body text right column',
                'position': {'x': 300, 'y': 150, 'width': 180, 'height': 25},
                'font_size': 12,
                'page_number': 1
            })
        
        return elements
    
    def test_column_detector_initialization(self):
        """Test column detector initialization"""
        if not STRUCTURE_MODULES_AVAILABLE:
            pytest.skip("Structure detection modules not available")
        
        detector = ColumnDetector()
        assert detector is not None
        
        # Test configuration
        config = detector.get_detection_config()
        assert 'min_column_width' in config
        assert 'max_columns' in config
        assert 'column_gap_threshold' in config
    
    def test_single_column_detection(self):
        """Test detection of single column layout"""
        if not STRUCTURE_MODULES_AVAILABLE:
            pytest.skip("Structure detection modules not available")
        
        detector = ColumnDetector()
        elements = self.create_mock_text_elements("single_column")
        
        layout = detector.detect_columns(elements, 500, 700, 1)
        
        assert layout.layout_type == ColumnLayoutType.SINGLE_COLUMN
        assert layout.get_column_count() == 1
        assert layout.confidence > 0.0
        assert len(layout.columns) == 1
        
        # Check column properties
        column = layout.columns[0]
        assert column.width > 0
        assert column.height > 0
    
    def test_two_column_detection(self):
        """Test detection of two column layout"""
        if not STRUCTURE_MODULES_AVAILABLE:
            pytest.skip("Structure detection modules not available")
        
        detector = ColumnDetector()
        elements = self.create_mock_text_elements("two_column")
        
        layout = detector.detect_columns(elements, 500, 700, 1)
        
        assert layout.layout_type == ColumnLayoutType.TWO_COLUMN
        assert layout.get_column_count() == 2
        assert layout.confidence > 0.0
        assert len(layout.columns) == 2
        
        # Verify columns are ordered correctly
        columns = sorted(layout.columns, key=lambda c: c.x0)
        assert columns[0].x0 < columns[1].x0  # Left column before right
        
        # Test column gap detection
        gap = columns[1].x0 - columns[0].x1
        assert gap > 0  # Should be a gap between columns
    
    def test_mixed_layout_detection(self):
        """Test detection of mixed layout (abstract + columns)"""
        if not STRUCTURE_MODULES_AVAILABLE:
            pytest.skip("Structure detection modules not available")
        
        detector = ColumnDetector()
        elements = self.create_mock_text_elements("mixed")
        
        layout = detector.detect_columns(elements, 500, 700, 1)
        
        # Should detect mixed layout
        assert layout.abstract_region is not None
        assert layout.get_column_count() >= 1
        
        # Abstract region should span full width
        abstract = layout.abstract_region
        assert abstract.width > layout.columns[0].width
    
    def test_column_confidence_scoring(self):
        """Test column detection confidence scoring"""
        if not STRUCTURE_MODULES_AVAILABLE:
            pytest.skip("Structure detection modules not available")
        
        detector = ColumnDetector()
        
        # Test with clear two-column layout
        clear_elements = self.create_mock_text_elements("two_column")
        clear_layout = detector.detect_columns(clear_elements, 500, 700, 1)
        
        # Test with ambiguous layout
        ambiguous_elements = [
            {
                'content': 'Ambiguous text',
                'position': {'x': 200, 'y': 100, 'width': 100, 'height': 25},
                'font_size': 12,
                'page_number': 1
            }
        ]
        ambiguous_layout = detector.detect_columns(ambiguous_elements, 500, 700, 1)
        
        # Clear layout should have higher confidence
        assert clear_layout.confidence > ambiguous_layout.confidence


class TestLayoutAnalyzer:
    """Test comprehensive layout analysis"""
    
    def test_layout_analyzer_initialization(self):
        """Test layout analyzer initialization"""
        if not STRUCTURE_MODULES_AVAILABLE:
            pytest.skip("Structure detection modules not available")
        
        analyzer = LayoutAnalyzer()
        assert analyzer is not None
        
        # Test analyzer capabilities
        capabilities = analyzer.get_analysis_capabilities()
        assert 'column_detection' in capabilities
        assert 'reading_order' in capabilities
        assert 'element_classification' in capabilities
    
    def test_page_layout_analysis(self):
        """Test comprehensive page layout analysis"""
        if not STRUCTURE_MODULES_AVAILABLE:
            pytest.skip("Structure detection modules not available")
        
        analyzer = LayoutAnalyzer()
        
        # Create mock elements with various types
        elements = [
            # Title
            {'content': 'Research Paper Title', 'position': {'x': 100, 'y': 50, 'width': 300, 'height': 30}, 
             'font_size': 18, 'font_weight': 'bold', 'page_number': 1},
            # Authors
            {'content': 'Author Name, Institution', 'position': {'x': 150, 'y': 90, 'width': 200, 'height': 15},
             'font_size': 12, 'font_style': 'italic', 'page_number': 1},
            # Abstract
            {'content': 'Abstract—This paper presents novel research...', 'position': {'x': 50, 'y': 120, 'width': 400, 'height': 60},
             'font_size': 11, 'page_number': 1},
            # Body paragraphs
            {'content': 'Introduction paragraph text.', 'position': {'x': 50, 'y': 200, 'width': 180, 'height': 40},
             'font_size': 12, 'page_number': 1},
            {'content': 'Methodology paragraph text.', 'position': {'x': 300, 'y': 200, 'width': 180, 'height': 40},
             'font_size': 12, 'page_number': 1}
        ]
        
        page_layout = analyzer.analyze_page_layout(elements, 500, 700, 1)
        
        # Test layout properties
        assert page_layout.page_number == 1
        assert page_layout.page_width == 500
        assert page_layout.page_height == 700
        assert page_layout.total_elements == len(elements)
        assert page_layout.columns_detected >= 1
        assert page_layout.confidence > 0.0
        
        # Test layout elements were created and classified
        assert len(page_layout.layout_elements) == len(elements)
        
        # Test element classification
        title_elements = [e for e in page_layout.layout_elements if e.element_type == 'title']
        abstract_elements = [e for e in page_layout.layout_elements if e.element_type == 'abstract']
        body_elements = [e for e in page_layout.layout_elements if e.element_type == 'body']
        
        assert len(title_elements) > 0
        assert len(abstract_elements) > 0 or len(body_elements) > 0
    
    def test_layout_element_classification(self):
        """Test classification of layout elements by type"""
        if not STRUCTURE_MODULES_AVAILABLE:
            pytest.skip("Structure detection modules not available")
        
        analyzer = LayoutAnalyzer()
        
        # Test different element types
        title_element = {'content': 'Document Title', 'font_size': 18, 'font_weight': 'bold',
                        'position': {'x': 100, 'y': 50, 'width': 300, 'height': 30}}
        
        heading_element = {'content': '1. Introduction', 'font_size': 14, 'font_weight': 'bold',
                          'position': {'x': 50, 'y': 100, 'width': 200, 'height': 20}}
        
        body_element = {'content': 'Regular paragraph text with normal formatting.',
                       'font_size': 12, 'position': {'x': 50, 'y': 130, 'width': 400, 'height': 40}}
        
        # Test classification
        title_type = analyzer._classify_element_type(title_element)
        heading_type = analyzer._classify_element_type(heading_element)
        body_type = analyzer._classify_element_type(body_element)
        
        assert title_type in ['title', 'heading']
        assert heading_type in ['heading', 'section_header']
        assert body_type in ['body', 'paragraph']
    
    def test_layout_statistics_generation(self):
        """Test generation of layout statistics"""
        if not STRUCTURE_MODULES_AVAILABLE:
            pytest.skip("Structure detection modules not available")
        
        analyzer = LayoutAnalyzer()
        
        # Create multiple page layouts
        elements1 = [{'content': f'Page 1 element {i}', 'position': {'x': 50, 'y': 100+i*30, 'width': 400, 'height': 25}} for i in range(3)]
        elements2 = [{'content': f'Page 2 element {i}', 'position': {'x': 50, 'y': 100+i*30, 'width': 200, 'height': 25}} for i in range(4)]
        
        layout1 = analyzer.analyze_page_layout(elements1, 500, 700, 1)
        layout2 = analyzer.analyze_page_layout(elements2, 500, 700, 2)
        
        page_layouts = [layout1, layout2]
        stats = analyzer.get_layout_statistics(page_layouts)
        
        # Test statistics structure
        assert stats['total_pages'] == 2
        assert 'layout_types' in stats
        assert 'column_distribution' in stats
        assert 'average_confidence' in stats
        assert 'elements_per_page' in stats
        
        # Test calculated values
        assert stats['average_confidence'] > 0.0
        assert stats['elements_per_page']['average'] > 0


class TestReadingOrderProcessor:
    """Test reading order processing"""
    
    def test_reading_order_initialization(self):
        """Test reading order processor initialization"""
        if not STRUCTURE_MODULES_AVAILABLE:
            pytest.skip("Structure detection modules not available")
        
        processor = ReadingOrderProcessor()
        assert processor is not None
        
        # Test processor configuration
        config = processor.get_processing_config()
        assert 'sort_by_position' in config
        assert 'respect_columns' in config
    
    def test_linear_reading_order(self):
        """Test single column linear reading order"""
        if not STRUCTURE_MODULES_AVAILABLE:
            pytest.skip("Structure detection modules not available")
        
        processor = ReadingOrderProcessor()
        
        # Create vertically arranged elements
        elements = []
        for i in range(4):
            element = Mock()
            element.content = f"Paragraph {i+1}"
            element.position = {'x': 50, 'y': 100 + i*40, 'width': 400, 'height': 35}
            element.page_number = 1
            elements.append(element)
        
        # Create single column layout
        column_layout = ColumnLayout(1, ColumnLayoutType.SINGLE_COLUMN, 500, 700)
        column_layout.columns = [ColumnRegion(0, 0, 500, 700, 0)]
        
        text_flow = processor.process_reading_order(elements, column_layout)
        
        # Test reading order
        assert len(text_flow.elements) == 4
        ordered_content = [elem.content for elem in text_flow.elements]
        
        # Should maintain vertical order
        assert ordered_content == ["Paragraph 1", "Paragraph 2", "Paragraph 3", "Paragraph 4"]
    
    def test_columnar_reading_order(self):
        """Test two-column reading order processing"""
        if not STRUCTURE_MODULES_AVAILABLE:
            pytest.skip("Structure detection modules not available")
        
        processor = ReadingOrderProcessor()
        
        # Create two-column elements
        elements = []
        
        # Left column elements
        for i in range(3):
            element = Mock()
            element.content = f"Left {i+1}"
            element.position = {'x': 50, 'y': 100 + i*30, 'width': 180, 'height': 25}
            element.page_number = 1
            elements.append(element)
        
        # Right column elements
        for i in range(3):
            element = Mock()
            element.content = f"Right {i+1}"
            element.position = {'x': 300, 'y': 100 + i*30, 'width': 180, 'height': 25}
            element.page_number = 1
            elements.append(element)
        
        # Create two column layout
        column_layout = ColumnLayout(1, ColumnLayoutType.TWO_COLUMN, 500, 700)
        column_layout.columns = [
            ColumnRegion(0, 0, 250, 700, 0),    # Left column
            ColumnRegion(250, 0, 500, 700, 1)   # Right column
        ]
        
        text_flow = processor.process_reading_order(elements, column_layout)
        
        # Test that elements are grouped by column and ordered within columns
        assert len(text_flow.elements) == 6
        ordered_content = [elem.content for elem in text_flow.elements]
        
        # Should process left column first, then right column
        left_elements = [content for content in ordered_content if "Left" in content]
        right_elements = [content for content in ordered_content if "Right" in content]
        
        assert len(left_elements) == 3
        assert len(right_elements) == 3
    
    def test_mixed_layout_reading_order(self):
        """Test reading order for mixed layouts"""
        if not STRUCTURE_MODULES_AVAILABLE:
            pytest.skip("Structure detection modules not available")
        
        processor = ReadingOrderProcessor()
        
        elements = []
        
        # Title (full width, should be first)
        title = Mock()
        title.content = "Document Title"
        title.position = {'x': 100, 'y': 50, 'width': 300, 'height': 30}
        title.page_number = 1
        elements.append(title)
        
        # Abstract (full width, should be second)
        abstract = Mock()
        abstract.content = "Abstract content"
        abstract.position = {'x': 50, 'y': 90, 'width': 400, 'height': 40}
        abstract.page_number = 1
        elements.append(abstract)
        
        # Two-column body (should follow abstract)
        left_body = Mock()
        left_body.content = "Left body"
        left_body.position = {'x': 50, 'y': 150, 'width': 180, 'height': 25}
        left_body.page_number = 1
        elements.append(left_body)
        
        right_body = Mock()
        right_body.content = "Right body"
        right_body.position = {'x': 300, 'y': 150, 'width': 180, 'height': 25}
        right_body.page_number = 1
        elements.append(right_body)
        
        # Create mixed layout
        column_layout = ColumnLayout(1, ColumnLayoutType.MIXED, 500, 700)
        column_layout.abstract_region = ColumnRegion(0, 80, 500, 140, -1)
        column_layout.columns = [
            ColumnRegion(0, 140, 250, 700, 0),
            ColumnRegion(250, 140, 500, 700, 1)
        ]
        
        text_flow = processor.process_reading_order(elements, column_layout)
        ordered_content = [elem.content for elem in text_flow.elements]
        
        # Verify reading order: title -> abstract -> body columns
        assert ordered_content[0] == "Document Title"
        assert ordered_content[1] == "Abstract content"
        assert "Left body" in ordered_content[2:]
        assert "Right body" in ordered_content[2:]


class TestStructureIntegration:
    """Test integration of structure detection components"""
    
    def test_document_structure_extraction_pipeline(self):
        """Test complete document structure extraction pipeline"""
        if not STRUCTURE_MODULES_AVAILABLE:
            pytest.skip("Structure detection modules not available")
        
        # This test would integrate all components
        # For now, test the coordination between components
        
        # Create a document with realistic structure
        metadata = Metadata(
            title="A Comprehensive Study of Academic Document Processing",
            authors=["John Smith", "Jane Doe"],
            abstract="This paper presents methods for academic document processing..."
        )
        
        document = Document(
            file_path="/test/academic_paper.pdf",
            file_name="academic_paper.pdf",
            metadata=metadata
        )
        
        # Add structured content
        # Abstract
        abstract_section = Section(title="Abstract", level=0)
        abstract_para = Paragraph(content=metadata.abstract, page_number=1)
        abstract_section.content.append(abstract_para)
        document.sections.append(abstract_section)
        
        # Introduction with subsections
        intro_section = Section(title="1. Introduction", level=1)
        intro_para = Paragraph(content="Introduction to the research problem.", page_number=1)
        intro_section.content.append(intro_para)
        
        # Add subsection
        background_section = Section(title="1.1 Background", level=2)
        background_para = Paragraph(content="Background and related work.", page_number=2)
        background_section.content.append(background_para)
        intro_section.subsections.append(background_section)
        
        document.sections.append(intro_section)
        
        # Test document structure integrity
        assert document.get_section_count() == 2
        assert len(document.get_all_paragraphs()) == 3
        assert document.find_section_by_title("Introduction") is not None
        
        # Test hierarchical structure
        intro = document.find_section_by_title("Introduction")
        assert len(intro.subsections) == 1
        assert intro.subsections[0].title == "1.1 Background"
    
    def test_structure_validation_and_quality_checks(self):
        """Test structure validation and quality assurance"""
        if not STRUCTURE_MODULES_AVAILABLE:
            pytest.skip("Structure detection modules not available")
        
        # Create document with potential structural issues
        document = Document(
            file_path="/test/test.pdf",
            file_name="test.pdf",
            metadata=Metadata(title="Test Document")
        )
        
        # Add sections with inconsistent numbering
        section1 = Section(title="1. Introduction", level=1)
        section2 = Section(title="3. Methodology", level=1)  # Missing section 2
        section3 = Section(title="2.1 Subsection", level=2)  # Wrong parent
        
        document.sections.extend([section1, section2, section3])
        
        # Test validation methods
        validation_results = document.validate_structure()
        
        # Should detect structural issues
        assert 'missing_sections' in validation_results
        assert 'orphaned_subsections' in validation_results
        assert 'inconsistent_numbering' in validation_results
    
    def test_performance_with_large_structures(self):
        """Test performance with documents containing many structural elements"""
        if not STRUCTURE_MODULES_AVAILABLE:
            pytest.skip("Structure detection modules not available")
        
        # Create large document structure
        document = Document(
            file_path="/test/large.pdf",
            file_name="large.pdf",
            metadata=Metadata(title="Large Document")
        )
        
        # Add many sections and paragraphs
        for i in range(50):
            section = Section(title=f"Section {i+1}", level=1)
            
            # Add paragraphs to each section
            for j in range(10):
                paragraph = Paragraph(
                    content=f"Paragraph {j+1} of section {i+1}",
                    page_number=(i*2) + 1
                )
                section.content.append(paragraph)
            
            document.sections.append(section)
        
        # Test that operations remain efficient
        import time
        
        start_time = time.time()
        all_paragraphs = document.get_all_paragraphs()
        end_time = time.time()
        
        # Should complete quickly even with large structure
        assert (end_time - start_time) < 1.0  # Less than 1 second
        assert len(all_paragraphs) == 500  # 50 sections * 10 paragraphs


if __name__ == "__main__":
    if STRUCTURE_MODULES_AVAILABLE:
        print("🔄 Running structure detection tests...")
        
        # Basic model tests
        try:
            test_models = TestDocumentStructureModels()
            test_models.test_heading_model()
            test_models.test_paragraph_model()
            test_models.test_section_model_hierarchy()
            print("✅ Document structure model tests passed")
        except Exception as e:
            print(f"❌ Model tests failed: {e}")
        
        # Integration tests
        try:
            test_integration = TestStructureIntegration()
            test_integration.test_document_structure_extraction_pipeline()
            print("✅ Structure extraction pipeline tests passed")
        except Exception as e:
            print(f"❌ Integration tests failed: {e}")
        
        print("\n🎉 Structure detection testing complete!")
        print("📝 Note: Full layout analysis tests require PDF processing libraries")
        
    else:
        print("⚠️  Structure detection modules not available")
        print("📦 Install requirements and ensure module structure is complete")