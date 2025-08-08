"""
Advanced column detection algorithms for academic PDF layouts
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict


class ColumnLayoutType(Enum):
    """Types of column layouts detected"""
    SINGLE_COLUMN = "single"
    TWO_COLUMN = "two"
    THREE_COLUMN = "three"
    MIXED = "mixed"  # Abstract single-column, body two-column
    IRREGULAR = "irregular"  # Varying column widths or complex layouts


@dataclass
class ColumnRegion:
    """Represents a detected column region"""
    x0: float  # Left boundary
    y0: float  # Top boundary  
    x1: float  # Right boundary
    y1: float  # Bottom boundary
    column_index: int = 0
    confidence: float = 1.0
    text_density: float = 0.0  # Amount of text in this region
    
    @property
    def width(self) -> float:
        """Column width"""
        return self.x1 - self.x0
    
    @property
    def height(self) -> float:
        """Column height"""
        return self.y1 - self.y0
    
    @property
    def area(self) -> float:
        """Column area"""
        return self.width * self.height
    
    @property
    def center_x(self) -> float:
        """Horizontal center of column"""
        return (self.x0 + self.x1) / 2
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is within column region"""
        return self.x0 <= x <= self.x1 and self.y0 <= y <= self.y1
    
    def overlaps_horizontally(self, other: "ColumnRegion", threshold: float = 0.1) -> bool:
        """Check if columns overlap horizontally"""
        overlap = min(self.x1, other.x1) - max(self.x0, other.x0)
        min_width = min(self.width, other.width)
        return overlap > (min_width * threshold)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'x0': self.x0,
            'y0': self.y0,
            'x1': self.x1,
            'y1': self.y1,
            'width': self.width,
            'height': self.height,
            'column_index': self.column_index,
            'confidence': self.confidence,
            'text_density': self.text_density,
        }


@dataclass
class ColumnLayout:
    """Complete column layout for a page"""
    page_number: int
    layout_type: ColumnLayoutType
    columns: List[ColumnRegion] = field(default_factory=list)
    page_width: float = 0.0
    page_height: float = 0.0
    confidence: float = 0.0
    
    # Academic-specific regions
    abstract_region: Optional[ColumnRegion] = None
    title_region: Optional[ColumnRegion] = None
    author_region: Optional[ColumnRegion] = None
    
    def get_column_count(self) -> int:
        """Get number of detected columns"""
        return len(self.columns)
    
    def get_column_by_index(self, index: int) -> Optional[ColumnRegion]:
        """Get column by index"""
        for col in self.columns:
            if col.column_index == index:
                return col
        return None
    
    def get_column_for_point(self, x: float, y: float) -> Optional[ColumnRegion]:
        """Find which column contains a point"""
        for col in self.columns:
            if col.contains_point(x, y):
                return col
        return None
    
    def is_mixed_layout(self) -> bool:
        """Check if this is a mixed layout (e.g., single-column abstract + two-column body)"""
        return self.layout_type == ColumnLayoutType.MIXED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'page_number': self.page_number,
            'layout_type': self.layout_type.value,
            'column_count': self.get_column_count(),
            'columns': [col.to_dict() for col in self.columns],
            'page_width': self.page_width,
            'page_height': self.page_height,
            'confidence': self.confidence,
            'abstract_region': self.abstract_region.to_dict() if self.abstract_region else None,
            'title_region': self.title_region.to_dict() if self.title_region else None,
            'author_region': self.author_region.to_dict() if self.author_region else None,
        }


