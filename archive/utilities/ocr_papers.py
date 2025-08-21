#!/usr/bin/env python3
"""
OCR Processing Script for Academic Papers
Converts scanned PDFs to searchable PDFs using ocrmypdf
"""

import os
import shutil
from pathlib import Path
import subprocess
import sys
from typing import List


def find_pdfs(directory: Path) -> List[Path]:
    """Find all PDF files in the directory"""
    return list(directory.glob("*.pdf"))


def backup_original(pdf_path: Path) -> Path:
    """Create backup of original PDF"""
    backup_path = pdf_path.with_suffix(".original.pdf")
    if not backup_path.exists():
        shutil.copy2(pdf_path, backup_path)
        print(f"✅ Backed up: {pdf_path.name} -> {backup_path.name}")
    else:
        print(f"⚠️  Backup already exists: {backup_path.name}")
    return backup_path


def ocr_pdf(input_path: Path, output_path: Path) -> bool:
    """
    OCR a PDF using ocrmypdf
    Returns True if successful, False otherwise
    """
    try:
        print(f"🔍 OCRing: {input_path.name}...")
        
        # Run ocrmypdf with basic settings (avoiding dependencies like unpaper)
        result = subprocess.run([
            "ocrmypdf",
            "--language", "eng+deu",  # English + German for academic papers
            "--optimize", "1",         # Light optimization
            "--skip-text",            # Skip pages that already have text
            "--deskew",               # Fix page rotation
            str(input_path),
            str(output_path)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Successfully OCR'd: {input_path.name}")
            return True
        else:
            print(f"❌ OCR failed for {input_path.name}")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during OCR of {input_path.name}: {e}")
        return False


def main():
    """Main OCR processing function"""
    
    # Set up paths
    script_dir = Path(__file__).parent
    papers_dir = script_dir / "paperqa-mcp" / "papers"
    
    if not papers_dir.exists():
        print(f"❌ Papers directory not found: {papers_dir}")
        sys.exit(1)
    
    print(f"🚀 Starting OCR processing for papers in: {papers_dir}")
    print(f"📚 This will process all PDFs and make them searchable")
    
    # Find all PDFs
    pdf_files = find_pdfs(papers_dir)
    
    if not pdf_files:
        print("❌ No PDF files found in papers directory")
        sys.exit(1)
    
    print(f"📄 Found {len(pdf_files)} PDF files:")
    for pdf in pdf_files:
        print(f"  - {pdf.name}")
    
    print("\n" + "="*50)
    
    success_count = 0
    
    for pdf_path in pdf_files:
        print(f"\n📝 Processing: {pdf_path.name}")
        
        # Create backup
        backup_path = backup_original(pdf_path)
        
        # Create temporary output path
        temp_output = pdf_path.with_suffix(".ocr_temp.pdf")
        
        # OCR the PDF
        if ocr_pdf(pdf_path, temp_output):
            # Replace original with OCR'd version
            shutil.move(temp_output, pdf_path)
            print(f"✅ Replaced {pdf_path.name} with OCR'd version")
            success_count += 1
        else:
            # Clean up temp file if it exists
            if temp_output.exists():
                temp_output.unlink()
            print(f"❌ Keeping original {pdf_path.name}")
    
    print("\n" + "="*50)
    print(f"🎉 OCR processing complete!")
    print(f"✅ Successfully processed: {success_count}/{len(pdf_files)} files")
    
    if success_count > 0:
        print(f"\n💡 Next steps:")
        print(f"1. Run: python build_index.py")
        print(f"2. Test search functionality with OCR'd content")
        print(f"\n📂 Original files backed up with .original.pdf extension")


if __name__ == "__main__":
    main()