#!/usr/bin/env python3
"""
Simple test to validate the core fix: agent_query vs ask
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path for config import
sys.path.insert(0, str(Path(__file__).parent / "paperqa-mcp"))

from paperqa import agent_query
from config import get_paperqa_settings

async def test_agent_query_access_patterns():
    """Test proper access patterns for agent_query result"""
    print("🔍 Testing agent_query() access patterns...")
    
    try:
        settings = get_paperqa_settings()
        
        result = await agent_query(
            query="What is this about?",
            settings=settings
        )
        
        print(f"✅ Result type: {type(result)}")
        
        # Test our original wrong access pattern
        try:
            answer_wrong = result.answer  # This was our fix attempt
            print("❌ ERROR: result.answer should not work if session is needed")
        except AttributeError as e:
            print(f"✅ CONFIRMED: result.answer doesn't exist: {e}")
        
        # Test session access pattern from docs
        try:
            answer_session = result.session.answer
            cost_session = result.session.cost
            contexts_session = result.session.contexts
            
            print(f"✅ CORRECT: result.session.answer works: {len(answer_session)} chars")
            print(f"✅ CORRECT: result.session.cost works: ${cost_session}")
            print(f"✅ CORRECT: result.session.contexts works: {len(contexts_session)} items")
            
            return True
            
        except AttributeError as e:
            print(f"❌ Session access failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ agent_query failed: {e}")
        return False

async def main():
    print("🚀 Simple fix validation test")
    
    # Check papers directory
    papers_dir = Path("paperqa-mcp/papers")
    pdf_files = list(papers_dir.glob("*.pdf"))
    print(f"📚 Found {len(pdf_files)} PDF files")
    
    success = await test_agent_query_access_patterns()
    
    if success:
        print("\n✅ VALIDATION PASSED")
        print("   - agent_query() returns AnswerResponse")
        print("   - Access pattern: result.session.answer")
        print("   - Ready for MCP server implementation")
    else:
        print("\n❌ VALIDATION FAILED")
        print("   - Need to investigate further")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())