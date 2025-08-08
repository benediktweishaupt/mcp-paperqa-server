"""
Academic PDF Processing Engine

A comprehensive PDF processing library designed for academic research documents,
with support for complex layouts, metadata extraction, and structure preservation.
"""

from .core import PDFProcessor, process_single_pdf, detect_publisher_from_pdf, ExtractionMethod, ProcessingResult
from .models import Document, Section, Paragraph, Metadata, Heading, Table, Reference
from .config import ProcessorConfig, PublisherProfile, PublisherType, get_academic_config, get_default_config
from .extractors import BaseExtractor, PyMuPDFExtractor, PDFPlumberExtractor
from .layout import LayoutAnalyzer, PageLayout, LayoutType, ColumnDetector, ColumnLayout, ReadingOrderProcessor

__version__ = "0.1.0"
__author__ = "Academic MCP Server Team"

__all__ = [
    # Main processing classes
    "PDFProcessor",
    "ProcessingResult",
    "ExtractionMethod",
    
    # Convenience functions
    "process_single_pdf",
    "detect_publisher_from_pdf",
    
    # Document models
    "Document", 
    "Section",
    "Paragraph",
    "Heading",
    "Table",
    "Reference",
    "Metadata",
    
    # Configuration
    "ProcessorConfig",
    "PublisherProfile",
    "PublisherType",
    "get_academic_config",
    "get_default_config",
    
    # Extractors
    "BaseExtractor",
    "PyMuPDFExtractor", 
    "PDFPlumberExtractor",
    
    # Layout Analysis
    "LayoutAnalyzer",
    "PageLayout",
    "LayoutType",
    "ColumnDetector",
    "ColumnLayout",
    "ReadingOrderProcessor",
]