"""
Main PDF processing engine with dual-library support and academic optimizations
"""

import time
import logging
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
from enum import Enum

from .extractors import BaseExtractor, PyMuPDFExtractor, PDFPlumberExtractor
from .models import Document, Metadata, Section, Paragraph, Heading, Table
from .config import ProcessorConfig, PublisherProfile, PublisherType, get_academic_config
from .layout import LayoutAnalyzer, PageLayout, LayoutType


class ExtractionMethod(Enum):
    """Available extraction methods"""
    PYMUPDF = "pymupdf"
    PDFPLUMBER = "pdfplumber"
    AUTO = "auto"
    HYBRID = "hybrid"


class ProcessingResult:
    """Result of PDF processing operation"""
    def __init__(self):
        self.document: Optional[Document] = None
        self.success: bool = False
        self.processing_time: float = 0.0
        self.extraction_method: str = "unknown"
        self.confidence_score: float = 0.0
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def add_error(self, error: str):
        """Add error message"""
        self.errors.append(error)
        
    def add_warning(self, warning: str):
        """Add warning message"""
        self.warnings.append(warning)


class PDFProcessor:
    """
    Main PDF processing engine with intelligent extraction strategy selection
    and academic document optimization
    """
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        self.config = config or get_academic_config()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize extractors
        self.extractors: Dict[str, BaseExtractor] = {}
        self._initialize_extractors()
        
        # Initialize layout analyzer
        layout_config = {
            'column_detection': self.config.to_dict().get('column_detection', {}),
            'reading_order': self.config.to_dict().get('reading_order', {}),
        }
        self.layout_analyzer = LayoutAnalyzer(layout_config)
        
        # Processing statistics
        self.stats = {
            'total_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'extraction_methods': {},
            'layout_analysis': {
                'pages_analyzed': 0,
                'mixed_layouts_detected': 0,
                'average_confidence': 0.0
            },
        }
    
    def _initialize_extractors(self):
        """Initialize available extractors"""
        try:
            self.extractors['pymupdf'] = PyMuPDFExtractor(self.config)
            self.logger.info("PyMuPDF extractor initialized")
        except ImportError as e:
            self.logger.warning(f"PyMuPDF not available: {e}")
        
        try:
            self.extractors['pdfplumber'] = PDFPlumberExtractor(self.config)
            self.logger.info("PDFplumber extractor initialized")
        except ImportError as e:
            self.logger.warning(f"PDFplumber not available: {e}")
        
        if not self.extractors:
            raise RuntimeError("No PDF extraction libraries available. Install PyMuPDF or pdfplumber.")
    
    def process_pdf(self, pdf_path: str, 
                   extraction_method: ExtractionMethod = ExtractionMethod.AUTO,
                   publisher_profile: Optional[PublisherType] = None) -> ProcessingResult:
        """
        Process a PDF file and extract structured content
        
        Args:
            pdf_path: Path to PDF file
            extraction_method: Extraction strategy to use
            publisher_profile: Optional publisher-specific optimization
            
        Returns:
            ProcessingResult containing the extracted document or error information
        """
        result = ProcessingResult()
        start_time = time.time()
        
        try:
            # Validate input
            if not Path(pdf_path).exists():
                result.add_error(f"PDF file not found: {pdf_path}")
                return result
            
            self.logger.info(f"Processing PDF: {pdf_path}")
            self.stats['total_processed'] += 1
            
            # Apply publisher profile if specified
            if publisher_profile:
                self._apply_publisher_profile(publisher_profile)
            
            # Determine extraction strategy
            chosen_extractor = self._select_extractor(pdf_path, extraction_method)
            if not chosen_extractor:
                result.add_error("No suitable extractor available")
                return result
            
            result.extraction_method = chosen_extractor
            
            # Extract content
            extraction_result = self.extractors[chosen_extractor].extract_text(pdf_path)
            
            if not extraction_result.success:
                # Try fallback extractor if primary failed
                fallback_extractor = self._get_fallback_extractor(chosen_extractor)
                if fallback_extractor:
                    self.logger.warning(f"Primary extractor {chosen_extractor} failed, trying {fallback_extractor}")
                    extraction_result = self.extractors[fallback_extractor].extract_text(pdf_path)
                    if extraction_result.success:
                        result.extraction_method = f"{chosen_extractor}->{fallback_extractor}"
            
            if not extraction_result.success:
                result.errors.extend(extraction_result.errors)
                result.warnings.extend(extraction_result.warnings)
                result.add_error("All extraction methods failed")
                self.stats['failed_extractions'] += 1
                return result
            
            # Build document
            document = self._build_document(pdf_path, extraction_result)
            
            # Apply post-processing enhancements
            document = self._enhance_document(document)
            
            # Calculate confidence score
            confidence = self._calculate_confidence_score(extraction_result, document)
            
            # Set result
            result.document = document
            result.success = True
            result.confidence_score = confidence
            result.warnings.extend(extraction_result.warnings)
            
            self.stats['successful_extractions'] += 1
            self.stats['extraction_methods'][result.extraction_method] = \
                self.stats['extraction_methods'].get(result.extraction_method, 0) + 1
            
            self.logger.info(f"Successfully processed {pdf_path} using {result.extraction_method}")
            
        except Exception as e:
            result.add_error(f"Processing failed: {str(e)}")
            self.logger.error(f"Processing error for {pdf_path}: {e}")
            self.stats['failed_extractions'] += 1
        
        finally:
            result.processing_time = time.time() - start_time
        
        return result
    
    def _select_extractor(self, pdf_path: str, method: ExtractionMethod) -> Optional[str]:
        """Select the best extractor for the given PDF and method"""
        
        if method == ExtractionMethod.PYMUPDF and 'pymupdf' in self.extractors:
            return 'pymupdf'
        elif method == ExtractionMethod.PDFPLUMBER and 'pdfplumber' in self.extractors:
            return 'pdfplumber'
        elif method == ExtractionMethod.AUTO:
            return self._auto_select_extractor(pdf_path)
        elif method == ExtractionMethod.HYBRID:
            # For hybrid, we'll use primary then combine with secondary
            return self.config.primary_library if self.config.primary_library in self.extractors else None
        
        # Fallback to first available extractor
        return next(iter(self.extractors.keys())) if self.extractors else None
    
    def _auto_select_extractor(self, pdf_path: str) -> str:
        """Automatically select the best extractor based on PDF characteristics"""
        
        # Quick analysis to choose extractor
        file_size = Path(pdf_path).stat().st_size
        
        # For very large files, prefer PyMuPDF (usually faster)
        if file_size > 50 * 1024 * 1024 and 'pymupdf' in self.extractors:  # > 50MB
            return 'pymupdf'
        
        # For files that likely contain tables, prefer pdfplumber
        try:
            # Quick check for table-heavy documents by examining filename/metadata
            filename_lower = Path(pdf_path).name.lower()
            table_indicators = ['table', 'data', 'report', 'statistics', 'financial']
            
            if any(indicator in filename_lower for indicator in table_indicators) and 'pdfplumber' in self.extractors:
                return 'pdfplumber'
        except:
            pass
        
        # Default preference based on config
        primary = self.config.primary_library
        if primary in self.extractors:
            return primary
        
        # Fallback to first available
        return next(iter(self.extractors.keys()))
    
    def _get_fallback_extractor(self, primary: str) -> Optional[str]:
        """Get fallback extractor if primary fails"""
        if primary == 'pymupdf' and 'pdfplumber' in self.extractors:
            return 'pdfplumber'
        elif primary == 'pdfplumber' and 'pymupdf' in self.extractors:
            return 'pymupdf'
        return None
    
    def _apply_publisher_profile(self, publisher: PublisherType):
        """Apply publisher-specific configuration"""
        profile_config = PublisherProfile.get_profile(publisher)
        
        # Merge profile settings with current config
        # This is a simplified merge - could be more sophisticated
        if hasattr(profile_config, 'extraction'):
            for key, value in profile_config.extraction.__dict__.items():
                setattr(self.config.extraction, key, value)
        
        if hasattr(profile_config, 'layout'):
            for key, value in profile_config.layout.__dict__.items():
                setattr(self.config.layout, key, value)
        
        if hasattr(profile_config, 'metadata'):
            for key, value in profile_config.metadata.__dict__.items():
                setattr(self.config.metadata, key, value)
        
        self.logger.info(f"Applied {publisher.value} publisher profile")
    
    def _build_document(self, pdf_path: str, extraction_result) -> Document:
        """Build Document object from extraction results"""
        
        document = Document(
            file_path=pdf_path,
            file_name=Path(pdf_path).name,
            metadata=extraction_result.metadata,
            sections=extraction_result.sections,
            num_pages=extraction_result.page_count,
            processing_time=extraction_result.extraction_time,
            extraction_method=self.extractors[self._select_extractor(pdf_path, ExtractionMethod.AUTO)].__class__.__name__,
        )
        
        return document
    
    def _enhance_document(self, document: Document) -> Document:
        """Apply post-processing enhancements to the document"""
        
        # Advanced layout analysis
        page_layouts = self.layout_analyzer.analyze_document_layout(document)
        
        # Apply layout-based improvements
        if page_layouts:
            document = self._apply_layout_improvements(document, page_layouts)
            
            # Update statistics
            layout_stats = self.layout_analyzer.get_layout_statistics(page_layouts)
            self._update_layout_stats(layout_stats)
        
        # Cross-reference resolution
        if self.config.extraction.extract_footnotes:
            document = self._resolve_cross_references(document)
        
        # Section hierarchy optimization
        document.sections = self._optimize_section_hierarchy(document.sections)
        
        # Reference extraction and parsing
        if self.config.metadata.extract_references:
            references = self._extract_references(document)
            document.references = references
        
        # Calculate final statistics
        document._calculate_stats()
        
        return document
    
    def _resolve_cross_references(self, document: Document) -> Document:
        """Resolve cross-references within the document"""
        # Placeholder for cross-reference resolution logic
        # This would identify and link "see Section 2.1", "Table 1", etc.
        return document
    
    def _optimize_section_hierarchy(self, sections: List[Section]) -> List[Section]:
        """Optimize section hierarchy and nesting"""
        if not sections:
            return sections
        
        # Simple hierarchy optimization
        optimized = []
        current_parent = None
        
        for section in sections:
            if section.level == 1:
                # Top-level section
                current_parent = section
                optimized.append(section)
            elif section.level > 1 and current_parent:
                # Subsection - add to parent
                current_parent.subsections.append(section)
            else:
                # Fallback - add as top-level
                optimized.append(section)
        
        return optimized
    
    def _extract_references(self, document: Document) -> List:
        """Extract and parse bibliographic references"""
        # Placeholder for reference extraction logic
        # This would find the references section and parse citations
        references = []
        
        # Look for references section
        for section in document.sections:
            if 'reference' in section.title.lower():
                # Parse references from this section
                # This would use citation parsing libraries
                break
        
        return references
    
    def _calculate_confidence_score(self, extraction_result, document: Document) -> float:
        """Calculate confidence score for the extraction"""
        score = 1.0
        
        # Reduce score based on errors and warnings
        if extraction_result.errors:
            score -= 0.3 * len(extraction_result.errors)
        if extraction_result.warnings:
            score -= 0.1 * len(extraction_result.warnings)
        
        # Boost score for good extraction indicators
        if document.metadata.title:
            score += 0.1
        if document.metadata.authors:
            score += 0.1
        if len(document.sections) > 1:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _apply_layout_improvements(self, document: Document, page_layouts: List[PageLayout]) -> Document:
        """Apply layout-based improvements to document structure"""
        
        # Reorganize sections based on layout analysis
        if page_layouts:
            # Check for mixed layouts and adjust section boundaries
            for layout in page_layouts:
                if layout.column_layout.is_mixed_layout():
                    self._handle_mixed_layout_sections(document, layout)
            
            # Improve reading order within sections
            document.sections = self._reorder_sections_by_layout(document.sections, page_layouts)
        
        return document
    
    def _handle_mixed_layout_sections(self, document: Document, layout: PageLayout):
        """Handle sections in mixed layout pages (abstract + columns)"""
        
        # Find sections on this page
        page_sections = [s for s in document.sections if s.page_start <= layout.page_number <= s.page_end]
        
        for section in page_sections:
            # Reorder content within section based on layout analysis
            layout_elements = layout.get_elements_by_role('body')
            
            if layout_elements:
                # Sort section content by layout reading order
                section.content.sort(key=lambda x: self._get_element_layout_order(x, layout_elements))
    
    def _get_element_layout_order(self, content_element, layout_elements) -> int:
        """Get the reading order index for a content element"""
        
        # Match content element to layout element by position/content similarity
        for layout_elem in layout_elements:
            if (hasattr(content_element, 'content') and 
                content_element.content == layout_elem.content):
                return layout_elem.reading_order_index
        
        return 999999  # Put unmatched elements at end
    
    def _reorder_sections_by_layout(self, sections: List[Section], page_layouts: List[PageLayout]) -> List[Section]:
        """Reorder sections based on layout analysis"""
        
        # This is a simplified implementation
        # A more sophisticated version would use the reading order from layout analysis
        
        # Group sections by page
        page_sections = {}
        for section in sections:
            for page_num in range(section.page_start, section.page_end + 1):
                if page_num not in page_sections:
                    page_sections[page_num] = []
                page_sections[page_num].append(section)
        
        # Reorder sections within each page based on layout
        reordered_sections = []
        processed_sections = set()
        
        for layout in sorted(page_layouts, key=lambda x: x.page_number):
            page_sects = page_sections.get(layout.page_number, [])
            
            for section in page_sects:
                if id(section) not in processed_sections:
                    reordered_sections.append(section)
                    processed_sections.add(id(section))
        
        # Add any remaining sections
        for section in sections:
            if id(section) not in processed_sections:
                reordered_sections.append(section)
        
        return reordered_sections
    
    def _update_layout_stats(self, layout_stats: Dict[str, Any]):
        """Update processing statistics with layout analysis results"""
        
        self.stats['layout_analysis']['pages_analyzed'] = layout_stats.get('total_pages', 0)
        self.stats['layout_analysis']['mixed_layouts_detected'] = layout_stats.get('pages_with_mixed_layout', 0)
        self.stats['layout_analysis']['average_confidence'] = layout_stats.get('average_confidence', 0.0)
    
    def process_multiple_pdfs(self, pdf_paths: List[str], 
                             extraction_method: ExtractionMethod = ExtractionMethod.AUTO) -> List[ProcessingResult]:
        """Process multiple PDFs in sequence"""
        results = []
        
        for pdf_path in pdf_paths:
            result = self.process_pdf(pdf_path, extraction_method)
            results.append(result)
            
            if not result.success:
                self.logger.warning(f"Failed to process {pdf_path}: {result.errors}")
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        success_rate = (self.stats['successful_extractions'] / 
                       max(1, self.stats['total_processed'])) * 100
        
        return {
            **self.stats,
            'success_rate': success_rate,
            'available_extractors': list(self.extractors.keys()),
            'config': self.config.to_dict(),
        }
    
    def validate_pdf_batch(self, pdf_paths: List[str]) -> Dict[str, Any]:
        """Validate multiple PDFs and return batch analysis"""
        valid_pdfs = []
        invalid_pdfs = []
        
        for pdf_path in pdf_paths:
            for extractor in self.extractors.values():
                is_valid, error = extractor.validate_pdf(pdf_path)
                if is_valid:
                    valid_pdfs.append(pdf_path)
                    break
            else:
                invalid_pdfs.append({'path': pdf_path, 'error': error})
        
        return {
            'total': len(pdf_paths),
            'valid': len(valid_pdfs),
            'invalid': len(invalid_pdfs),
            'valid_files': valid_pdfs,
            'invalid_files': invalid_pdfs,
        }
    
    def set_publisher_profile(self, publisher: Union[PublisherType, str]):
        """Set publisher profile for subsequent processing"""
        if isinstance(publisher, str):
            publisher = PublisherType(publisher.lower())
        
        self._apply_publisher_profile(publisher)
    
    def reset_config(self):
        """Reset configuration to default academic settings"""
        self.config = get_academic_config()
        self._initialize_extractors()


# Convenience functions
def process_single_pdf(pdf_path: str, 
                      config: Optional[ProcessorConfig] = None,
                      publisher: Optional[PublisherType] = None) -> Document:
    """
    Convenience function to process a single PDF
    
    Args:
        pdf_path: Path to PDF file
        config: Optional custom configuration
        publisher: Optional publisher profile
        
    Returns:
        Document object or None if processing failed
        
    Raises:
        Exception if processing fails completely
    """
    processor = PDFProcessor(config)
    
    if publisher:
        processor.set_publisher_profile(publisher)
    
    result = processor.process_pdf(pdf_path)
    
    if not result.success:
        raise Exception(f"PDF processing failed: {', '.join(result.errors)}")
    
    return result.document


def detect_publisher_from_pdf(pdf_path: str) -> PublisherType:
    """
    Detect publisher type from PDF content
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Detected publisher type
    """
    # Quick extraction to analyze content
    try:
        processor = PDFProcessor()
        extractor = next(iter(processor.extractors.values()))
        
        # Get first page content for analysis
        # This is a simplified version - full implementation would be more thorough
        metadata = extractor.extract_metadata(pdf_path)
        
        # Analyze metadata and content for publisher detection
        return PublisherProfile.detect_publisher(pdf_path, metadata.title)
        
    except Exception:
        return PublisherType.GENERIC