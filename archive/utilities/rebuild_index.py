#!/usr/bin/env python3
"""
Force rebuild PaperQA2 index to fix ERROR status on all PDFs
"""

import asyncio
import logging
import shutil
from pathlib import Path

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from paperqa.agents.search import get_directory_index
from config import get_paperqa_settings

async def rebuild_index():
    """Force rebuild the PaperQA2 index"""
    
    print("=== Rebuilding PaperQA2 Index ===")
    
    # Get current settings
    settings = get_paperqa_settings()
    
    # Force rebuild by setting rebuild_index=True
    settings.agent.rebuild_index = True
    
    print(f"Paper directory: {settings.agent.index.paper_directory}")
    print(f"Index directory: {settings.agent.index.index_directory}")
    
    # Check papers
    papers_dir = Path(settings.agent.index.paper_directory)
    pdf_files = list(papers_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files to index")
    
    # Optional: Remove existing broken index
    index_dir = Path(settings.agent.index.index_directory)
    print(f"\nRemoving existing broken index directories...")
    for subdir in index_dir.iterdir():
        if subdir.is_dir() and subdir.name.startswith('pqa_index_'):
            print(f"  Removing {subdir.name}")
            shutil.rmtree(subdir)
    
    print(f"\nRebuilding index...")
    try:
        # This should rebuild the index from scratch
        built_index = await get_directory_index(settings=settings)
        
        # Check results
        index_name = settings.get_index_name()
        print(f"✅ New index created: {index_name}")
        
        index_files = await built_index.index_files
        print(f"Index files: {index_files}")
        
        # Count successful vs error files
        if isinstance(index_files, dict):
            success_count = sum(1 for status in index_files.values() if status != 'ERROR')
            error_count = sum(1 for status in index_files.values() if status == 'ERROR')
            print(f"✅ Successfully indexed: {success_count} files")
            print(f"❌ Failed to index: {error_count} files")
            
            if error_count > 0:
                print("\nFiles with errors:")
                for filename, status in index_files.items():
                    if status == 'ERROR':
                        print(f"  - {filename}: {status}")
        else:
            print(f"Index files result: {index_files}")
    
    except Exception as e:
        print(f"❌ Error rebuilding index: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(rebuild_index())