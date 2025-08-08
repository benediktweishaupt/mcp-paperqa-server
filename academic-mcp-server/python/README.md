# Academic PDF Processing Engine

Python-based PDF processing engine for the Academic MCP Server, designed specifically for academic research document analysis.

## Features

- **Advanced PDF Text Extraction**: Uses PyMuPDF and pdfplumber for robust text extraction
- **Academic Format Support**: Handles complex academic layouts, multi-column text, footnotes
- **Structure Preservation**: Maintains document hierarchy (chapters, sections, paragraphs)
- **Publisher Compatibility**: Optimized for IEEE, ACM, Springer, Elsevier formats
- **Metadata Extraction**: Extracts titles, authors, abstracts, references
- **Encoding Handling**: Robust handling of special characters and encoding issues

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Usage

```python
from pdf_processing import PDFProcessor, Document

# Initialize processor with academic-optimized settings
processor = PDFProcessor(
    use_academic_profiles=True,
    preserve_structure=True,
    extract_metadata=True
)

# Process a PDF
document = processor.process_pdf("path/to/academic_paper.pdf")

# Access structured content
print(document.title)
print(document.authors)
for section in document.sections:
    print(f"Section: {section.title}")
    for paragraph in section.paragraphs:
        print(paragraph.text)
```

## Configuration

The processor supports publisher-specific profiles:

```python
# IEEE format optimization
processor.set_profile("ieee")

# ACM format optimization  
processor.set_profile("acm")

# Springer format optimization
processor.set_profile("springer")

# Custom profile
processor.configure({
    "column_detection": True,
    "footnote_extraction": True,
    "reference_parsing": True,
    "table_extraction": True
})
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pdf_processing

# Run specific test category
pytest tests/extraction/
```

## Architecture

- `pdf_processing/` - Main processing modules
- `extractors/` - Text extraction engines (PyMuPDF, pdfplumber)
- `processors/` - Document structure processors
- `formats/` - Publisher-specific format handlers
- `models/` - Data models for documents and content
- `config/` - Configuration profiles and settings