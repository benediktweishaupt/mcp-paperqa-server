"""
PDFplumber-based PDF text extractor optimized for academic documents
"""

import time
from typing import List, Dict, Any, Optional, Tuple
import logging

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from .base_extractor import BaseExtractor, ExtractionResult
from ..models import Document, Metadata, Section, Paragraph, Heading, TextElement, ContentType, Table
from ..config import ProcessorConfig


class PDFPlumberExtractor(BaseExtractor):
    """PDF text extractor using pdfplumber with table extraction capabilities"""
    
    def __init__(self, config: ProcessorConfig):
        super().__init__(config)
        
        if not pdfplumber:
            raise ImportError("pdfplumber not installed. Install with: pip install pdfplumber")
    
    def extract_text(self, pdf_path: str) -> ExtractionResult:
        """Extract text using pdfplumber with enhanced table and layout support"""
        result = ExtractionResult()
        start_time = time.time()
        
        try:
            # Validate PDF
            is_valid, error_msg = self.validate_pdf(pdf_path)
            if not is_valid:
                result.errors.append(f"PDF validation failed: {error_msg}")
                return result
            
            # Open PDF
            with pdfplumber.open(pdf_path) as pdf:
                result.page_count = len(pdf.pages)
                self.logger.info(f"Processing {result.page_count} pages from {pdf_path}")
                
                # Extract metadata first
                result.metadata = self.extract_metadata(pdf_path)
                
                # Process pages in batches
                batch_size = self.config.max_pages_per_batch
                for batch_start in range(0, result.page_count, batch_size):
                    batch_end = min(batch_start + batch_size, result.page_count)
                    batch_elements = self._extract_page_batch(pdf, batch_start, batch_end)
                    result.text_elements.extend(batch_elements)
                
                # Extract tables separately (pdfplumber's strength)
                if self.config.extraction.extract_tables:
                    tables = self._extract_all_tables(pdf)
                    # Tables will be integrated into sections later
            
            # Post-process extracted elements
            result.text_elements = self._detect_font_changes(result.text_elements)
            result.sections = self._group_into_sections(result.text_elements)
            
            result.success = True
            
        except Exception as e:
            result.errors.append(f"PDFplumber extraction failed: {str(e)}")
            self.logger.error(f"Extraction error: {e}")
        
        finally:
            result.extraction_time = time.time() - start_time
            self._log_extraction_stats(result, pdf_path)
        
        return result
    
    def _extract_page_batch(self, pdf: pdfplumber.PDF, start_page: int, end_page: int) -> List[TextElement]:
        """Extract text from a batch of pages"""
        elements = []
        
        for page_num in range(start_page, end_page):
            try:
                page = pdf.pages[page_num]
                page_elements = self._extract_page_content(page, page_num + 1)
                elements.extend(page_elements)
                
            except Exception as e:
                self.logger.warning(f"Failed to process page {page_num + 1}: {e}")
                if not self.config.continue_on_errors:
                    raise
        
        return elements
    
    def _extract_page_content(self, page: pdfplumber.page.Page, page_number: int) -> List[TextElement]:
        """Extract content from a single page with layout analysis"""
        elements = []
        
        try:
            # Get page dimensions for layout analysis
            page_width = page.width
            page_height = page.height
            
            # Detect columns if enabled
            if self.config.extraction.detect_columns:
                column_regions = self._detect_columns(page)
            else:
                column_regions = [{'x0': 0, 'y0': 0, 'x1': page_width, 'y1': page_height}]
            
            # Extract text from each column region
            for col_idx, region in enumerate(column_regions):
                col_elements = self._extract_column_text(page, region, page_number, col_idx)
                elements.extend(col_elements)
                
        except Exception as e:
            self.logger.warning(f"Page {page_number} processing error: {e}")
            
            # Fallback to simple text extraction
            try:
                simple_text = page.extract_text()
                if simple_text and simple_text.strip():
                    fallback_element = Paragraph(
                        content=self._clean_text(simple_text),
                        page_number=page_number,
                        confidence=0.5  # Lower confidence for fallback
                    )
                    elements.append(fallback_element)
            except Exception as fallback_error:
                self.logger.error(f"Fallback extraction failed for page {page_number}: {fallback_error}")
        
        return elements
    
    def _detect_columns(self, page: pdfplumber.page.Page) -> List[Dict[str, float]]:
        """Detect column layout on the page"""
        # Get all text objects
        chars = page.chars
        if not chars:
            return [{'x0': 0, 'y0': 0, 'x1': page.width, 'y1': page.height}]
        
        # Group characters by their x-coordinates to find column boundaries
        x_positions = sorted(set(char['x0'] for char in chars))
        
        # Simple column detection based on significant gaps in x-positions
        columns = []
        current_col_start = x_positions[0]
        
        for i in range(1, len(x_positions)):
            gap = x_positions[i] - x_positions[i-1]
            
            # If gap is significant (heuristic: > 5% of page width), it's a column boundary
            if gap > page.width * 0.05:
                columns.append({
                    'x0': current_col_start,
                    'y0': 0,
                    'x1': x_positions[i-1] + 10,  # Add some padding
                    'y1': page.height
                })
                current_col_start = x_positions[i]
        
        # Add the last column
        columns.append({
            'x0': current_col_start,
            'y0': 0,
            'x1': page.width,
            'y1': page.height
        })
        
        # Filter out very narrow columns (likely noise)
        min_column_width = page.width * 0.15  # At least 15% of page width
        columns = [col for col in columns if (col['x1'] - col['x0']) >= min_column_width]
        
        # If no reasonable columns found, default to single column
        if not columns:
            columns = [{'x0': 0, 'y0': 0, 'x1': page.width, 'y1': page.height}]
        
        return columns
    
    def _extract_column_text(self, page: pdfplumber.page.Page, region: Dict[str, float], 
                            page_number: int, column_index: int) -> List[TextElement]:
        """Extract text from a specific column region"""
        elements = []
        
        try:
            # Crop page to column region
            cropped = page.crop(region)
            
            # Extract words with position information
            words = cropped.extract_words(
                x_tolerance=3,
                y_tolerance=3,
                keep_blank_chars=False,
                use_text_flow=True,
                horizontal_ltr=True,
                vertical_ttb=True,
                extra_attrs=['fontname', 'size']
            )
            
            if not words:
                return elements
            
            # Group words into text blocks based on proximity and alignment
            text_blocks = self._group_words_into_blocks(words)
            
            # Convert blocks to text elements
            for block_idx, block in enumerate(text_blocks):
                text_content = ' '.join(word['text'] for word in block['words'])
                text_content = self._clean_text(text_content)
                
                if len(text_content) < self.config.extraction.min_text_length:
                    continue
                
                # Calculate block position
                x_positions = [w['x0'] for w in block['words']]
                y_positions = [w['top'] for w in block['words']]
                
                position = {
                    'x': min(x_positions),
                    'y': min(y_positions),
                    'width': max(w['x1'] for w in block['words']) - min(x_positions),
                    'height': max(w['bottom'] for w in block['words']) - min(y_positions),
                    'column': column_index
                }
                
                # Get font information from dominant font in block
                font_info = self._get_block_font_info(block['words'])
                
                # Determine element type
                is_heading = self._is_likely_heading_pdfplumber(text_content, font_info, position, words)
                
                if is_heading:
                    heading = Heading(
                        content=text_content,
                        page_number=page_number,
                        position=position,
                        font_info=font_info,
                        level=self._estimate_heading_level_pdfplumber(font_info)
                    )
                    elements.append(heading)
                else:
                    paragraph = Paragraph(
                        content=text_content,
                        page_number=page_number,
                        position=position,
                        font_info=font_info
                    )
                    elements.append(paragraph)
                    
        except Exception as e:
            self.logger.warning(f"Column {column_index} extraction failed: {e}")
        
        return elements
    
    def _group_words_into_blocks(self, words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group words into coherent text blocks"""
        if not words:
            return []
        
        blocks = []
        current_block = {'words': [words[0]], 'line_y': words[0]['top']}
        
        for word in words[1:]:
            # Check if word belongs to current block based on vertical proximity
            y_diff = abs(word['top'] - current_block['line_y'])
            
            # If words are on roughly the same line (within threshold)
            if y_diff <= self.config.layout.paragraph_spacing_threshold:
                current_block['words'].append(word)
            else:
                # Start new block
                blocks.append(current_block)
                current_block = {'words': [word], 'line_y': word['top']}
        
        # Add the last block
        if current_block['words']:
            blocks.append(current_block)
        
        return blocks
    
    def _get_block_font_info(self, words: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get dominant font information from a block of words"""
        if not words:
            return {}
        
        # Collect font information
        font_sizes = []
        font_names = []
        
        for word in words:
            if 'size' in word and word['size']:
                font_sizes.append(word['size'])
            if 'fontname' in word and word['fontname']:
                font_names.append(word['fontname'])
        
        # Calculate dominant font
        font_info = {}
        
        if font_sizes:
            font_info['size'] = sum(font_sizes) / len(font_sizes)  # Average size
        
        if font_names:
            # Most common font name
            from collections import Counter
            font_counter = Counter(font_names)
            font_info['font'] = font_counter.most_common(1)[0][0]
            
            # Detect bold/italic from font name
            font_name = font_info['font'].lower()
            font_info['is_bold'] = 'bold' in font_name or 'black' in font_name
            font_info['is_italic'] = 'italic' in font_name or 'oblique' in font_name
        
        return font_info
    
    def _is_likely_heading_pdfplumber(self, text: str, font_info: Dict[str, Any], 
                                     position: Dict[str, float], all_words: List[Dict[str, Any]]) -> bool:
        """Determine if text is likely a heading using pdfplumber-specific analysis"""
        if not text or len(text) > 200:
            return False
        
        # Font-based analysis
        font_size = font_info.get('size', 12)
        is_bold = font_info.get('is_bold', False)
        
        # Calculate average font size on page for comparison
        page_font_sizes = [w.get('size', 12) for w in all_words if w.get('size')]
        avg_font_size = sum(page_font_sizes) / len(page_font_sizes) if page_font_sizes else 12
        
        # Position-based analysis
        is_left_aligned = position.get('x', 0) < 100  # Close to left margin
        
        # Content-based analysis
        import re
        has_numbering = bool(re.match(r'^\d+\.?\s+', text))
        has_roman_numbering = bool(re.match(r'^[IVX]+\.?\s+', text))
        
        # Common academic section headings
        academic_headings = [
            'abstract', 'introduction', 'methodology', 'methods', 'results',
            'discussion', 'conclusion', 'references', 'acknowledgments',
            'literature review', 'background', 'related work', 'evaluation',
            'experiments', 'analysis', 'findings', 'limitations', 'future work'
        ]
        starts_with_academic_heading = any(text.lower().startswith(heading) for heading in academic_headings)
        
        # Scoring system
        score = 0
        if font_size > avg_font_size + 1: score += 2
        if is_bold: score += 2
        if has_numbering or has_roman_numbering: score += 3
        if starts_with_academic_heading: score += 2
        if is_left_aligned: score += 1
        if len(text) < 100: score += 1
        if text.isupper(): score += 1  # All caps headings
        
        return score >= 3
    
    def _estimate_heading_level_pdfplumber(self, font_info: Dict[str, Any]) -> int:
        """Estimate heading level based on font information"""
        font_size = font_info.get('size', 12)
        is_bold = font_info.get('is_bold', False)
        
        if font_size >= 18 or (font_size >= 16 and is_bold):
            return 1  # Main heading
        elif font_size >= 16 or (font_size >= 14 and is_bold):
            return 2  # Section heading
        elif font_size >= 14 or is_bold:
            return 3  # Subsection heading
        else:
            return 4  # Minor heading
    
    def _extract_all_tables(self, pdf: pdfplumber.PDF) -> List[Table]:
        """Extract all tables from the PDF (pdfplumber's specialty)"""
        tables = []
        
        for page_num, page in enumerate(pdf.pages):
            try:
                page_tables = page.extract_tables()
                
                for table_idx, table_data in enumerate(page_tables):
                    if not table_data or not any(table_data):  # Skip empty tables
                        continue
                    
                    # Clean table data
                    cleaned_data = []
                    headers = []
                    
                    for row_idx, row in enumerate(table_data):
                        if row and any(cell for cell in row if cell):  # Skip empty rows
                            cleaned_row = [str(cell).strip() if cell else "" for cell in row]
                            
                            # First non-empty row might be headers
                            if row_idx == 0 and not headers:
                                headers = cleaned_row
                            else:
                                cleaned_data.append(cleaned_row)
                    
                    if cleaned_data:  # Only add non-empty tables
                        table = Table(
                            content=cleaned_data,
                            headers=headers,
                            page_number=page_num + 1,
                            caption=f"Table {table_idx + 1} from page {page_num + 1}"
                        )
                        tables.append(table)
                        
            except Exception as e:
                self.logger.warning(f"Table extraction failed on page {page_num + 1}: {e}")
        
        self.logger.info(f"Extracted {len(tables)} tables")
        return tables
    
    def extract_metadata(self, pdf_path: str) -> Metadata:
        """Extract metadata using pdfplumber"""
        metadata = self._extract_basic_metadata(pdf_path)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Get PDF metadata
                pdf_metadata = pdf.metadata
                
                if pdf_metadata:
                    if pdf_metadata.get('Title'):
                        metadata.title = pdf_metadata['Title'].strip()
                    if pdf_metadata.get('Author'):
                        authors = pdf_metadata['Author'].strip()
                        metadata.authors = [a.strip() for a in authors.split(',') if a.strip()]
                    if pdf_metadata.get('Subject'):
                        metadata.subject = pdf_metadata['Subject'].strip()
                    if pdf_metadata.get('Creator'):
                        metadata.creator = pdf_metadata['Creator'].strip()
                    if pdf_metadata.get('Producer'):
                        metadata.producer = pdf_metadata['Producer'].strip()
                
                # Enhance with first page analysis
                if pdf.pages:
                    first_page_text = pdf.pages[0].extract_text()
                    if first_page_text:
                        metadata = self._enhance_metadata_from_text(metadata, first_page_text)
                        
        except Exception as e:
            self.logger.warning(f"Metadata extraction failed: {e}")
        
        return metadata
    
    def get_page_count(self, pdf_path: str) -> int:
        """Get page count using pdfplumber"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return len(pdf.pages)
        except Exception:
            return 0
    
    def validate_pdf(self, pdf_path: str) -> Tuple[bool, Optional[str]]:
        """Validate PDF file with pdfplumber"""
        if not self._validate_file_exists(pdf_path):
            return False, "File does not exist"
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Check if document has pages
                if not pdf.pages:
                    return False, "Document has no pages"
                
                # Test access to first page
                try:
                    first_page = pdf.pages[0]
                    first_page.extract_text()
                except Exception:
                    return False, "Cannot access document content"
                
                return True, None
                
        except Exception as e:
            return False, f"PDFplumber validation error: {str(e)}"