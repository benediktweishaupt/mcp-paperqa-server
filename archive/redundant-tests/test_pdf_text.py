#!/usr/bin/env python3
"""
Test script to check if PDFs have extractable text
"""

import sys
from pathlib import Path
sys.path.insert(0, 'paper-qa')

from paperqa import Docs

def test_pdf_text_extraction():
    """Test if PDFs have extractable text using PaperQA2's reader"""
    
    papers_dir = Path("paperqa-mcp/papers")
    pdfs = list(papers_dir.glob("*.pdf"))
    
    # Filter out backup files
    pdfs = [p for p in pdfs if not p.name.endswith('.original.pdf')]
    
    print(f"Testing text extraction for {len(pdfs)} PDFs:")
    
    for pdf_path in pdfs:
        print(f"\n📄 Testing: {pdf_path.name}")
        
        try:
            # Create a Docs object and try to add the PDF
            docs = Docs()
            result = docs.add(str(pdf_path))
            
            print(f"✅ Document added: {result}")
            
            # Check if any text was extracted
            if hasattr(docs, 'docs') and docs.docs:
                doc = list(docs.docs.values())[0]
                if hasattr(doc, 'texts') and doc.texts:
                    text_length = sum(len(text.text) for text in doc.texts)
                    print(f"📝 Extracted text length: {text_length} characters")
                    
                    if text_length > 100:  # Has substantial text
                        first_text = doc.texts[0].text[:200].replace('\n', ' ')
                        print(f"📖 Sample text: {first_text}...")
                        print(f"✅ {pdf_path.name} has extractable text!")
                    else:
                        print(f"❌ {pdf_path.name} has minimal text - likely needs OCR")
                else:
                    print(f"❌ {pdf_path.name} has no extractable text - needs OCR")
            else:
                print(f"❌ {pdf_path.name} could not be processed")
                
        except Exception as e:
            print(f"❌ Error testing {pdf_path.name}: {e}")

if __name__ == "__main__":
    test_pdf_text_extraction()