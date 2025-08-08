"""
Reading order processor for maintaining logical text flow in multi-column layouts
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

from .column_detector import ColumnLayout, ColumnRegion
from ..models import TextElement, Paragraph, Heading


class ReadingDirection(Enum):
    """Reading direction for text flow"""
    LEFT_TO_RIGHT = "ltr"
    RIGHT_TO_LEFT = "rtl"
    TOP_TO_BOTTOM = "ttb"
    COLUMN_WISE = "column"


class FlowType(Enum):
    """Type of text flow pattern"""
    LINEAR = "linear"           # Simple top-to-bottom
    COLUMNAR = "columnar"       # Column-by-column
    MIXED = "mixed"             # Abstract + columns
    IRREGULAR = "irregular"     # Complex layout


@dataclass
class TextFlow:
    """Represents the reading flow of text elements"""
    flow_type: FlowType
    reading_direction: ReadingDirection = ReadingDirection.LEFT_TO_RIGHT
    elements: List[TextElement] = field(default_factory=list)
    confidence: float = 0.0
    
    def get_ordered_elements(self) -> List[TextElement]:
        """Get elements in proper reading order"""
        return self.elements
    
    def add_element(self, element: TextElement, position_index: Optional[int] = None):
        """Add element to flow at specific position or end"""
        if position_index is not None:
            self.elements.insert(position_index, element)
        else:
            self.elements.append(element)


@dataclass 
class ColumnTextGroup:
    """Group of text elements within a column"""
    column_index: int
    column_region: ColumnRegion
    elements: List[TextElement] = field(default_factory=list)
    y_sorted_elements: List[TextElement] = field(default_factory=list)
    
    def sort_elements(self):
        """Sort elements by vertical position within column"""
        self.y_sorted_elements = sorted(
            self.elements,
            key=lambda e: e.position.get('y', 0)
        )
    
    def get_top_element(self) -> Optional[TextElement]:
        """Get topmost element in column"""
        if self.y_sorted_elements:
            return self.y_sorted_elements[0]
        return None
    
    def get_bottom_element(self) -> Optional[TextElement]:
        """Get bottommost element in column"""
        if self.y_sorted_elements:
            return self.y_sorted_elements[-1]
        return None


class ReadingOrderProcessor:
    """
    Advanced reading order processor for multi-column academic layouts
    
    Handles:
    1. Single-column linear flow
    2. Multi-column columnar flow
    3. Mixed layouts (abstract + columns)
    4. Academic-specific elements (footnotes, captions)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Reading order preferences
        self.column_reading_direction = ReadingDirection.LEFT_TO_RIGHT
        self.vertical_tolerance = self.config.get('vertical_tolerance', 5.0)  # Points
        self.column_overlap_threshold = self.config.get('column_overlap_threshold', 0.1)
        
        # Academic layout preferences
        self.prioritize_abstracts = self.config.get('prioritize_abstracts', True)
        self.handle_footnotes = self.config.get('handle_footnotes', True)
        self.maintain_section_order = self.config.get('maintain_section_order', True)
    
    def process_reading_order(self, text_elements: List[TextElement],
                            column_layout: ColumnLayout) -> TextFlow:
        """
        Process text elements and return them in proper reading order
        
        Args:
            text_elements: List of text elements with position information
            column_layout: Detected column layout for the page
            
        Returns:
            TextFlow object with properly ordered elements
        """
        
        if not text_elements:
            return TextFlow(flow_type=FlowType.LINEAR, elements=[])
        
        # Determine flow strategy based on layout
        flow_type = self._determine_flow_type(column_layout)
        
        # Group elements by columns
        column_groups = self._group_elements_by_columns(text_elements, column_layout)
        
        # Apply reading order strategy
        ordered_elements = []
        
        if flow_type == FlowType.LINEAR:
            ordered_elements = self._process_linear_flow(text_elements)
        elif flow_type == FlowType.COLUMNAR:
            ordered_elements = self._process_columnar_flow(column_groups)
        elif flow_type == FlowType.MIXED:
            ordered_elements = self._process_mixed_flow(text_elements, column_layout, column_groups)
        else:  # IRREGULAR
            ordered_elements = self._process_irregular_flow(text_elements, column_groups)
        
        # Post-process for academic elements
        ordered_elements = self._handle_academic_elements(ordered_elements, column_layout)
        
        # Calculate confidence
        confidence = self._calculate_flow_confidence(ordered_elements, text_elements)
        
        flow = TextFlow(
            flow_type=flow_type,
            reading_direction=self.column_reading_direction,
            elements=ordered_elements,
            confidence=confidence
        )
        
        self.logger.debug(f"Processed {len(text_elements)} elements into {flow_type.value} flow")
        
        return flow
    
    def _determine_flow_type(self, column_layout: ColumnLayout) -> FlowType:
        """Determine the type of reading flow based on layout"""
        
        if column_layout.get_column_count() <= 1:
            return FlowType.LINEAR
        elif column_layout.is_mixed_layout():
            return FlowType.MIXED
        elif column_layout.get_column_count() <= 3:
            return FlowType.COLUMNAR
        else:
            return FlowType.IRREGULAR
    
    def _group_elements_by_columns(self, text_elements: List[TextElement],
                                 column_layout: ColumnLayout) -> List[ColumnTextGroup]:
        """Group text elements by their column membership"""
        
        # Create groups for each column
        column_groups = []
        for col in column_layout.columns:
            group = ColumnTextGroup(
                column_index=col.column_index,
                column_region=col
            )
            column_groups.append(group)
        
        # Assign elements to columns
        unassigned_elements = []
        
        for element in text_elements:
            assigned = False
            element_center_x = element.position.get('x', 0) + element.position.get('width', 0) / 2
            element_center_y = element.position.get('y', 0) + element.position.get('height', 0) / 2
            
            # Find best matching column
            for group in column_groups:
                if group.column_region.contains_point(element_center_x, element_center_y):
                    group.elements.append(element)
                    assigned = True
                    break
            
            if not assigned:
                unassigned_elements.append(element)
        
        # Handle unassigned elements (assign to nearest column)
        for element in unassigned_elements:
            element_center_x = element.position.get('x', 0) + element.position.get('width', 0) / 2
            
            # Find closest column by horizontal distance
            closest_group = None
            min_distance = float('inf')
            
            for group in column_groups:
                col_center = group.column_region.center_x
                distance = abs(element_center_x - col_center)
                
                if distance < min_distance:
                    min_distance = distance
                    closest_group = group
            
            if closest_group:
                closest_group.elements.append(element)
        
        # Sort elements within each column
        for group in column_groups:
            group.sort_elements()
        
        return column_groups
    
    def _process_linear_flow(self, text_elements: List[TextElement]) -> List[TextElement]:
        """Process single-column linear reading flow"""
        
        # Simple top-to-bottom sort
        return sorted(text_elements, key=lambda e: e.position.get('y', 0))
    
    def _process_columnar_flow(self, column_groups: List[ColumnTextGroup]) -> List[TextElement]:
        """Process multi-column reading flow (left-to-right, top-to-bottom)"""
        
        if not column_groups:
            return []
        
        # Sort column groups by horizontal position
        sorted_groups = sorted(column_groups, key=lambda g: g.column_region.x0)
        
        ordered_elements = []
        
        # Strategy: Alternate between columns at similar vertical positions
        # This preserves logical reading order across columns
        
        max_elements = max(len(g.y_sorted_elements) for g in sorted_groups)
        
        for element_index in range(max_elements):
            # Process each column group at this vertical level
            for group in sorted_groups:
                if element_index < len(group.y_sorted_elements):
                    ordered_elements.append(group.y_sorted_elements[element_index])
        
        return ordered_elements
    
    def _process_mixed_flow(self, text_elements: List[TextElement],
                          column_layout: ColumnLayout,
                          column_groups: List[ColumnTextGroup]) -> List[TextElement]:
        """Process mixed layout (abstract + multi-column body)"""
        
        ordered_elements = []
        
        # First, add academic regions in order (title, authors, abstract)
        if column_layout.title_region:
            title_elements = [e for e in text_elements 
                            if self._element_in_region(e, column_layout.title_region)]
            title_elements.sort(key=lambda e: e.position.get('y', 0))
            ordered_elements.extend(title_elements)
        
        if column_layout.author_region:
            author_elements = [e for e in text_elements 
                             if self._element_in_region(e, column_layout.author_region)]
            author_elements.sort(key=lambda e: e.position.get('y', 0))
            ordered_elements.extend(author_elements)
        
        if column_layout.abstract_region:
            abstract_elements = [e for e in text_elements 
                               if self._element_in_region(e, column_layout.abstract_region)]
            abstract_elements.sort(key=lambda e: e.position.get('y', 0))
            ordered_elements.extend(abstract_elements)
        
        # Then process column content
        column_elements = self._process_columnar_flow(column_groups)
        
        # Filter out elements already added from academic regions
        added_element_ids = set(id(e) for e in ordered_elements)
        remaining_elements = [e for e in column_elements if id(e) not in added_element_ids]
        
        ordered_elements.extend(remaining_elements)
        
        return ordered_elements
    
    def _process_irregular_flow(self, text_elements: List[TextElement],
                              column_groups: List[ColumnTextGroup]) -> List[TextElement]:
        """Process irregular or complex layouts"""
        
        # Fallback to simple top-to-bottom sorting
        # For complex layouts, maintaining vertical order is most reliable
        return sorted(text_elements, key=lambda e: e.position.get('y', 0))
    
    def _element_in_region(self, element: TextElement, region: ColumnRegion) -> bool:
        """Check if element is within a specific region"""
        element_center_x = element.position.get('x', 0) + element.position.get('width', 0) / 2
        element_center_y = element.position.get('y', 0) + element.position.get('height', 0) / 2
        
        return region.contains_point(element_center_x, element_center_y)
    
    def _handle_academic_elements(self, ordered_elements: List[TextElement],
                                column_layout: ColumnLayout) -> List[TextElement]:
        """Handle academic-specific elements like footnotes, captions"""
        
        if not self.handle_footnotes:
            return ordered_elements
        
        # Separate footnotes and captions for special handling
        main_elements = []
        footnotes = []
        captions = []
        
        for element in ordered_elements:
            content = element.content.lower() if hasattr(element, 'content') else ''
            
            # Identify footnotes (small text at bottom, numbered references)
            if self._is_footnote(element, column_layout):
                footnotes.append(element)
            # Identify captions (text near bottom, contains "figure", "table")
            elif self._is_caption(element):
                captions.append(element)
            else:
                main_elements.append(element)
        
        # Reorder: main content, then captions, then footnotes
        final_order = main_elements + captions + footnotes
        
        return final_order
    
    def _is_footnote(self, element: TextElement, column_layout: ColumnLayout) -> bool:
        """Identify if element is a footnote"""
        
        # Check position (bottom 20% of page)
        element_y = element.position.get('y', 0)
        page_height = column_layout.page_height
        
        if element_y < page_height * 0.8:
            return False
        
        # Check font size (typically smaller)
        font_size = element.font_info.get('size', 12)
        if font_size > 10:  # Footnotes are usually small
            return False
        
        # Check content patterns
        content = element.content if hasattr(element, 'content') else ''
        if len(content) < 10:  # Very short content
            return False
        
        # Look for numbering patterns at start
        import re
        if re.match(r'^\d+\.?\s', content):
            return True
        
        return False
    
    def _is_caption(self, element: TextElement) -> bool:
        """Identify if element is a figure or table caption"""
        
        content = element.content.lower() if hasattr(element, 'content') else ''
        
        # Look for caption keywords
        caption_keywords = ['figure', 'table', 'fig.', 'tab.', 'chart', 'graph']
        
        for keyword in caption_keywords:
            if keyword in content:
                return True
        
        return False
    
    def _calculate_flow_confidence(self, ordered_elements: List[TextElement],
                                 original_elements: List[TextElement]) -> float:
        """Calculate confidence in the reading order"""
        
        if not ordered_elements or not original_elements:
            return 0.0
        
        confidence = 0.0
        
        # Check completeness (all elements preserved)
        if len(ordered_elements) == len(original_elements):
            confidence += 0.4
        else:
            # Penalize for missing elements
            ratio = len(ordered_elements) / len(original_elements)
            confidence += ratio * 0.4
        
        # Check logical vertical progression
        vertical_consistency = 0.0
        prev_y = -1
        
        for element in ordered_elements:
            current_y = element.position.get('y', 0)
            
            if prev_y == -1:
                prev_y = current_y
                continue
            
            # Allow some tolerance for elements at similar vertical positions
            if current_y >= prev_y - self.vertical_tolerance:
                vertical_consistency += 1
            
            prev_y = current_y
        
        if len(ordered_elements) > 1:
            vertical_score = vertical_consistency / (len(ordered_elements) - 1)
            confidence += vertical_score * 0.4
        
        # Bonus for maintaining section order (headings before paragraphs)
        if self.maintain_section_order:
            section_order_score = self._evaluate_section_order(ordered_elements)
            confidence += section_order_score * 0.2
        
        return min(confidence, 1.0)
    
    def _evaluate_section_order(self, ordered_elements: List[TextElement]) -> float:
        """Evaluate if section order is logical (headings before content)"""
        
        section_transitions = 0
        correct_transitions = 0
        
        for i in range(len(ordered_elements) - 1):
            current = ordered_elements[i]
            next_elem = ordered_elements[i + 1]
            
            # Check if we have a heading followed by paragraph
            if (isinstance(current, Heading) and isinstance(next_elem, Paragraph)):
                section_transitions += 1
                
                # Check if paragraph is related (similar vertical position or indented)
                current_y = current.position.get('y', 0)
                next_y = next_elem.position.get('y', 0)
                
                if next_y >= current_y:  # Logical vertical progression
                    correct_transitions += 1
        
        if section_transitions == 0:
            return 0.5  # Neutral score if no clear sections
        
        return correct_transitions / section_transitions