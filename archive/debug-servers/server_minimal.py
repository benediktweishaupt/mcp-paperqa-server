#!/usr/bin/env python3
"""
Minimal PaperQA2 MCP Server - Debug Version
Stripped down to bare minimum to isolate TaskGroup async errors.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

# PaperQA2 imports - only what we need
from paperqa.agents.main import agent_query
from paperqa.agents.search import get_directory_index

# Minimal logging to stderr only
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Silence PaperQA loggers
logging.getLogger("paperqa").setLevel(logging.WARNING)
logging.getLogger("paperqa.agents").setLevel(logging.WARNING)

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import config
sys.path.insert(0, os.path.dirname(__file__))
from config import get_paperqa_settings

# Get settings - single instance
settings = get_paperqa_settings()
server = FastMCP("paperqa-minimal")

logger.info("Minimal PaperQA MCP Server starting...")

@server.tool()
async def search_literature(query: str, max_sources: Optional[int] = 5) -> str:
    """
    Minimal literature search - no progress reporting, no Context usage
    Just query -> answer
    """
    try:
        logger.info(f"Minimal search: {query[:50]}...")
        
        # Simple settings copy
        current_settings = settings.model_copy(deep=True)
        if max_sources and 1 <= max_sources <= 15:
            current_settings.answer.evidence_k = max_sources
        
        # Load index - this works fine in direct API
        built_index = await get_directory_index(settings=current_settings)
        
        # Make query - this works fine in direct API  
        result = await agent_query(
            query=query,
            settings=current_settings
        )
        
        # Simple response - no formatting complexity
        answer = result.session.answer
        cost = result.session.cost
        source_count = len(result.session.contexts)
        
        # Basic response
        return f"Answer: {answer}\n\nSources: {source_count}, Cost: ${cost:.4f}"
        
    except Exception as e:
        logger.error(f"Minimal search failed: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    try:
        logger.info("Starting minimal MCP server...")
        server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise