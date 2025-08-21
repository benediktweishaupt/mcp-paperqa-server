#!/usr/bin/env python3
"""
PaperQA2 MCP Server - Lean Implementation
Academic research MCP server providing direct PaperQA2 integration to Claude Desktop.

This is a minimal, fast implementation that directly exposes PaperQA2 functionality
through the MCP protocol without complex bridge architectures.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from mcp.types import Tool, TextContent

# PaperQA2 imports - using async API for proper integration
from paperqa import Settings, Docs
from paperqa.agents.main import agent_query  # Async API for proper FastMCP integration
from paperqa.settings import AgentSettings, IndexSettings
import paperqa

# Setup logging - Configure to prevent stdout pollution for MCP
# Redirect all logging to stderr to avoid breaking JSON-RPC protocol
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Redirect to stderr instead of stdout
)
logger = logging.getLogger(__name__)

# Silence noisy PaperQA loggers that might pollute stdout
logging.getLogger("paperqa").setLevel(logging.WARNING)
logging.getLogger("paperqa.agents").setLevel(logging.WARNING)
logging.getLogger("paperqa.agents.main").setLevel(logging.WARNING)
logging.getLogger("paperqa.agents.main.agent_callers").setLevel(logging.ERROR)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✅ Loaded environment variables from .env file")
except ImportError:
    logger.info("⚠️ python-dotenv not installed, using system environment variables only")

# Import configuration
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from config import get_paperqa_settings, get_supported_embedding_models, get_model_info

# Get optimized settings for academic research
settings = get_paperqa_settings()

# Directory references for logging
paper_directory = Path(__file__).parent / "papers"
cache_directory = Path(__file__).parent / "cache"

# Global state - simple and effective for MCP server
server = FastMCP("paperqa-academic")
docs = Docs()

logger.info(f"PaperQA2 MCP Server starting with Voyage AI embedding: {settings.embedding}")
logger.info("💡 Using voyage-3-large: 9.74% better than OpenAI + 2x cheaper + 32K context")
logger.info(f"Cache directory: {cache_directory}")


@server.tool()
async def search_literature(
    query: str,
    ctx: Context[ServerSession, None],
    max_sources: Optional[int] = 5,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None
) -> str:
    """
    Search academic literature using PaperQA2's agent workflow.
    
    Performs comprehensive academic research including paper search, evidence gathering,
    and synthesis with proper citations.
    
    Args:
        query: Research question or topic to investigate
        max_sources: Maximum number of evidence sources to use (1-15)
        min_year: Earliest publication year to include
        max_year: Latest publication year to include
        
    Returns:
        Comprehensive answer with citations and source attribution
    """
    try:
        logger.info(f"Literature search: {query[:100]}...")
        
        # Progress: Starting research
        await ctx.info(f"🔍 Starting literature search: {query[:60]}...")
        await ctx.report_progress(progress=0.1, total=1.0, message="Initializing research query")
        
        # Adjust settings based on parameters
        current_settings = settings
        if max_sources and 1 <= max_sources <= 15:
            current_settings.answer.evidence_k = max_sources
            
        await ctx.report_progress(progress=0.2, total=1.0, message="Configuration complete")
        
        # Progress: Searching papers
        await ctx.report_progress(progress=0.3, total=1.0, message="Searching academic papers...")
        
        # Use PaperQA2's async API for proper FastMCP integration
        await ctx.report_progress(progress=0.5, total=1.0, message="Analyzing evidence and generating answer...")
        
        result = await agent_query(
            query=query,
            settings=current_settings
        )
        
        # Progress: Formatting results
        await ctx.report_progress(progress=0.9, total=1.0, message="Formatting research results...")
        
        # Format comprehensive response - use correct session access pattern
        answer = result.session.answer
        cost = result.session.cost
        source_count = len(result.session.contexts)
        
        response = f"""# Literature Search Results

{answer}

---
**Research Summary**: {source_count} evidence sources analyzed | **Query Cost**: ${cost:.4f}
**Library Status**: Using pre-built index | **Embedding Model**: {settings.embedding}
"""
        
        # Progress: Complete
        await ctx.report_progress(progress=1.0, total=1.0, message="Research complete!")
        await ctx.info(f"✅ Search completed: {source_count} sources, ${cost:.4f} cost")
        
        logger.info(f"Search completed: {source_count} sources, ${cost:.4f} cost")
        return response
        
    except Exception as e:
        logger.error(f"Literature search failed: {e}")
        return f"❌ Literature search failed: {str(e)}\n\nPlease check your API keys and document library."


# Document indexing disabled - use build_index.py script instead
# MCP servers have timeout issues with large document processing
# 
# @server.tool()
# async def add_document(file_path: str, document_name: Optional[str] = None) -> str:
#     """DISABLED: Use build_index.py script for document indexing instead."""
#     return """❌ Document indexing via MCP is disabled
# 
# **Reason**: Large PDF processing causes MCP timeouts (>60 seconds)
# 
# **Solution**: Use the offline indexing script instead:
# 
# 1. Copy PDFs to: paperqa-mcp/papers/
# 2. Run: python build_index.py
# 3. Restart Claude Desktop
# 4. Use search_literature tool
# 
# **Benefits**: Faster, more reliable, no timeout issues
# """


@server.tool()
async def get_library_status() -> str:
    """
    Get current status of the research library.
    
    Returns comprehensive information about pre-built index, papers directory,
    configuration, and system status.
    
    Returns:
        Detailed library and system status
    """
    try:
        # Check paper directory and index
        paper_files = list(paper_directory.glob("*.pdf"))
        index_dir = Path(settings.agent.index.index_directory)
        index_files = list(index_dir.glob("*")) if index_dir.exists() else []
        
        # Calculate total storage
        total_size = sum(pf.stat().st_size for pf in paper_files)
        
        if not paper_files:
            return f"""📚 Research Library Status

**Status**: No papers found
**Paper Directory**: {paper_directory}
**Index Status**: {len(index_files)} files in index

**Setup Instructions**:
1. Copy PDFs to: {paper_directory}
2. Run: `python build_index.py`
3. Restart Claude Desktop
4. Use `search_literature` tool

**Configuration**:
- Embedding Model: {settings.embedding}
- LLM Model: {settings.llm}
- Index Directory: {index_dir}
"""

        # Status based on index availability
        if not index_files:
            status = "⚠️ Papers found but no index - run build_index.py"
        else:
            status = "✅ Ready for research"
        
        # Get paper names for display
        paper_names = [pf.stem for pf in paper_files[:5]]
        paper_summary = ", ".join(paper_names)
        if len(paper_files) > 5:
            paper_summary += f" and {len(paper_files) - 5} more..."
        
        response = f"""📚 Research Library Status

**Library Statistics**:
- Papers: {len(paper_files)} PDFs in directory
- Index Files: {len(index_files)} files
- Storage: {total_size / 1024 / 1024:.1f} MB
- Status: {status}

**Papers**: {paper_summary}

**Configuration**:
- Embedding Model: {settings.embedding}
- LLM Model: {settings.llm}
- Evidence Sources: {settings.answer.evidence_k} per query
- Paper Directory: {paper_directory}
- Index Directory: {index_dir}

**Available Commands**:
- `search_literature`: Research questions and topics
- `get_library_status`: Check system status
- `configure_embedding`: Switch embedding models

**Note**: Document indexing via MCP is disabled. Use `build_index.py` script instead.
"""
        
        return response
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return f"❌ Status check failed: {str(e)}"


@server.tool()
async def configure_embedding(
    model_name: str = "voyage-ai/voyage-3-lite"
) -> str:
    """
    Configure the embedding model used for semantic search.
    
    Supports the validated embedding models from our benchmarks.
    Note: Existing documents will need to be re-added to use the new embedding model.
    
    Args:
        model_name: Embedding model identifier
                   Options: 'voyage-ai/voyage-3-lite' (recommended), 
                           'gemini/gemini-embedding-001', 
                           'text-embedding-3-small'
    
    Returns:
        Configuration change confirmation
    """
    try:
        # Get supported models from config
        supported_models = get_supported_embedding_models()
        
        if model_name not in supported_models:
            return f"""❌ Unsupported embedding model: {model_name}

**Supported models**:
- `voyage/voyage-3-large` (NEW: state-of-the-art, 9.74% better than OpenAI)
- `voyage/voyage-3.5` (high performance alternative)
- `voyage/voyage-3-lite` (budget: 6x cheaper than OpenAI)
- `voyage/voyage-3` (balanced performance/cost)
- `gemini/text-embedding-004` (free Google option)
- `text-embedding-3-large` (OpenAI baseline)

**Recommendation**: Voyage models excel at academic content with 32K context support."""

        old_model = settings.embedding
        settings.embedding = model_name
        
        logger.info(f"Embedding model changed: {old_model} → {model_name}")
        
        response = f"""✅ Embedding model updated

**Previous**: {old_model}
**Current**: {model_name}

**Performance Notes**:
{chr(10).join(f"- {model}: {get_model_info(model)}" for model in supported_models[:4])}
- All Voyage models: 32K context (vs OpenAI's 8K)

⚠️ **Important**: Re-add documents to use new embedding model for optimal search quality.

**Recommendation**: Test search quality with new model before production use."""
        
        return response
        
    except Exception as e:
        logger.error(f"Embedding configuration failed: {e}")
        return f"❌ Configuration failed: {str(e)}"


async def load_existing_papers():
    """Use PaperQA2's built-in index management - no custom code needed"""
    
    try:
        pdf_files = list(paper_directory.glob("*.pdf"))
        if not pdf_files:
            logger.info("No existing papers found in papers directory")
            return
        
        logger.info(f"📚 Found {len(pdf_files)} papers in directory")
        logger.info(f"🚀 PaperQA2 will handle indexing automatically through IndexSettings")
        logger.info(f"✅ Index directory: {settings.agent.index.index_directory}")
        logger.info(f"💰 Cost savings: PaperQA2 reuses existing embeddings automatically")
        
    except Exception as e:
        logger.error(f"Error checking papers directory: {e}")


async def main():
    """Main entry point for the PaperQA2 MCP server"""
    logger.info(f"Starting PaperQA2 MCP Server v{paperqa.__version__}")
    logger.info(f"Embedding model: {settings.embedding}")
    logger.info(f"Paper directory: {paper_directory}")
    
    # Load existing papers on startup
    await load_existing_papers()
    
    logger.info("PaperQA2 MCP Server ready - connecting to Claude Desktop...")
    
    # Run the FastMCP server
    await server.run()


if __name__ == "__main__":
    try:
        # FastMCP server.run() handles its own async event loop
        # No need for asyncio.run() wrapper - this causes conflicts
        
        logger.info(f"Starting PaperQA2 MCP Server v{paperqa.__version__}")
        logger.info(f"Embedding model: {settings.embedding}")
        logger.info(f"Paper directory: {paper_directory}")
        
        # Run startup synchronously first
        import anyio
        anyio.run(load_existing_papers)
        
        logger.info("PaperQA2 MCP Server ready - connecting to Claude Desktop...")
        
        # Run FastMCP server directly - it manages its own async loop
        server.run()
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise