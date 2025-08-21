#!/usr/bin/env python3
"""
Debug script to test PaperQA2 API step by step
Following the exact pattern from Context7 documentation snippet #35
"""

import asyncio
import logging
import os
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from paperqa import Settings
from paperqa.agents.main import agent_query
from paperqa.agents.search import get_directory_index
from config import get_paperqa_settings

async def debug_paperqa():
    """Debug PaperQA2 step by step"""
    
    print("=== PaperQA2 Debug Test ===")
    
    # Step 1: Check what papers exist
    papers_dir = Path(__file__).parent / "papers"
    print(f"\n1. Papers directory: {papers_dir}")
    pdf_files = list(papers_dir.glob("*.pdf"))
    print(f"   Found {len(pdf_files)} PDF files:")
    for pdf in pdf_files[:5]:  # Show first 5
        print(f"   - {pdf.name} ({pdf.stat().st_size / 1024:.1f} KB)")
    
    # Step 2: Check existing indices
    cache_dir = Path(__file__).parent / "cache" / "index"
    print(f"\n2. Cache directory: {cache_dir}")
    index_dirs = [d for d in cache_dir.iterdir() if d.is_dir()]
    print(f"   Found {len(index_dirs)} index directories:")
    for idx_dir in index_dirs:
        print(f"   - {idx_dir.name}")
    
    # Step 3: Get settings and show configuration
    print(f"\n3. Settings configuration:")
    settings = get_paperqa_settings()
    print(f"   Paper directory: {settings.agent.index.paper_directory}")
    print(f"   Index directory: {settings.agent.index.index_directory}")
    print(f"   Embedding model: {settings.embedding}")
    print(f"   LLM model: {settings.llm}")
    
    # Step 4: Try to load/build index following exact docs pattern
    print(f"\n4. Loading/building index...")
    try:
        built_index = await get_directory_index(settings=settings)
        
        # This should now show the auto-generated index name
        index_name = settings.get_index_name()
        print(f"   Index name: {index_name}")
        
        # This should show the actual index files
        index_files = await built_index.index_files
        print(f"   Index files: {index_files}")
        print(f"   Index files type: {type(index_files)}")
        
        # Try to show some files if it's iterable
        try:
            if hasattr(index_files, '__len__'):
                print(f"   Number of index files: {len(index_files)}")
        except:
            print("   Cannot determine number of index files")
            
    except Exception as e:
        print(f"   ERROR loading index: {e}")
        return
    
    # Step 5: Test simple query
    print(f"\n5. Testing simple query...")
    try:
        result = await agent_query(
            query="What is mentioned in these documents?",
            settings=settings
        )
        
        # Check results
        answer = result.session.answer
        cost = result.session.cost
        source_count = len(result.session.contexts)
        
        print(f"   Answer length: {len(answer)} chars")
        print(f"   Sources found: {source_count}")
        print(f"   Query cost: ${cost:.4f}")
        print(f"   Answer preview: {answer[:200]}...")
        
        if source_count == 0:
            print("   ❌ NO SOURCES FOUND - This is the problem!")
        else:
            print("   ✅ Sources found successfully!")
            
    except Exception as e:
        print(f"   ERROR during query: {e}")
        return

if __name__ == "__main__":
    asyncio.run(debug_paperqa())