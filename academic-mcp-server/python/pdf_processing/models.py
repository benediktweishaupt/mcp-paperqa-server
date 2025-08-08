"""
Data models for representing processed PDF documents and their content
"""

from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path


class ContentType(Enum):
    """Types of content elements"""
    TEXT = "text"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    FOOTNOTE = "footnote"
    REFERENCE = "reference"
    TABLE = "table"
    IMAGE = "image"
    CAPTION = "caption"
    ABSTRACT = "abstract"
    KEYWORD = "keyword"


@dataclass
class TextElement:
    """Base class for all text elements"""
    content: str
    content_type: ContentType
    page_number: int
    position: Dict[str, float] = field(default_factory=dict)  # x, y, width, height
    font_info: Dict[str, Any] = field(default_factory=dict)   # size, family, weight
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Clean and validate content"""
        if self.content:
            self.content = self.content.strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "content": self.content,
            "content_type": self.content_type.value,
            "page_number": self.page_number,
            "position": self.position,
            "font_info": self.font_info,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass
class Paragraph(TextElement):
    """Represents a paragraph with formatting information"""
    content_type: ContentType = field(default=ContentType.PARAGRAPH, init=False)
    sentences: List[str] = field(default_factory=list)
    is_justified: bool = False
    line_spacing: float = 1.0
    indent: float = 0.0
    
    def __post_init__(self):
        super().__post_init__()
        if not self.sentences and self.content:
            # Simple sentence splitting - could be enhanced with NLTK
            import re
            self.sentences = re.split(r'[.!?]+\s+', self.content)
            self.sentences = [s.strip() for s in self.sentences if s.strip()]


@dataclass
class Heading(TextElement):
    """Represents a section heading"""
    content_type: ContentType = field(default=ContentType.HEADING, init=False)
    level: int = 1  # Heading level (1=main, 2=sub, etc.)
    numbering: Optional[str] = None
    is_toc_entry: bool = False
    
    def get_anchor(self) -> str:
        """Generate anchor ID for heading"""
        import re
        # Convert to lowercase, replace spaces with hyphens, remove special chars
        anchor = re.sub(r'[^\w\s-]', '', self.content.lower())
        return re.sub(r'[\s_]+', '-', anchor)


@dataclass 
class Reference(TextElement):
    """Represents a bibliographic reference"""
    content_type: ContentType = field(default=ContentType.REFERENCE, init=False)
    ref_number: Optional[int] = None
    authors: List[str] = field(default_factory=list)
    title: Optional[str] = None
    venue: Optional[str] = None  # Journal, conference, etc.
    year: Optional[int] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    citation_style: str = "unknown"
    
    def format_citation(self, style: str = "apa") -> str:
        """Format reference in specified citation style"""
        # Placeholder for citation formatting
        if style == "apa" and self.authors and self.title and self.year:
            authors_str = ", ".join(self.authors)
            return f"{authors_str} ({self.year}). {self.title}. {self.venue or ''}"
        return self.content


@dataclass
class Table:
    """Represents a table extracted from the PDF"""
    content: List[List[str]]  # 2D array of cell contents
    headers: List[str] = field(default_factory=list)
    caption: Optional[str] = None
    page_number: int = 0
    position: Dict[str, float] = field(default_factory=dict)
    num_rows: int = 0
    num_cols: int = 0
    
    def __post_init__(self):
        if self.content:
            self.num_rows = len(self.content)
            self.num_cols = max(len(row) for row in self.content) if self.content else 0
    
    def to_csv(self) -> str:
        """Convert table to CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        if self.headers:
            writer.writerow(self.headers)
        
        for row in self.content:
            writer.writerow(row)
            
        return output.getvalue()


@dataclass
class Image:
    """Represents an image extracted from the PDF"""
    image_data: Optional[bytes] = None
    image_format: str = "png"
    width: int = 0
    height: int = 0
    caption: Optional[str] = None
    page_number: int = 0
    position: Dict[str, float] = field(default_factory=dict)
    alt_text: Optional[str] = None
    
    def save_image(self, path: str) -> bool:
        """Save image to file"""
        if not self.image_data:
            return False
            
        try:
            with open(path, 'wb') as f:
                f.write(self.image_data)
            return True
        except Exception:
            return False


@dataclass
class Section:
    """Represents a document section with hierarchical structure"""
    title: str
    level: int = 1
    number: Optional[str] = None
    content: List[Union[Paragraph, Heading, Table, Image]] = field(default_factory=list)
    subsections: List["Section"] = field(default_factory=list)
    page_start: int = 1
    page_end: int = 1
    
    def get_text_content(self) -> str:
        """Get all text content from this section"""
        text_parts = []
        
        for item in self.content:
            if isinstance(item, (Paragraph, Heading)):
                text_parts.append(item.content)
            elif isinstance(item, Table) and item.caption:
                text_parts.append(f"Table: {item.caption}")
                
        for subsection in self.subsections:
            text_parts.append(subsection.get_text_content())
            
        return "\n\n".join(text_parts)
    
    def count_words(self) -> int:
        """Count total words in section"""
        text = self.get_text_content()
        return len(text.split()) if text else 0


@dataclass
class Metadata:
    """Document metadata extracted from PDF"""
    title: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    abstract: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    doi: Optional[str] = None
    isbn: Optional[str] = None
    
    # Publication information
    journal: Optional[str] = None
    conference: Optional[str] = None
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    
    # Technical metadata
    language: str = "en"
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    
    # Academic-specific fields
    citations_count: int = 0
    references_count: int = 0
    figures_count: int = 0
    tables_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with serializable values"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat() if value else None
            else:
                result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Metadata":
        """Create from dictionary"""
        # Handle datetime fields
        for date_field in ["creation_date", "modification_date"]:
            if data.get(date_field):
                try:
                    data[date_field] = datetime.fromisoformat(data[date_field])
                except (ValueError, TypeError):
                    data[date_field] = None
                    
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


@dataclass
class Document:
    """Main document representation containing all extracted content"""
    file_path: str
    file_name: str
    metadata: Metadata = field(default_factory=Metadata)
    sections: List[Section] = field(default_factory=list)
    references: List[Reference] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    images: List[Image] = field(default_factory=list)
    
    # Processing information
    num_pages: int = 0
    processing_time: float = 0.0
    extraction_method: str = "unknown"
    processing_date: datetime = field(default_factory=datetime.now)
    confidence_score: float = 1.0
    
    # Derived properties
    word_count: int = 0
    character_count: int = 0
    
    def __post_init__(self):
        """Calculate derived properties"""
        self.file_name = Path(self.file_path).name
        self._calculate_stats()
    
    def _calculate_stats(self):
        """Calculate word and character counts"""
        all_text = self.get_full_text()
        self.word_count = len(all_text.split()) if all_text else 0
        self.character_count = len(all_text) if all_text else 0
    
    def get_full_text(self) -> str:
        """Get all text content from the document"""
        text_parts = []
        
        # Add title and abstract from metadata
        if self.metadata.title:
            text_parts.append(self.metadata.title)
        if self.metadata.abstract:
            text_parts.append(self.metadata.abstract)
            
        # Add section content
        for section in self.sections:
            text_parts.append(section.get_text_content())
            
        return "\n\n".join(text_parts)
    
    def get_section_by_title(self, title: str) -> Optional[Section]:
        """Find section by title (case-insensitive)"""
        title_lower = title.lower()
        for section in self.sections:
            if section.title.lower() == title_lower:
                return section
        return None
    
    def get_sections_by_level(self, level: int) -> List[Section]:
        """Get all sections at specified level"""
        return [s for s in self.sections if s.level == level]
    
    def export_to_dict(self) -> Dict[str, Any]:
        """Export document to dictionary for serialization"""
        return {
            "file_path": self.file_path,
            "file_name": self.file_name,
            "metadata": self.metadata.to_dict(),
            "sections": [
                {
                    "title": s.title,
                    "level": s.level,
                    "number": s.number,
                    "text_content": s.get_text_content(),
                    "page_start": s.page_start,
                    "page_end": s.page_end,
                    "word_count": s.count_words(),
                }
                for s in self.sections
            ],
            "references": [ref.to_dict() for ref in self.references],
            "tables": [
                {
                    "caption": t.caption,
                    "num_rows": t.num_rows,
                    "num_cols": t.num_cols,
                    "page_number": t.page_number,
                    "csv_data": t.to_csv(),
                }
                for t in self.tables
            ],
            "processing_info": {
                "num_pages": self.num_pages,
                "processing_time": self.processing_time,
                "extraction_method": self.extraction_method,
                "processing_date": self.processing_date.isoformat(),
                "confidence_score": self.confidence_score,
                "word_count": self.word_count,
                "character_count": self.character_count,
            },
        }
    
    def save_to_json(self, output_path: str) -> bool:
        """Save document to JSON file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.export_to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Failed to save document to JSON: {e}")
            return False
    
    @classmethod
    def load_from_json(cls, json_path: str) -> Optional["Document"]:
        """Load document from JSON file"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # This is a simplified loader - full implementation would 
            # reconstruct all objects properly
            doc = cls(
                file_path=data["file_path"],
                file_name=data["file_name"],
            )
            
            # Load metadata
            doc.metadata = Metadata.from_dict(data["metadata"])
            
            # Load processing info
            proc_info = data.get("processing_info", {})
            doc.num_pages = proc_info.get("num_pages", 0)
            doc.processing_time = proc_info.get("processing_time", 0.0)
            doc.extraction_method = proc_info.get("extraction_method", "unknown")
            doc.confidence_score = proc_info.get("confidence_score", 1.0)
            doc.word_count = proc_info.get("word_count", 0)
            doc.character_count = proc_info.get("character_count", 0)
            
            if proc_info.get("processing_date"):
                doc.processing_date = datetime.fromisoformat(proc_info["processing_date"])
            
            return doc
            
        except Exception as e:
            print(f"Failed to load document from JSON: {e}")
            return None