#!/usr/bin/env python3
"""
Test script to verify PaperQA2 API behavior outside MCP context
Testing ask() vs agent_query() return types and stdout behavior
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add current directory to path for config import
sys.path.insert(0, str(Path(__file__).parent / "paperqa-mcp"))

from paperqa import ask, agent_query
from config import get_paperqa_settings

def setup_logging():
    """Setup basic logging to see what PaperQA outputs"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr
    )
    return logging.getLogger(__name__)

def test_ask_sync():
    """Test the synchronous ask() function"""
    logger = logging.getLogger(__name__)
    
    logger.info("🔍 Testing ask() function...")
    
    try:
        settings = get_paperqa_settings()
        
        logger.info(f"Settings configured with embedding: {settings.embedding}")
        
        result = ask(
            query="What is the main topic of the PDF in the papers directory?",
            settings=settings
        )
        
        logger.info(f"✅ ask() returned type: {type(result)}")
        logger.info(f"✅ ask() result attributes: {dir(result)}")
        
        # Test attribute access patterns
        if hasattr(result, 'answer'):
            logger.info(f"✅ Direct access - result.answer: {len(result.answer) if result.answer else 'None'} chars")
        
        if hasattr(result, 'session'):
            logger.info(f"✅ Session access - result.session: {type(result.session)}")
            if hasattr(result.session, 'answer'):
                logger.info(f"✅ Session answer - result.session.answer: {len(result.session.answer) if result.session.answer else 'None'} chars")
        
        if hasattr(result, 'cost'):
            logger.info(f"✅ Cost access - result.cost: ${result.cost}")
            
        if hasattr(result, 'contexts'):
            logger.info(f"✅ Contexts access - result.contexts: {len(result.contexts)} items")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ ask() failed: {type(e).__name__}: {e}")
        return None

async def test_agent_query_async():
    """Test the asynchronous agent_query() function"""
    logger = logging.getLogger(__name__)
    
    logger.info("🔍 Testing agent_query() function...")
    
    try:
        settings = get_paperqa_settings()
        
        result = await agent_query(
            query="What is the main topic of the PDF in the papers directory?",
            settings=settings
        )
        
        logger.info(f"✅ agent_query() returned type: {type(result)}")
        logger.info(f"✅ agent_query() result attributes: {dir(result)}")
        
        # Test attribute access patterns
        if hasattr(result, 'answer'):
            logger.info(f"✅ Direct access - result.answer: {len(result.answer) if result.answer else 'None'} chars")
        
        if hasattr(result, 'session'):
            logger.info(f"✅ Session access - result.session: {type(result.session)}")
            if hasattr(result.session, 'answer'):
                logger.info(f"✅ Session answer - result.session.answer: {len(result.session.answer) if result.session.answer else 'None'} chars")
        
        if hasattr(result, 'cost'):
            logger.info(f"✅ Cost access - result.cost: ${result.cost}")
            
        if hasattr(result, 'contexts'):
            logger.info(f"✅ Contexts access - result.contexts: {len(result.contexts)} items")
            
        return result
        
    except Exception as e:
        logger.error(f"❌ agent_query() failed: {type(e).__name__}: {e}")
        return None

async def main():
    """Main test function"""
    logger = setup_logging()
    
    logger.info("🚀 Starting PaperQA2 API behavior test")
    logger.info("📁 Expected papers directory: paperqa-mcp/papers/")
    
    # Check if papers directory exists
    papers_dir = Path("paperqa-mcp/papers")
    if not papers_dir.exists():
        logger.error(f"❌ Papers directory not found: {papers_dir.absolute()}")
        return
    
    pdf_files = list(papers_dir.glob("*.pdf"))
    logger.info(f"📚 Found {len(pdf_files)} PDF files: {[f.name for f in pdf_files]}")
    
    if not pdf_files:
        logger.warning("⚠️ No PDF files found - tests may not work properly")
    
    # Test 1: Synchronous ask()
    logger.info("\n" + "="*50)
    logger.info("TEST 1: Synchronous ask() function")
    logger.info("="*50)
    
    sync_result = test_ask_sync()
    
    # Test 2: Asynchronous agent_query()  
    logger.info("\n" + "="*50)
    logger.info("TEST 2: Asynchronous agent_query() function")
    logger.info("="*50)
    
    async_result = await test_agent_query_async()
    
    # Comparison
    logger.info("\n" + "="*50)
    logger.info("COMPARISON")
    logger.info("="*50)
    
    if sync_result and async_result:
        logger.info(f"✅ Both functions completed successfully")
        logger.info(f"Sync result type: {type(sync_result)}")
        logger.info(f"Async result type: {type(async_result)}")
        logger.info(f"Types match: {type(sync_result) == type(async_result)}")
    else:
        if not sync_result:
            logger.error("❌ Sync ask() failed")
        if not async_result:
            logger.error("❌ Async agent_query() failed")
    
    logger.info("🏁 Test completed")

if __name__ == "__main__":
    asyncio.run(main())