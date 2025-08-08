"""
Base class for PDF text extractors
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

from ..models import Document, Metadata, Section, Paragraph, Heading, TextElement
from ..config import ProcessorConfig


class ExtractionResult:
    """Container for extraction results"""
    def __init__(self):
        self.text_elements: List[TextElement] = []
        self.sections: List[Section] = []
        self.metadata: Metadata = Metadata()
        self.page_count: int = 0
        self.extraction_time: float = 0.0
        self.success: bool = False
        self.errors: List[str] = []
        self.warnings: List[str] = []


class BaseExtractor(ABC):
    """Abstract base class for PDF text extractors"""
    
    def __init__(self, config: ProcessorConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @abstractmethod
    def extract_text(self, pdf_path: str) -> ExtractionResult:
        """Extract text from PDF file"""
        pass
    
    @abstractmethod
    def extract_metadata(self, pdf_path: str) -> Metadata:
        """Extract metadata from PDF file"""
        pass
    
    @abstractmethod
    def get_page_count(self, pdf_path: str) -> int:
        """Get number of pages in PDF"""
        pass
    
    @abstractmethod
    def validate_pdf(self, pdf_path: str) -> Tuple[bool, Optional[str]]:
        """Validate that PDF can be processed"""
        pass
    
    def _validate_file_exists(self, pdf_path: str) -> bool:
        """Check if PDF file exists"""
        return Path(pdf_path).exists()
    
    def _get_file_size(self, pdf_path: str) -> int:
        """Get file size in bytes"""
        try:
            return Path(pdf_path).stat().st_size
        except Exception:
            return 0
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
            
        # Remove excessive whitespace
        if self.config.extraction.normalize_whitespace:
            import re
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n\s*\n', '\n\n', text)
            
        # Remove hyphenation
        if self.config.extraction.remove_hyphenation:
            text = self._remove_hyphenation(text)
            
        return text.strip()
    
    def _remove_hyphenation(self, text: str) -> str:
        """Remove hyphenation from text"""
        import re
        # Remove hyphens at end of lines followed by continuation
        text = re.sub(r'-\s*\n\s*([a-z])', r'\1', text)
        return text
    
    def _detect_font_changes(self, elements: List[TextElement]) -> List[TextElement]:
        """Detect font changes to identify headings"""
        if not elements:
            return elements
            
        # Calculate average font size
        font_sizes = []
        for elem in elements:
            if elem.font_info.get('size'):
                font_sizes.append(elem.font_info['size'])
                
        if not font_sizes:
            return elements
            
        avg_font_size = sum(font_sizes) / len(font_sizes)
        threshold = avg_font_size + self.config.layout.font_size_threshold
        
        # Mark elements with larger fonts as potential headings
        for elem in elements:
            font_size = elem.font_info.get('size', avg_font_size)
            is_bold = elem.font_info.get('weight', 400) >= self.config.layout.bold_weight_threshold
            
            if font_size >= threshold or is_bold:
                # Could be a heading - further analysis needed
                elem.metadata['potential_heading'] = True
                
        return elements
    
    def _group_into_sections(self, elements: List[TextElement]) -> List[Section]:
        """Group text elements into sections based on headings"""
        sections = []
        current_section = None
        
        for elem in elements:
            if elem.metadata.get('potential_heading') and isinstance(elem, Heading):
                # Start new section
                if current_section:
                    sections.append(current_section)
                    
                current_section = Section(
                    title=elem.content,
                    level=elem.level,
                    number=elem.numbering,
                    page_start=elem.page_number,
                    page_end=elem.page_number
                )
                current_section.content.append(elem)
                
            elif current_section:
                # Add to current section
                current_section.content.append(elem)
                current_section.page_end = elem.page_number
                
            else:
                # No section yet, create default one
                if not current_section:
                    current_section = Section(
                        title="Content",
                        level=1,
                        page_start=elem.page_number,
                        page_end=elem.page_number
                    )
                current_section.content.append(elem)
                current_section.page_end = elem.page_number
        
        # Add final section
        if current_section:
            sections.append(current_section)
            
        return sections
    
    def _extract_basic_metadata(self, pdf_path: str) -> Metadata:
        """Extract basic metadata available to all extractors"""
        metadata = Metadata()
        
        # File information
        path = Path(pdf_path)
        stat = path.stat()
        
        metadata.creation_date = None  # Will be set by specific extractor
        metadata.modification_date = None  # Will be set by specific extractor
        
        return metadata
    
    def _log_extraction_stats(self, result: ExtractionResult, pdf_path: str):
        """Log extraction statistics"""
        self.logger.info(f"Extracted {len(result.text_elements)} text elements from {pdf_path}")
        self.logger.info(f"Found {len(result.sections)} sections")
        self.logger.info(f"Processing time: {result.extraction_time:.2f}s")
        
        if result.warnings:
            for warning in result.warnings:
                self.logger.warning(warning)
                
        if result.errors:
            for error in result.errors:
                self.logger.error(error)