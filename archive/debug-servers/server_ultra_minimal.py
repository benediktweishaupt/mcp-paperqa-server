#!/usr/bin/env python3
"""
Ultra Minimal MCP Server - Test without agent_query
Just return hardcoded response to test MCP wrapper itself
"""

import logging
import sys
from mcp.server.fastmcp import FastMCP

# Minimal logging
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
logger = logging.getLogger(__name__)

server = FastMCP("paperqa-ultra-minimal")

@server.tool()
async def search_literature(query: str, max_sources: int = 5) -> str:
    """Ultra minimal test - no PaperQA calls at all"""
    try:
        logger.info(f"Ultra minimal test: {query[:20]}...")
        
        # Just return a test response - no PaperQA involved
        return f"Test response for: {query[:50]}... (max_sources: {max_sources})"
        
    except Exception as e:
        logger.error(f"Ultra minimal failed: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    try:
        logger.info("Starting ultra minimal MCP server...")
        server.run()
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise