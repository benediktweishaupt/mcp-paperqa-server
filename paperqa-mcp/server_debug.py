#!/usr/bin/env python3
"""
Debug MCP Server - Test different FastMCP patterns
"""

import logging
import sys
from typing import Optional
from mcp.server.fastmcp import FastMCP

# Verbose logging to see what's happening
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

server = FastMCP("paperqa-debug")

@server.tool()
async def search_literature(query: str, max_sources: Optional[int] = 5) -> str:
    """Debug version with proper typing and error handling"""
    logger.info(f"Function called with: query='{query}', max_sources={max_sources}")
    
    try:
        # Simple string operations only
        result = f"Debug response: Query was '{query}' with {max_sources} max sources"
        logger.info(f"Returning: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Exception in function: {e}", exc_info=True)
        return f"Function error: {str(e)}"

@server.tool()
async def simple_test() -> str:
    """Even simpler test with no parameters"""
    logger.info("Simple test called")
    return "Simple test response"

if __name__ == "__main__":
    try:
        logger.info("Starting debug MCP server...")
        logger.info("Server initialized, calling run()...")
        server.run()
    except Exception as e:
        logger.error(f"Server startup error: {e}", exc_info=True)
        raise