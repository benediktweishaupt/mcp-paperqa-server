"""
Configuration management for PDF processing with academic-specific profiles
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path


class PublisherType(Enum):
    """Supported academic publisher types"""
    IEEE = "ieee"
    ACM = "acm"
    SPRINGER = "springer"
    ELSEVIER = "elsevier"
    ARXIV = "arxiv"
    GENERIC = "generic"


@dataclass
class ExtractionSettings:
    """Settings for text extraction"""
    preserve_layout: bool = True
    detect_columns: bool = True
    extract_tables: bool = True
    extract_images: bool = False
    extract_footnotes: bool = True
    extract_headers_footers: bool = False
    min_text_length: int = 10
    remove_hyphenation: bool = True
    normalize_whitespace: bool = True


@dataclass  
class LayoutSettings:
    """Settings for layout analysis"""
    column_threshold: float = 0.7
    paragraph_spacing_threshold: float = 12.0
    section_detection_enabled: bool = True
    heading_detection_enabled: bool = True
    font_size_threshold: float = 2.0
    bold_weight_threshold: int = 600
    margin_threshold: float = 50.0


@dataclass
class MetadataSettings:
    """Settings for metadata extraction"""
    extract_title: bool = True
    extract_authors: bool = True
    extract_abstract: bool = True
    extract_keywords: bool = True
    extract_references: bool = True
    extract_doi: bool = True
    extract_publication_info: bool = True
    title_max_length: int = 300
    abstract_max_length: int = 2000


@dataclass
class ProcessorConfig:
    """Main configuration for PDF processor"""
    extraction: ExtractionSettings = field(default_factory=ExtractionSettings)
    layout: LayoutSettings = field(default_factory=LayoutSettings)
    metadata: MetadataSettings = field(default_factory=MetadataSettings)
    
    # Library preferences
    primary_library: str = "pymupdf"  # pymupdf or pdfplumber
    fallback_library: str = "pdfplumber"
    
    # Performance settings
    max_pages_per_batch: int = 10
    use_multiprocessing: bool = False
    max_workers: int = 4
    
    # Error handling
    strict_mode: bool = False
    continue_on_errors: bool = True
    log_extraction_warnings: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "extraction": self.extraction.__dict__,
            "layout": self.layout.__dict__,
            "metadata": self.metadata.__dict__,
            "primary_library": self.primary_library,
            "fallback_library": self.fallback_library,
            "max_pages_per_batch": self.max_pages_per_batch,
            "use_multiprocessing": self.use_multiprocessing,
            "max_workers": self.max_workers,
            "strict_mode": self.strict_mode,
            "continue_on_errors": self.continue_on_errors,
            "log_extraction_warnings": self.log_extraction_warnings,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessorConfig":
        """Create config from dictionary"""
        config = cls()
        
        if "extraction" in data:
            config.extraction = ExtractionSettings(**data["extraction"])
        if "layout" in data:
            config.layout = LayoutSettings(**data["layout"])
        if "metadata" in data:
            config.metadata = MetadataSettings(**data["metadata"])
            
        # Update other fields
        for key, value in data.items():
            if key not in ["extraction", "layout", "metadata"] and hasattr(config, key):
                setattr(config, key, value)
                
        return config


class PublisherProfile:
    """Publisher-specific configuration profiles"""
    
    # Predefined profiles for major academic publishers
    PROFILES: Dict[PublisherType, Dict[str, Any]] = {
        PublisherType.IEEE: {
            "extraction": {
                "detect_columns": True,
                "extract_tables": True,
                "extract_footnotes": False,  # IEEE uses endnotes
                "remove_hyphenation": True,
            },
            "layout": {
                "column_threshold": 0.6,
                "paragraph_spacing_threshold": 10.0,
                "font_size_threshold": 1.5,
            },
            "metadata": {
                "extract_abstract": True,
                "extract_keywords": True,
                "title_max_length": 200,
            }
        },
        
        PublisherType.ACM: {
            "extraction": {
                "detect_columns": True,
                "extract_tables": True,
                "extract_footnotes": True,
                "remove_hyphenation": True,
            },
            "layout": {
                "column_threshold": 0.65,
                "paragraph_spacing_threshold": 12.0,
                "font_size_threshold": 2.0,
            },
            "metadata": {
                "extract_abstract": True,
                "extract_keywords": True,
                "title_max_length": 250,
            }
        },
        
        PublisherType.SPRINGER: {
            "extraction": {
                "detect_columns": False,  # Usually single column
                "extract_tables": True,
                "extract_footnotes": True,
                "remove_hyphenation": True,
            },
            "layout": {
                "column_threshold": 0.8,
                "paragraph_spacing_threshold": 14.0,
                "font_size_threshold": 2.5,
            },
            "metadata": {
                "extract_abstract": True,
                "extract_keywords": True,
                "title_max_length": 300,
            }
        },
        
        PublisherType.ELSEVIER: {
            "extraction": {
                "detect_columns": True,
                "extract_tables": True,
                "extract_footnotes": True,
                "remove_hyphenation": True,
            },
            "layout": {
                "column_threshold": 0.7,
                "paragraph_spacing_threshold": 11.0,
                "font_size_threshold": 2.0,
            },
            "metadata": {
                "extract_abstract": True,
                "extract_keywords": True,
                "title_max_length": 250,
            }
        },
        
        PublisherType.ARXIV: {
            "extraction": {
                "detect_columns": False,  # Usually single column
                "extract_tables": True,
                "extract_footnotes": True,
                "remove_hyphenation": True,
            },
            "layout": {
                "column_threshold": 0.9,
                "paragraph_spacing_threshold": 12.0,
                "font_size_threshold": 2.0,
            },
            "metadata": {
                "extract_abstract": True,
                "extract_keywords": False,  # ArXiv doesn't always have keywords
                "title_max_length": 200,
            }
        },
    }
    
    @classmethod
    def get_profile(cls, publisher: PublisherType) -> ProcessorConfig:
        """Get configuration for specific publisher"""
        if publisher not in cls.PROFILES:
            publisher = PublisherType.GENERIC
            
        # Start with default config
        config = ProcessorConfig()
        
        # Apply publisher-specific overrides
        if publisher in cls.PROFILES:
            profile_data = cls.PROFILES[publisher]
            config = ProcessorConfig.from_dict(profile_data)
            
        return config
    
    @classmethod
    def detect_publisher(cls, pdf_path: str, content_sample: Optional[str] = None) -> PublisherType:
        """Detect publisher from PDF metadata or content"""
        # This is a placeholder - implement actual detection logic
        # Could analyze:
        # - PDF metadata (creator, producer fields)
        # - Text patterns and formatting
        # - DOI prefixes
        # - Citation formats
        
        if content_sample:
            content_lower = content_sample.lower()
            
            # Simple heuristic detection
            if "ieee" in content_lower or "10.1109" in content_lower:
                return PublisherType.IEEE
            elif "acm" in content_lower or "10.1145" in content_lower:
                return PublisherType.ACM
            elif "springer" in content_lower or "10.1007" in content_lower:
                return PublisherType.SPRINGER
            elif "elsevier" in content_lower or "10.1016" in content_lower:
                return PublisherType.ELSEVIER
            elif "arxiv" in content_lower or "arxiv.org" in content_lower:
                return PublisherType.ARXIV
                
        return PublisherType.GENERIC
    
    @classmethod
    def save_profile(cls, profile_name: str, config: ProcessorConfig, path: str):
        """Save custom profile to file"""
        profile_data = {
            "name": profile_name,
            "config": config.to_dict(),
        }
        
        with open(path, 'w') as f:
            json.dump(profile_data, f, indent=2)
    
    @classmethod
    def load_profile(cls, path: str) -> ProcessorConfig:
        """Load custom profile from file"""
        with open(path, 'r') as f:
            profile_data = json.load(f)
            
        return ProcessorConfig.from_dict(profile_data["config"])


def get_default_config() -> ProcessorConfig:
    """Get default processing configuration"""
    return ProcessorConfig()


def get_academic_config() -> ProcessorConfig:
    """Get configuration optimized for academic documents"""
    config = ProcessorConfig()
    
    # Academic-specific optimizations
    config.extraction.preserve_layout = True
    config.extraction.detect_columns = True
    config.extraction.extract_footnotes = True
    config.extraction.remove_hyphenation = True
    
    config.layout.section_detection_enabled = True
    config.layout.heading_detection_enabled = True
    
    config.metadata.extract_abstract = True
    config.metadata.extract_references = True
    config.metadata.extract_doi = True
    
    return config