class ColumnDetector:
    """
    Advanced column detection for academic PDF layouts
    
    Uses multiple algorithms:
    1. Text density analysis
    2. Whitespace gap detection  
    3. Academic format pattern recognition
    4. Geometric clustering of text elements
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Detection thresholds
        self.min_column_width_ratio = self.config.get('min_column_width_ratio', 0.15)  # 15% of page width
        self.max_column_width_ratio = self.config.get('max_column_width_ratio', 0.8)   # 80% of page width
        self.column_gap_threshold = self.config.get('column_gap_threshold', 20)        # Minimum gap in points
        self.text_density_threshold = self.config.get('text_density_threshold', 0.1)  # Minimum text density
        
        # Academic layout patterns
        self.abstract_height_ratio = self.config.get('abstract_height_ratio', 0.25)   # Abstract in top 25% of page
        self.title_height_ratio = self.config.get('title_height_ratio', 0.15)         # Title in top 15% of page
        
    def detect_columns(self, text_elements: List[Dict[str, Any]], 
                      page_width: float, page_height: float,
                      page_number: int) -> ColumnLayout:
        """
        Detect column layout for a page
        
        Args:
            text_elements: List of text elements with position information
            page_width: Page width in points
            page_height: Page height in points  
            page_number: Page number for reference
            
        Returns:
            ColumnLayout object with detected columns
        """
        layout = ColumnLayout(
            page_number=page_number,
            layout_type=ColumnLayoutType.SINGLE_COLUMN,
            page_width=page_width,
            page_height=page_height
        )
        
        if not text_elements:
            return layout
        
        # Method 1: Whitespace gap analysis
        gap_columns = self._detect_by_whitespace_gaps(text_elements, page_width, page_height)
        
        # Method 2: Text density clustering
        density_columns = self._detect_by_text_density(text_elements, page_width, page_height)
        
        # Method 3: Academic pattern recognition
        academic_regions = self._detect_academic_regions(text_elements, page_width, page_height)
        
        # Combine and validate detection methods
        final_columns = self._combine_detection_methods(
            gap_columns, density_columns, academic_regions, 
            page_width, page_height
        )
        
        # Set layout properties
        layout.columns = final_columns
        layout.layout_type = self._classify_layout_type(final_columns, academic_regions)
        layout.confidence = self._calculate_layout_confidence(final_columns, text_elements)
        
        # Set academic regions
        if academic_regions:
            layout.abstract_region = academic_regions.get('abstract')
            layout.title_region = academic_regions.get('title')
            layout.author_region = academic_regions.get('author')
        
        self.logger.debug(f"Page {page_number}: Detected {layout.layout_type.value} layout with {len(final_columns)} columns")
        
        return layout
    
    def _detect_by_whitespace_gaps(self, text_elements: List[Dict[str, Any]], 
                                  page_width: float, page_height: float) -> List[ColumnRegion]:
        """Detect columns by analyzing whitespace gaps between text"""
        
        # Collect x-coordinates of all text elements
        x_positions = []
        for element in text_elements:
            if 'position' in element:
                pos = element['position']
                x_positions.extend([pos.get('x', 0), pos.get('x', 0) + pos.get('width', 0)])
        
        if not x_positions:
            return []
        
        x_positions.sort()
        
        # Find significant gaps in x-coordinates
        gaps = []
        for i in range(1, len(x_positions)):
            gap_size = x_positions[i] - x_positions[i-1]
            if gap_size >= self.column_gap_threshold:
                gaps.append({
                    'start': x_positions[i-1],
                    'end': x_positions[i], 
                    'size': gap_size,
                    'position': (x_positions[i-1] + x_positions[i]) / 2
                })
        
        # Sort gaps by size (largest first)
        gaps.sort(key=lambda g: g['size'], reverse=True)
        
        # Create columns based on gaps
        columns = []
        if not gaps:
            # Single column
            columns.append(ColumnRegion(
                x0=min(x_positions),
                y0=0,
                x1=max(x_positions), 
                y1=page_height,
                column_index=0
            ))
        else:
            # Multiple columns separated by gaps
            column_boundaries = [0]  # Start with left edge
            
            # Add significant gap positions as column boundaries
            for gap in gaps[:2]:  # Consider at most 2 major gaps (3 columns max)
                if gap['size'] > self.column_gap_threshold:
                    column_boundaries.append(gap['position'])
            
            column_boundaries.append(page_width)  # End with right edge
            column_boundaries.sort()
            
            # Create column regions
            for i in range(len(column_boundaries) - 1):
                col_width = column_boundaries[i+1] - column_boundaries[i]
                
                # Filter out very narrow columns
                if col_width >= page_width * self.min_column_width_ratio:
                    columns.append(ColumnRegion(
                        x0=column_boundaries[i],
                        y0=0,
                        x1=column_boundaries[i+1],
                        y1=page_height,
                        column_index=i
                    ))
        
        return columns
    
    def _detect_by_text_density(self, text_elements: List[Dict[str, Any]],
                               page_width: float, page_height: float) -> List[ColumnRegion]:
        """Detect columns by analyzing text density distribution"""
        
        # Create density grid
        grid_width = int(page_width // 20)  # 20 point grid cells
        grid_height = int(page_height // 20)
        
        density_grid = [[0 for _ in range(grid_width)] for _ in range(grid_height)]
        
        # Populate density grid
        for element in text_elements:
            if 'position' in element and 'content' in element:
                pos = element['position']
                x = pos.get('x', 0)
                y = pos.get('y', 0)
                
                grid_x = min(int(x // 20), grid_width - 1)
                grid_y = min(int(y // 20), grid_height - 1)
                
                text_length = len(element.get('content', ''))
                density_grid[grid_y][grid_x] += text_length
        
        # Analyze horizontal density patterns
        horizontal_density = [sum(row) for row in density_grid]
        vertical_density = [sum(density_grid[row][col] for row in range(grid_height)) 
                           for col in range(grid_width)]
        
        # Find column boundaries based on vertical density valleys
        columns = []
        if vertical_density:
            avg_density = sum(vertical_density) / len(vertical_density)
            threshold = avg_density * self.text_density_threshold
            
            # Find density valleys (potential column gaps)
            valleys = []
            for i in range(1, len(vertical_density) - 1):
                if (vertical_density[i] < threshold and 
                    vertical_density[i] < vertical_density[i-1] and 
                    vertical_density[i] < vertical_density[i+1]):
                    valleys.append(i * 20)  # Convert back to page coordinates
            
            # Create columns based on valleys
            if not valleys:
                columns.append(ColumnRegion(0, 0, page_width, page_height, 0))
            else:
                boundaries = [0] + valleys + [page_width]
                for i in range(len(boundaries) - 1):
                    col_width = boundaries[i+1] - boundaries[i]
                    if col_width >= page_width * self.min_column_width_ratio:
                        columns.append(ColumnRegion(
                            boundaries[i], 0, boundaries[i+1], page_height, i
                        ))
        
        return columns
    
    def _detect_academic_regions(self, text_elements: List[Dict[str, Any]],
                                page_width: float, page_height: float) -> Dict[str, ColumnRegion]:
        """Detect academic-specific regions like title, abstract, authors"""
        
        regions = {}
        
        # Sort elements by vertical position (top to bottom)
        sorted_elements = sorted(
            [e for e in text_elements if 'position' in e],
            key=lambda x: x['position'].get('y', 0)
        )
        
        if not sorted_elements:
            return regions
        
        # Title region detection (top 15% of page)
        title_threshold = page_height * self.title_height_ratio
        title_elements = [e for e in sorted_elements 
                         if e['position'].get('y', 0) <= title_threshold]
        
        if title_elements:
            title_x_positions = [e['position'].get('x', 0) for e in title_elements]
            title_widths = [e['position'].get('width', 0) for e in title_elements]
            
            regions['title'] = ColumnRegion(
                x0=min(title_x_positions),
                y0=0,
                x1=max(title_x_positions[i] + title_widths[i] for i in range(len(title_elements))),
                y1=title_threshold,
                column_index=-1  # Special index for title
            )
        
        # Abstract region detection (typically single column in top 25% after title)
        abstract_threshold = page_height * self.abstract_height_ratio
        abstract_candidates = []
        
        for element in sorted_elements:
            y_pos = element['position'].get('y', 0)
            content = element.get('content', '').lower()
            
            if (title_threshold < y_pos <= abstract_threshold and 
                ('abstract' in content or len(content) > 100)):  # Long text blocks
                abstract_candidates.append(element)
        
        if abstract_candidates:
            abstract_x_positions = [e['position'].get('x', 0) for e in abstract_candidates]
            abstract_widths = [e['position'].get('width', 0) for e in abstract_candidates]
            abstract_y_positions = [e['position'].get('y', 0) for e in abstract_candidates]
            abstract_heights = [e['position'].get('height', 0) for e in abstract_candidates]
            
            regions['abstract'] = ColumnRegion(
                x0=min(abstract_x_positions),
                y0=min(abstract_y_positions),
                x1=max(abstract_x_positions[i] + abstract_widths[i] for i in range(len(abstract_candidates))),
                y1=max(abstract_y_positions[i] + abstract_heights[i] for i in range(len(abstract_candidates))),
                column_index=-2  # Special index for abstract
            )
        
        return regions
    
    def _combine_detection_methods(self, gap_columns: List[ColumnRegion],
                                  density_columns: List[ColumnRegion],
                                  academic_regions: Dict[str, ColumnRegion],
                                  page_width: float, page_height: float) -> List[ColumnRegion]:
        """Combine results from different detection methods"""
        
        # Score each detection method
        gap_score = self._score_column_detection(gap_columns, page_width)
        density_score = self._score_column_detection(density_columns, page_width)
        
        # Choose best detection method
        if gap_score >= density_score:
            primary_columns = gap_columns
            primary_score = gap_score
        else:
            primary_columns = density_columns 
            primary_score = density_score
        
        # Refine columns based on academic regions
        if academic_regions and primary_columns:
            primary_columns = self._refine_with_academic_regions(
                primary_columns, academic_regions, page_height
            )
        
        # Ensure minimum quality threshold
        if primary_score < 0.3 or not primary_columns:
            # Fallback to single column
            return [ColumnRegion(0, 0, page_width, page_height, 0)]
        
        return primary_columns
    
    def _score_column_detection(self, columns: List[ColumnRegion], page_width: float) -> float:
        """Score the quality of column detection"""
        if not columns:
            return 0.0
        
        score = 0.0
        
        # Prefer 2 columns for academic papers
        if len(columns) == 2:
            score += 0.5
        elif len(columns) == 1:
            score += 0.3
        else:
            score += 0.1  # Penalize too many columns
        
        # Check column width consistency
        if len(columns) > 1:
            widths = [col.width for col in columns]
            width_variance = max(widths) - min(widths)
            consistency_score = 1.0 - (width_variance / page_width)
            score += consistency_score * 0.3
        
        # Check reasonable column widths
        for col in columns:
            width_ratio = col.width / page_width
            if self.min_column_width_ratio <= width_ratio <= self.max_column_width_ratio:
                score += 0.2
        
        return min(score, 1.0)
    
    def _refine_with_academic_regions(self, columns: List[ColumnRegion],
                                    academic_regions: Dict[str, ColumnRegion],
                                    page_height: float) -> List[ColumnRegion]:
        """Refine column detection using academic region information"""
        
        # If we have an abstract region, adjust column boundaries
        if 'abstract' in academic_regions:
            abstract_region = academic_regions['abstract']
            
            # Check if abstract spans multiple detected columns (mixed layout)
            spanning_columns = []
            for col in columns:
                if col.overlaps_horizontally(abstract_region, threshold=0.3):
                    spanning_columns.append(col)
            
            if len(spanning_columns) > 1:
                # Abstract spans columns - create mixed layout
                # Keep original columns for body text but adjust boundaries
                body_start_y = abstract_region.y1
                
                refined_columns = []
                for i, col in enumerate(columns):
                    # Create body column starting after abstract
                    refined_col = ColumnRegion(
                        x0=col.x0,
                        y0=body_start_y,
                        x1=col.x1,
                        y1=col.y1,
                        column_index=i
                    )
                    refined_columns.append(refined_col)
                
                return refined_columns
        
        return columns
    
    def _classify_layout_type(self, columns: List[ColumnRegion], 
                            academic_regions: Dict[str, ColumnRegion]) -> ColumnLayoutType:
        """Classify the type of column layout"""
        
        num_columns = len(columns)
        
        # Check for mixed layout (abstract + columns)
        if 'abstract' in academic_regions and num_columns >= 2:
            abstract_region = academic_regions['abstract']
            
            # Check if abstract spans multiple columns
            spanning_count = sum(1 for col in columns if col.overlaps_horizontally(abstract_region))
            if spanning_count > 1:
                return ColumnLayoutType.MIXED
        
        # Standard layouts
        if num_columns == 1:
            return ColumnLayoutType.SINGLE_COLUMN
        elif num_columns == 2:
            return ColumnLayoutType.TWO_COLUMN
        elif num_columns == 3:
            return ColumnLayoutType.THREE_COLUMN
        else:
            return ColumnLayoutType.IRREGULAR
    
    def _calculate_layout_confidence(self, columns: List[ColumnRegion],
                                   text_elements: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for the detected layout"""
        
        if not columns or not text_elements:
            return 0.0
        
        confidence = 0.0
        
        # Text distribution across columns
        column_text_counts = defaultdict(int)
        
        for element in text_elements:
            if 'position' in element:
                pos = element['position']
                x = pos.get('x', 0) + pos.get('width', 0) / 2  # Center point
                y = pos.get('y', 0) + pos.get('height', 0) / 2
                
                # Find which column contains this element
                for col in columns:
                    if col.contains_point(x, y):
                        column_text_counts[col.column_index] += len(element.get('content', ''))
                        break
        
        # Check text distribution balance
        if len(columns) > 1:
            text_counts = list(column_text_counts.values())
            if text_counts:
                avg_text = sum(text_counts) / len(text_counts)
                balance_score = 1.0 - (max(text_counts) - min(text_counts)) / max(avg_text, 1)
                confidence += balance_score * 0.5
        else:
            confidence += 0.3  # Single column is always reasonably confident
        
        # Column geometry scoring
        geometry_score = self._score_column_detection(columns, max(col.x1 for col in columns))
        confidence += geometry_score * 0.5
        
        return min(confidence, 1.0)