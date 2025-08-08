"""
PyMuPDF-based PDF text extractor with academic document support
"""

import time
from typing import List, Dict, Any, Optional, Tuple
import logging

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from .base_extractor import BaseExtractor, ExtractionResult
from ..models import Document, Metadata, Section, Paragraph, Heading, TextElement, ContentType
from ..config import ProcessorConfig


class PyMuPDFExtractor(BaseExtractor):
    """PDF text extractor using PyMuPDF (fitz)"""
    
    def __init__(self, config: ProcessorConfig):
        super().__init__(config)
        
        if not fitz:
            raise ImportError("PyMuPDF (fitz) not installed. Install with: pip install PyMuPDF")
    
    def extract_text(self, pdf_path: str) -> ExtractionResult:
        """Extract text using PyMuPDF with academic optimizations"""
        result = ExtractionResult()
        start_time = time.time()
        
        try:
            # Validate PDF
            is_valid, error_msg = self.validate_pdf(pdf_path)
            if not is_valid:
                result.errors.append(f"PDF validation failed: {error_msg}")
                return result
            
            # Open PDF
            doc = fitz.open(pdf_path)
            result.page_count = doc.page_count
            
            self.logger.info(f"Processing {result.page_count} pages from {pdf_path}")
            
            # Extract metadata first
            result.metadata = self.extract_metadata(pdf_path)
            
            # Process pages in batches
            batch_size = self.config.max_pages_per_batch
            for batch_start in range(0, result.page_count, batch_size):
                batch_end = min(batch_start + batch_size, result.page_count)
                batch_elements = self._extract_page_batch(doc, batch_start, batch_end)
                result.text_elements.extend(batch_elements)
            
            doc.close()
            
            # Post-process extracted elements
            result.text_elements = self._detect_font_changes(result.text_elements)
            result.sections = self._group_into_sections(result.text_elements)
            
            result.success = True
            
        except Exception as e:
            result.errors.append(f"PyMuPDF extraction failed: {str(e)}")
            self.logger.error(f"Extraction error: {e}")
        
        finally:
            result.extraction_time = time.time() - start_time
            self._log_extraction_stats(result, pdf_path)
        
        return result
    
    def _extract_page_batch(self, doc: fitz.Document, start_page: int, end_page: int) -> List[TextElement]:
        """Extract text from a batch of pages"""
        elements = []
        
        for page_num in range(start_page, end_page):
            try:
                page = doc[page_num]
                page_elements = self._extract_page_content(page, page_num + 1)
                elements.extend(page_elements)
                
            except Exception as e:
                self.logger.warning(f"Failed to process page {page_num + 1}: {e}")
                if not self.config.continue_on_errors:
                    raise
        
        return elements
    
    def _extract_page_content(self, page: fitz.Page, page_number: int) -> List[TextElement]:
        """Extract content from a single page with layout analysis"""
        elements = []
        
        try:
            # Get text with detailed formatting information
            text_dict = page.get_text("dict")
            
            # Process blocks (paragraphs/sections)
            for block in text_dict.get("blocks", []):
                if "lines" not in block:  # Skip image blocks
                    continue
                
                block_elements = self._process_text_block(block, page_number)
                elements.extend(block_elements)
                
        except Exception as e:
            self.logger.warning(f"Page {page_number} processing error: {e}")
            
            # Fallback to simple text extraction
            try:
                simple_text = page.get_text()
                if simple_text.strip():
                    fallback_element = Paragraph(
                        content=self._clean_text(simple_text),
                        page_number=page_number,
                        confidence=0.5  # Lower confidence for fallback
                    )
                    elements.append(fallback_element)
            except Exception as fallback_error:
                self.logger.error(f"Fallback extraction failed for page {page_number}: {fallback_error}")
        
        return elements
    
    def _process_text_block(self, block: Dict[str, Any], page_number: int) -> List[TextElement]:
        """Process a text block and extract elements"""
        elements = []
        
        # Get block position
        bbox = block.get("bbox", [0, 0, 0, 0])
        block_position = {
            "x": bbox[0],
            "y": bbox[1], 
            "width": bbox[2] - bbox[0],
            "height": bbox[3] - bbox[1]
        }
        
        # Combine all text from lines in block
        block_text_parts = []
        font_info = {}
        
        for line in block.get("lines", []):
            line_text_parts = []
            
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text:
                    continue
                    
                line_text_parts.append(text)
                
                # Collect font information from first significant span
                if not font_info and len(text) > 3:
                    font_info = {
                        "size": span.get("size", 12),
                        "flags": span.get("flags", 0),
                        "font": span.get("font", ""),
                        "color": span.get("color", 0)
                    }
            
            if line_text_parts:
                block_text_parts.append(" ".join(line_text_parts))
        
        # Create text element from block
        if block_text_parts:
            block_text = "\n".join(block_text_parts)
            block_text = self._clean_text(block_text)
            
            if len(block_text) < self.config.extraction.min_text_length:
                return elements
            
            # Determine element type based on formatting
            is_heading = self._is_likely_heading(block_text, font_info, block_position)
            
            if is_heading:
                heading = Heading(
                    content=block_text,
                    page_number=page_number,
                    position=block_position,
                    font_info=font_info,
                    level=self._estimate_heading_level(font_info)
                )
                elements.append(heading)
            else:
                paragraph = Paragraph(
                    content=block_text,
                    page_number=page_number,
                    position=block_position,
                    font_info=font_info
                )
                elements.append(paragraph)
        
        return elements
    
    def _is_likely_heading(self, text: str, font_info: Dict[str, Any], position: Dict[str, float]) -> bool:
        """Determine if text is likely a heading"""
        if not text or len(text) > 200:  # Headings are usually short
            return False
        
        # Check font formatting
        flags = font_info.get("flags", 0)
        is_bold = bool(flags & 2**4)  # Bold flag
        font_size = font_info.get("size", 12)
        
        # Check if text looks like a heading pattern
        import re
        
        # Section numbering patterns
        has_numbering = bool(re.match(r'^\d+\.?\s+', text))
        has_roman_numbering = bool(re.match(r'^[IVX]+\.?\s+', text))
        
        # Common heading words
        heading_words = ['abstract', 'introduction', 'conclusion', 'references', 
                        'methodology', 'results', 'discussion', 'acknowledgments']
        starts_with_heading_word = any(text.lower().startswith(word) for word in heading_words)
        
        # Title case pattern
        words = text.split()
        is_title_case = len(words) > 1 and sum(1 for w in words if w[0].isupper()) >= len(words) * 0.7
        
        # Combine heuristics
        score = 0
        if is_bold: score += 2
        if font_size > 14: score += 2
        if has_numbering or has_roman_numbering: score += 3
        if starts_with_heading_word: score += 2
        if is_title_case: score += 1
        if len(text) < 100: score += 1
        
        return score >= 3
    
    def _estimate_heading_level(self, font_info: Dict[str, Any]) -> int:
        """Estimate heading level based on font size"""
        font_size = font_info.get("size", 12)
        
        if font_size >= 18:
            return 1  # Main heading
        elif font_size >= 16:
            return 2  # Section heading
        elif font_size >= 14:
            return 3  # Subsection heading
        else:
            return 4  # Minor heading
    
    def extract_metadata(self, pdf_path: str) -> Metadata:
        """Extract metadata using PyMuPDF"""
        metadata = self._extract_basic_metadata(pdf_path)
        
        try:
            doc = fitz.open(pdf_path)
            
            # Extract PDF metadata
            pdf_meta = doc.metadata
            
            if pdf_meta.get("title"):
                metadata.title = pdf_meta["title"].strip()
            if pdf_meta.get("author"):
                # Split multiple authors
                authors = pdf_meta["author"].strip()
                metadata.authors = [a.strip() for a in authors.split(",") if a.strip()]
            if pdf_meta.get("subject"):
                metadata.subject = pdf_meta["subject"].strip()
            if pdf_meta.get("creator"):
                metadata.creator = pdf_meta["creator"].strip()
            if pdf_meta.get("producer"):
                metadata.producer = pdf_meta["producer"].strip()
                
            # Try to extract more metadata from first page
            if doc.page_count > 0:
                first_page_text = doc[0].get_text()
                metadata = self._enhance_metadata_from_text(metadata, first_page_text)
            
            doc.close()
            
        except Exception as e:
            self.logger.warning(f"Metadata extraction failed: {e}")
        
        return metadata
    
    def _enhance_metadata_from_text(self, metadata: Metadata, text: str) -> Metadata:
        """Enhance metadata by analyzing first page text"""
        import re
        
        lines = text.split('\n')
        
        # Look for DOI
        for line in lines[:20]:  # Check first 20 lines
            doi_match = re.search(r'doi:\s*([^\s]+)', line, re.IGNORECASE)
            if doi_match:
                metadata.doi = doi_match.group(1)
                break
        
        # Look for abstract
        text_lower = text.lower()
        abstract_start = text_lower.find('abstract')
        if abstract_start != -1:
            # Find abstract content (simple heuristic)
            abstract_text = text[abstract_start:abstract_start + 2000]
            abstract_lines = abstract_text.split('\n')[1:10]  # Skip "Abstract" line
            abstract_content = ' '.join(abstract_lines).strip()
            if len(abstract_content) > 50:  # Reasonable abstract length
                metadata.abstract = abstract_content[:500]  # Limit length
        
        return metadata
    
    def get_page_count(self, pdf_path: str) -> int:
        """Get page count using PyMuPDF"""
        try:
            doc = fitz.open(pdf_path)
            count = doc.page_count
            doc.close()
            return count
        except Exception:
            return 0
    
    def validate_pdf(self, pdf_path: str) -> Tuple[bool, Optional[str]]:
        """Validate PDF file with PyMuPDF"""
        if not self._validate_file_exists(pdf_path):
            return False, "File does not exist"
        
        try:
            doc = fitz.open(pdf_path)
            
            # Check if document is valid
            if doc.is_closed:
                return False, "Document is closed/invalid"
            
            # Check if document has pages
            if doc.page_count == 0:
                return False, "Document has no pages"
            
            # Check if document is encrypted
            if doc.needs_pass:
                doc.close()
                return False, "Document is password protected"
            
            # Test access to first page
            try:
                first_page = doc[0]
                first_page.get_text()
            except Exception:
                doc.close()
                return False, "Cannot access document content"
            
            doc.close()
            return True, None
            
        except Exception as e:
            return False, f"PyMuPDF validation error: {str(e)}"