"""
Comprehensive layout analyzer integrating column detection and reading order processing
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from .column_detector import ColumnDetector, ColumnLayout, ColumnLayoutType
from .reading_order import ReadingOrderProcessor, TextFlow, FlowType
from ..models import TextElement, Document, Section, Paragraph, Heading


class LayoutType(Enum):
    """Overall layout classification"""
    ACADEMIC_PAPER = "academic_paper"
    BOOK_CHAPTER = "book_chapter"
    REPORT = "report"
    PRESENTATION = "presentation"
    UNKNOWN = "unknown"


@dataclass
class LayoutElement:
    """Enhanced text element with layout context"""
    original_element: TextElement
    column_index: int = -1
    reading_order_index: int = -1
    layout_confidence: float = 0.0
    academic_role: Optional[str] = None  # title, abstract, body, footnote, etc.
    
    @property
    def content(self) -> str:
        """Get content from original element"""
        return self.original_element.content
    
    @property 
    def position(self) -> Dict[str, float]:
        """Get position from original element"""
        return self.original_element.position
    
    @property
    def font_info(self) -> Dict[str, Any]:
        """Get font info from original element"""
        return self.original_element.font_info


@dataclass
class PageLayout:
    """Complete layout analysis for a page"""
    page_number: int
    layout_type: LayoutType
    column_layout: ColumnLayout
    text_flow: TextFlow
    layout_elements: List[LayoutElement] = field(default_factory=list)
    confidence: float = 0.0
    
    # Layout statistics
    total_elements: int = 0
    columns_detected: int = 0
    reading_order_quality: float = 0.0
    
    def get_elements_by_column(self, column_index: int) -> List[LayoutElement]:
        """Get all elements in a specific column"""
        return [elem for elem in self.layout_elements if elem.column_index == column_index]
    
    def get_elements_by_role(self, role: str) -> List[LayoutElement]:
        """Get elements by academic role"""
        return [elem for elem in self.layout_elements if elem.academic_role == role]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'page_number': self.page_number,
            'layout_type': self.layout_type.value,
            'column_layout': self.column_layout.to_dict(),
            'text_flow': {
                'flow_type': self.text_flow.flow_type.value,
                'reading_direction': self.text_flow.reading_direction.value,
                'confidence': self.text_flow.confidence,
                'element_count': len(self.text_flow.elements)
            },
            'statistics': {
                'total_elements': self.total_elements,
                'columns_detected': self.columns_detected,
                'reading_order_quality': self.reading_order_quality,
                'overall_confidence': self.confidence
            }
        }


class LayoutAnalyzer:
    """
    Comprehensive layout analyzer that combines column detection and reading order processing
    to provide complete layout understanding for academic documents
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize sub-components
        column_config = self.config.get('column_detection', {})
        self.column_detector = ColumnDetector(column_config)
        
        reading_order_config = self.config.get('reading_order', {})
        self.reading_order_processor = ReadingOrderProcessor(reading_order_config)
        
        # Layout classification thresholds
        self.academic_confidence_threshold = self.config.get('academic_confidence_threshold', 0.7)
        self.mixed_layout_threshold = self.config.get('mixed_layout_threshold', 0.6)
        
    def analyze_page_layout(self, text_elements: List[TextElement],
                           page_width: float, page_height: float,
                           page_number: int) -> PageLayout:
        """
        Perform comprehensive layout analysis for a single page
        
        Args:
            text_elements: List of text elements with position information
            page_width: Page width in points
            page_height: Page height in points
            page_number: Page number for reference
            
        Returns:
            PageLayout object with complete analysis
        """
        
        # Convert text elements to dict format for column detector
        element_dicts = []
        for elem in text_elements:
            element_dicts.append({
                'content': elem.content,
                'position': elem.position,
                'font_info': elem.font_info if hasattr(elem, 'font_info') else {}
            })
        
        # Step 1: Detect column layout
        column_layout = self.column_detector.detect_columns(
            element_dicts, page_width, page_height, page_number
        )
        
        # Step 2: Determine reading order
        text_flow = self.reading_order_processor.process_reading_order(
            text_elements, column_layout
        )
        
        # Step 3: Classify overall layout type
        layout_type = self._classify_layout_type(column_layout, text_elements)
        
        # Step 4: Create enhanced layout elements
        layout_elements = self._create_layout_elements(
            text_elements, column_layout, text_flow
        )
        
        # Step 5: Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(
            column_layout, text_flow, layout_elements
        )
        
        # Create page layout
        page_layout = PageLayout(
            page_number=page_number,
            layout_type=layout_type,
            column_layout=column_layout,
            text_flow=text_flow,
            layout_elements=layout_elements,
            confidence=overall_confidence,
            total_elements=len(text_elements),
            columns_detected=column_layout.get_column_count(),
            reading_order_quality=text_flow.confidence
        )
        
        self.logger.info(f"Page {page_number}: {layout_type.value} layout, "
                        f"{column_layout.get_column_count()} columns, "
                        f"confidence {overall_confidence:.2f}")
        
        return page_layout
    
    def analyze_document_layout(self, document: Document) -> List[PageLayout]:
        """
        Analyze layout for entire document
        
        Args:
            document: Document object with sections and text elements
            
        Returns:
            List of PageLayout objects, one per page
        """
        
        page_layouts = []
        
        # Group elements by page
        pages_elements = self._group_elements_by_page(document)
        
        for page_number, elements in pages_elements.items():
            if not elements:
                continue
            
            # Estimate page dimensions (could be improved with actual PDF metadata)
            page_width, page_height = self._estimate_page_dimensions(elements)
            
            page_layout = self.analyze_page_layout(
                elements, page_width, page_height, page_number
            )
            
            page_layouts.append(page_layout)
        
        # Post-process for document-level consistency
        page_layouts = self._apply_document_consistency(page_layouts)
        
        self.logger.info(f"Analyzed {len(page_layouts)} pages in document")
        
        return page_layouts
    
    def _classify_layout_type(self, column_layout: ColumnLayout,
                            text_elements: List[TextElement]) -> LayoutType:
        """Classify the overall layout type based on detected patterns"""
        
        # Check for academic paper indicators
        academic_indicators = 0
        
        # Abstract region indicates academic paper
        if column_layout.abstract_region:
            academic_indicators += 2
        
        # Title region indicates academic paper  
        if column_layout.title_region:
            academic_indicators += 1
        
        # Two-column layout is common in academic papers
        if column_layout.layout_type in [ColumnLayoutType.TWO_COLUMN, ColumnLayoutType.MIXED]:
            academic_indicators += 1
        
        # Check text content for academic patterns
        combined_text = ' '.join(elem.content.lower() for elem in text_elements[:5])  # First few elements
        
        academic_keywords = [
            'abstract', 'introduction', 'methodology', 'results', 'conclusion',
            'references', 'doi', 'journal', 'conference', 'university',
            'keywords', 'author', 'email'
        ]
        
        keyword_matches = sum(1 for keyword in academic_keywords if keyword in combined_text)
        academic_indicators += min(keyword_matches, 3)  # Cap at 3 points
        
        # Classification based on indicators
        if academic_indicators >= 4:
            return LayoutType.ACADEMIC_PAPER
        elif len(text_elements) > 50 and column_layout.get_column_count() == 1:
            return LayoutType.BOOK_CHAPTER
        elif 'report' in combined_text or 'summary' in combined_text:
            return LayoutType.REPORT
        else:
            return LayoutType.UNKNOWN
    
    def _create_layout_elements(self, text_elements: List[TextElement],
                              column_layout: ColumnLayout,
                              text_flow: TextFlow) -> List[LayoutElement]:
        """Create enhanced layout elements with layout context"""
        
        layout_elements = []
        
        # Create mapping from original elements to flow order
        flow_order_map = {}
        for i, elem in enumerate(text_flow.elements):
            flow_order_map[id(elem)] = i
        
        # Process each original element
        for elem in text_elements:
            # Determine column membership
            column_index = self._find_element_column(elem, column_layout)
            
            # Get reading order index
            reading_order_index = flow_order_map.get(id(elem), -1)
            
            # Determine academic role
            academic_role = self._classify_academic_role(elem, column_layout)
            
            # Calculate layout confidence
            layout_confidence = self._calculate_element_confidence(
                elem, column_index, reading_order_index, academic_role
            )
            
            layout_element = LayoutElement(
                original_element=elem,
                column_index=column_index,
                reading_order_index=reading_order_index,
                layout_confidence=layout_confidence,
                academic_role=academic_role
            )
            
            layout_elements.append(layout_element)
        
        return layout_elements
    
    def _find_element_column(self, element: TextElement,
                           column_layout: ColumnLayout) -> int:
        """Find which column an element belongs to"""
        
        element_center_x = element.position.get('x', 0) + element.position.get('width', 0) / 2
        element_center_y = element.position.get('y', 0) + element.position.get('height', 0) / 2
        
        # Check each column
        for col in column_layout.columns:
            if col.contains_point(element_center_x, element_center_y):
                return col.column_index
        
        # If not in any column, assign to nearest one
        min_distance = float('inf')
        nearest_column = 0
        
        for col in column_layout.columns:
            distance = abs(element_center_x - col.center_x)
            if distance < min_distance:
                min_distance = distance
                nearest_column = col.column_index
        
        return nearest_column
    
    def _classify_academic_role(self, element: TextElement,
                              column_layout: ColumnLayout) -> Optional[str]:
        """Classify the academic role of a text element"""
        
        content = element.content.lower() if hasattr(element, 'content') else ''
        element_y = element.position.get('y', 0)
        
        # Title (top region, large font, centered)
        if column_layout.title_region:
            if self._element_in_region(element, column_layout.title_region):
                return 'title'
        
        # Abstract
        if column_layout.abstract_region:
            if self._element_in_region(element, column_layout.abstract_region):
                return 'abstract'
        
        # Check content-based roles
        if content.startswith('abstract'):
            return 'abstract'
        elif any(keyword in content for keyword in ['author', 'email', 'affiliation']):
            return 'author'
        elif isinstance(element, Heading):
            return 'heading'
        elif content.startswith('reference') or content.startswith('bibliograph'):
            return 'references'
        elif element_y > column_layout.page_height * 0.85:  # Bottom 15%
            return 'footnote'
        else:
            return 'body'
    
    def _element_in_region(self, element: TextElement, region) -> bool:
        """Check if element is within a region"""
        element_center_x = element.position.get('x', 0) + element.position.get('width', 0) / 2
        element_center_y = element.position.get('y', 0) + element.position.get('height', 0) / 2
        
        return region.contains_point(element_center_x, element_center_y)
    
    def _calculate_element_confidence(self, element: TextElement,
                                    column_index: int, reading_order_index: int,
                                    academic_role: Optional[str]) -> float:
        """Calculate confidence score for element layout analysis"""
        
        confidence = 0.0
        
        # Column assignment confidence
        if column_index >= 0:
            confidence += 0.4
        
        # Reading order confidence
        if reading_order_index >= 0:
            confidence += 0.3
        
        # Academic role confidence
        if academic_role:
            confidence += 0.2
        
        # Position reasonableness (not overlapping margins, etc.)
        x = element.position.get('x', 0)
        y = element.position.get('y', 0)
        
        if x > 0 and y > 0:  # Basic position sanity
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _calculate_overall_confidence(self, column_layout: ColumnLayout,
                                    text_flow: TextFlow,
                                    layout_elements: List[LayoutElement]) -> float:
        """Calculate overall layout analysis confidence"""
        
        confidence = 0.0
        
        # Column detection confidence
        confidence += column_layout.confidence * 0.4
        
        # Reading order confidence
        confidence += text_flow.confidence * 0.4
        
        # Element analysis confidence
        if layout_elements:
            avg_element_confidence = sum(elem.layout_confidence for elem in layout_elements) / len(layout_elements)
            confidence += avg_element_confidence * 0.2
        
        return min(confidence, 1.0)
    
    def _group_elements_by_page(self, document: Document) -> Dict[int, List[TextElement]]:
        """Group document elements by page number"""
        
        pages = {}
        
        # Extract elements from sections
        for section in document.sections:
            for content_item in section.content:
                if isinstance(content_item, (Paragraph, Heading)):
                    page_num = content_item.page_number
                    if page_num not in pages:
                        pages[page_num] = []
                    pages[page_num].append(content_item)
        
        return pages
    
    def _estimate_page_dimensions(self, elements: List[TextElement]) -> Tuple[float, float]:
        """Estimate page dimensions from element positions"""
        
        if not elements:
            return 612, 792  # Default US Letter size
        
        # Find maximum extents
        max_x = 0
        max_y = 0
        
        for elem in elements:
            x = elem.position.get('x', 0) + elem.position.get('width', 0)
            y = elem.position.get('y', 0) + elem.position.get('height', 0)
            
            max_x = max(max_x, x)
            max_y = max(max_y, y)
        
        # Add margins (estimate)
        page_width = max_x + 72  # 1 inch margin
        page_height = max_y + 72
        
        return page_width, page_height
    
    def _apply_document_consistency(self, page_layouts: List[PageLayout]) -> List[PageLayout]:
        """Apply document-level consistency checks and corrections"""
        
        if len(page_layouts) <= 1:
            return page_layouts
        
        # Check for consistent column patterns
        column_counts = [layout.columns_detected for layout in page_layouts]
        most_common_columns = max(set(column_counts), key=column_counts.count)
        
        # Update layouts with inconsistent column counts (with low confidence)
        for layout in page_layouts:
            if (layout.columns_detected != most_common_columns and 
                layout.column_layout.confidence < 0.5):
                
                # This could be improved with more sophisticated consistency logic
                self.logger.warning(f"Page {layout.page_number} has inconsistent column layout")
        
        return page_layouts
    
    def get_layout_statistics(self, page_layouts: List[PageLayout]) -> Dict[str, Any]:
        """Get comprehensive statistics about document layout"""
        
        if not page_layouts:
            return {}
        
        # Collect statistics
        layout_types = [layout.layout_type for layout in page_layouts]
        column_counts = [layout.columns_detected for layout in page_layouts]
        confidences = [layout.confidence for layout in page_layouts]
        
        stats = {
            'total_pages': len(page_layouts),
            'layout_types': {
                layout_type.value: layout_types.count(layout_type)
                for layout_type in set(layout_types)
            },
            'column_distribution': {
                str(count): column_counts.count(count)
                for count in set(column_counts)
            },
            'average_confidence': sum(confidences) / len(confidences),
            'min_confidence': min(confidences),
            'max_confidence': max(confidences),
            'pages_with_mixed_layout': sum(1 for layout in page_layouts 
                                         if layout.column_layout.layout_type == ColumnLayoutType.MIXED),
            'academic_paper_likelihood': layout_types.count(LayoutType.ACADEMIC_PAPER) / len(layout_types)
        }
        
        return stats