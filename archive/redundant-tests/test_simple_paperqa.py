#!/usr/bin/env python3
"""
Simple PaperQA test - Direct API usage (no MCP)
Goal: Verify PaperQA can answer questions about PDFs end-to-end
"""

import asyncio
import logging
from pathlib import Path

# Minimal logging
logging.basicConfig(level=logging.WARNING)

from paperqa import Settings
from paperqa.agents.main import agent_query
from paperqa.agents.search import get_directory_index
from config import get_paperqa_settings

async def simple_paperqa_test():
    """Test PaperQA with our PDFs - simple and direct"""
    
    print("=== Simple PaperQA Test ===")
    print("Goal: Get PaperQA to answer a question about our PDFs")
    
    # Step 1: Load settings (already working)
    print("\n1. Loading configuration...")
    settings = get_paperqa_settings()
    print(f"   ✅ Paper directory: {settings.agent.index.paper_directory}")
    print(f"   ✅ Embedding model: {settings.embedding}")
    print(f"   ✅ LLM model: {settings.llm}")
    
    # Step 2: Load existing index (we know this works)
    print("\n2. Loading document index...")
    built_index = await get_directory_index(settings=settings)
    index_files = await built_index.index_files
    
    success_count = sum(1 for status in index_files.values() if status != 'ERROR')
    print(f"   ✅ Successfully indexed: {success_count} documents")
    
    if success_count == 0:
        print("   ❌ No documents indexed - stopping test")
        return
    
    # Step 3: Ask a specific question about the content
    print("\n3. Testing content-specific question...")
    test_questions = [
        "What does Hito Steyerl write about truth and representation?",
        "What are the main concepts discussed in these papers?", 
        "What does the Powers of Ten paper discuss?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n--- Test Question {i} ---")
        print(f"Q: {question}")
        
        try:
            result = await agent_query(
                query=question,
                settings=settings
            )
            
            answer = result.session.answer
            cost = result.session.cost
            source_count = len(result.session.contexts)
            
            print(f"Sources found: {source_count}")
            print(f"Cost: ${cost:.4f}")
            print(f"Answer length: {len(answer)} characters")
            
            if source_count > 0:
                print(f"✅ SUCCESS - Found content!")
                print(f"Answer: {answer[:300]}...")
                
                # Show sources
                print(f"\nSources used:")
                for j, context in enumerate(result.session.contexts[:3], 1):
                    print(f"  {j}. {context.text.name} (score: {context.score:.2f})")
                
                return True  # Success - we got content!
                
            else:
                print(f"❌ No sources found for this question")
                print(f"Answer: {answer}")
        
        except Exception as e:
            print(f"❌ Error during query: {e}")
    
    print("\n❌ All test questions failed to find content")
    return False

if __name__ == "__main__":
    success = asyncio.run(simple_paperqa_test())
    
    if success:
        print("\n🎉 PaperQA is working correctly!")
        print("Next: Can proceed with MCP integration")
    else:
        print("\n⚠️  PaperQA needs more debugging")
        print("Core functionality not yet working")