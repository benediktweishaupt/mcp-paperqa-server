#!/usr/bin/env python3
"""
Clean test script for logging suppression effectiveness
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

async def test_suppression_approaches():
    """Test different suppression approaches with clean output"""
    print("🚀 Testing PaperQA2 logging suppression approaches")
    
    settings = get_paperqa_settings()
    query = "What is this PDF about?"
    
    results = {}
    
    # Test 1: No suppression
    print("\n📊 Test 1: Baseline (no suppression)")
    stdout_capture = StringIO()
    
    with redirect_stdout(stdout_capture):
        try:
            await agent_query(query=query, settings=settings)
            results['baseline'] = len(stdout_capture.getvalue())
            print(f"   Stdout captured: {results['baseline']} chars")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results['baseline'] = 0
    
    # Test 2: Basic logger suppression
    print("\n📊 Test 2: Basic logger suppression")
    
    # Suppress paperqa loggers
    paperqa_loggers = ['paperqa', 'paperqa.agents', 'paperqa.agents.tools', 'paperqa.agents.main']
    original_levels = {}
    
    for logger_name in paperqa_loggers:
        logger = logging.getLogger(logger_name)
        original_levels[logger_name] = logger.level
        logger.setLevel(logging.CRITICAL)
        logger.handlers.clear()
    
    stdout_capture = StringIO()
    
    with redirect_stdout(stdout_capture):
        try:
            await agent_query(query=query, settings=settings)
            results['basic'] = len(stdout_capture.getvalue())
            print(f"   Stdout captured: {results['basic']} chars")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results['basic'] = 0
    
    # Restore loggers
    for logger_name, level in original_levels.items():
        logging.getLogger(logger_name).setLevel(level)
    
    # Test 3: Nuclear suppression  
    print("\n📊 Test 3: Nuclear suppression (devnull)")
    
    with open(os.devnull, 'w') as devnull:
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        # Complete redirection
        sys.stdout = devnull
        sys.stderr = devnull
        
        # Also suppress all paperqa loggers
        for logger_name in logging.root.manager.loggerDict:
            if 'paperqa' in logger_name:
                logger = logging.getLogger(logger_name)
                logger.handlers.clear()
                logger.setLevel(logging.CRITICAL)
        
        stdout_capture = StringIO()
        
        with redirect_stdout(stdout_capture):
            try:
                await agent_query(query=query, settings=settings)
                results['nuclear'] = len(stdout_capture.getvalue())
            except Exception as e:
                results['nuclear'] = 0
            finally:
                sys.stdout = original_stdout
                sys.stderr = original_stderr
    
    print(f"   Stdout captured: {results['nuclear']} chars")
    
    # Summary
    print("\n🎯 SUPPRESSION EFFECTIVENESS SUMMARY")
    print("="*50)
    
    baseline = results.get('baseline', 0)
    
    for test_name, chars in results.items():
        print(f"{test_name:15}: {chars:6} chars", end="")
        
        if baseline > 0 and test_name != 'baseline':
            reduction = ((baseline - chars) / baseline) * 100
            print(f" ({reduction:5.1f}% reduction)")
        else:
            print()
    
    # Find most effective
    non_baseline = {k: v for k, v in results.items() if k != 'baseline'}
    if non_baseline:
        best_approach = min(non_baseline, key=non_baseline.get)
        print(f"\n🏆 Most effective: {best_approach}")
        
        # Test if any approach achieves 100% suppression
        if results[best_approach] == 0:
            print("✅ Perfect suppression achieved!")
            return True
        else:
            print("⚠️  Some output still leaking to stdout")
            return False
    
    return False

if __name__ == "__main__":
    success = asyncio.run(test_suppression_approaches())