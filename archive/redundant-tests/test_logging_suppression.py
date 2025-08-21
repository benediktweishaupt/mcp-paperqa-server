#!/usr/bin/env python3
"""
Test script to verify logging suppression effectiveness
Testing different approaches to suppress PaperQA2 stdout output
"""

import asyncio
import sys
import logging
import os
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO

# Add current directory to path for config import
sys.path.insert(0, str(Path(__file__).parent / "paperqa-mcp"))

from paperqa import agent_query
from config import get_paperqa_settings

def setup_test_logging():
    """Setup logging to capture what gets through"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='[TEST LOG] %(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr
    )
    return logging.getLogger(__name__)

async def test_no_suppression():
    """Baseline test - no suppression"""
    logger = logging.getLogger(__name__)
    logger.info("🔍 TEST 1: No suppression (baseline)")
    
    stdout_capture = StringIO()
    
    with redirect_stdout(stdout_capture):
        try:
            settings = get_paperqa_settings()
            result = await agent_query(
                query="What is this PDF about?",
                settings=settings
            )
            logger.info(f"✅ Query completed: {type(result)}")
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
    
    captured = stdout_capture.getvalue()
    logger.info(f"📊 Stdout captured: {len(captured)} chars")
    if captured:
        logger.info(f"📝 Sample output: {captured[:200]}...")
    
    return len(captured)

async def test_basic_suppression():
    """Test basic logging level suppression"""
    logger = logging.getLogger(__name__)
    logger.info("🔍 TEST 2: Basic logging suppression")
    
    # Save original levels
    original_levels = {}
    paperqa_loggers = [
        'paperqa',
        'paperqa.agents',
        'paperqa.agents.tools',
        'paperqa.agents.main',
        'paperqa.agents.main.agent_callers'
    ]
    
    # Suppress paperqa loggers
    for logger_name in paperqa_loggers:
        paperqa_logger = logging.getLogger(logger_name)
        original_levels[logger_name] = paperqa_logger.level
        paperqa_logger.setLevel(logging.CRITICAL)
    
    stdout_capture = StringIO()
    
    with redirect_stdout(stdout_capture):
        try:
            settings = get_paperqa_settings()
            result = await agent_query(
                query="What is this PDF about?",
                settings=settings
            )
            logger.info(f"✅ Query completed: {type(result)}")
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
    
    # Restore original levels
    for logger_name, level in original_levels.items():
        logging.getLogger(logger_name).setLevel(level)
    
    captured = stdout_capture.getvalue()
    logger.info(f"📊 Stdout captured: {len(captured)} chars")
    if captured:
        logger.info(f"📝 Sample output: {captured[:200]}...")
    
    return len(captured)

async def test_nuclear_suppression():
    """Test nuclear option - complete stdout/stderr redirection"""
    logger = logging.getLogger(__name__)
    logger.info("🔍 TEST 3: Nuclear suppression")
    
    stdout_capture = StringIO()
    stderr_capture = StringIO()
    
    # Complete redirection
    with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
        # Also suppress all paperqa loggers
        for logger_name in logging.root.manager.loggerDict:
            if 'paperqa' in logger_name:
                paperqa_logger = logging.getLogger(logger_name)
                paperqa_logger.handlers.clear()
                paperqa_logger.setLevel(logging.CRITICAL)
        
        try:
            settings = get_paperqa_settings()
            result = await agent_query(
                query="What is this PDF about?",
                settings=settings
            )
            logger.info(f"✅ Query completed: {type(result)}")
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
    
    captured_stdout = stdout_capture.getvalue()
    captured_stderr = stderr_capture.getvalue()
    
    logger.info(f"📊 Stdout captured: {len(captured_stdout)} chars")
    logger.info(f"📊 Stderr captured: {len(captured_stderr)} chars")
    
    if captured_stdout:
        logger.info(f"📝 Stdout sample: {captured_stdout[:200]}...")
    if captured_stderr:
        logger.info(f"📝 Stderr sample: {captured_stderr[:200]}...")
    
    return len(captured_stdout), len(captured_stderr)

async def test_devnull_suppression():
    """Test /dev/null redirection approach"""
    logger = logging.getLogger(__name__)
    logger.info("🔍 TEST 4: /dev/null redirection")
    
    stdout_capture = StringIO()
    
    with redirect_stdout(stdout_capture):
        with open(os.devnull, 'w') as devnull:
            # Redirect sys.stdout and sys.stderr during execution
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            
            sys.stdout = devnull
            sys.stderr = devnull
            
            try:
                settings = get_paperqa_settings()
                result = await agent_query(
                    query="What is this PDF about?",
                    settings=settings
                )
                logger.info(f"✅ Query completed: {type(result)}")
            except Exception as e:
                logger.error(f"❌ Query failed: {e}")
            finally:
                # Always restore
                sys.stdout = original_stdout
                sys.stderr = original_stderr
    
    captured = stdout_capture.getvalue()
    logger.info(f"📊 Stdout captured: {len(captured)} chars")
    if captured:
        logger.info(f"📝 Sample output: {captured[:200]}...")
    
    return len(captured)

async def main():
    """Main test function"""
    logger = setup_test_logging()
    
    logger.info("🚀 Starting PaperQA2 logging suppression tests")
    
    # Check papers directory
    papers_dir = Path("paperqa-mcp/papers")
    pdf_files = list(papers_dir.glob("*.pdf"))
    logger.info(f"📚 Found {len(pdf_files)} PDF files")
    
    results = {}
    
    try:
        # Test 1: No suppression
        results['no_suppression'] = await test_no_suppression()
        
        logger.info("\n" + "="*50)
        
        # Test 2: Basic suppression
        results['basic_suppression'] = await test_basic_suppression()
        
        logger.info("\n" + "="*50)
        
        # Test 3: Nuclear suppression
        nuclear_result = await test_nuclear_suppression()
        results['nuclear_stdout'], results['nuclear_stderr'] = nuclear_result
        
        logger.info("\n" + "="*50)
        
        # Test 4: /dev/null suppression
        results['devnull_suppression'] = await test_devnull_suppression()
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        return
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("SUPPRESSION EFFECTIVENESS SUMMARY")
    logger.info("="*50)
    
    baseline = results.get('no_suppression', 0)
    
    for test_name, chars in results.items():
        if test_name == 'nuclear_stdout':
            continue  # Skip, handled separately
        if test_name == 'nuclear_stderr':
            stdout_chars = results.get('nuclear_stdout', 0)
            logger.info(f"{test_name:20}: {chars:6} stderr chars, {stdout_chars:6} stdout chars")
            if baseline > 0:
                reduction = ((baseline - stdout_chars) / baseline) * 100
                logger.info(f"{'':20}  {reduction:6.1f}% stdout reduction")
        elif isinstance(chars, int):
            logger.info(f"{test_name:20}: {chars:6} chars")
            if baseline > 0 and test_name != 'no_suppression':
                reduction = ((baseline - chars) / baseline) * 100
                logger.info(f"{'':20}  {reduction:6.1f}% reduction")
    
    # Best approach recommendation
    min_output = min([v for k, v in results.items() if isinstance(v, int) and k != 'no_suppression'])
    best_approach = [k for k, v in results.items() if v == min_output][0]
    
    logger.info(f"\n🏆 Most effective approach: {best_approach}")
    logger.info("🏁 Test completed")

if __name__ == "__main__":
    asyncio.run(main())