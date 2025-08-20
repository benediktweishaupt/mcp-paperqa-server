#!/usr/bin/env python3
"""
PaperQA2 MCP Server - Lean Implementation
Academic research MCP server providing direct PaperQA2 integration to Claude Desktop.

This is a minimal, fast implementation that directly exposes PaperQA2 functionality
through the MCP protocol without complex bridge architectures.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from mcp.server.fastmcp import FastMCP
from mcp.types import Tool, TextContent

# PaperQA2 imports - using our validated PyPI package
from paperqa import agent_query, Settings, Docs
from paperqa.settings import AgentSettings, IndexSettings
import paperqa

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import configuration
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
        
        # Adjust settings based on parameters
        current_settings = settings
        if max_sources and 1 <= max_sources <= 15:
            current_settings.answer.evidence_k = max_sources
        
        # Use PaperQA2's agent_query for full research workflow
        result = await agent_query(
            query=query,
            settings=current_settings,
            docs=docs
        )
        
        # Format comprehensive response
        answer = result.session.answer
        cost = result.session.cost
        source_count = len(result.session.contexts)
        
        response = f"""# Literature Search Results

{answer}

---
**Research Summary**: {source_count} evidence sources analyzed | **Query Cost**: ${cost:.4f}
**Library Status**: {len(docs.docs)} documents indexed | **Embedding Model**: {settings.embedding}
"""
        
        logger.info(f"Search completed: {source_count} sources, ${cost:.4f} cost")
        return response
        
    except Exception as e:
        logger.error(f"Literature search failed: {e}")
        return f"❌ Literature search failed: {str(e)}\n\nPlease check your API keys and document library."


@server.tool()
async def add_document(
    file_path: str,
    document_name: Optional[str] = None
) -> str:
    """
    Add a PDF document to the research library.
    
    The document will be processed, embedded, and made available for literature searches.
    Supports academic PDFs from major publishers.
    
    Args:
        file_path: Path to the PDF file to add
        document_name: Optional custom name for the document
        
    Returns:
        Status message with library information
    """
    try:
        file_path_obj = Path(file_path)
        
        # Validation
        if not file_path_obj.exists():
            return f"❌ Error: File not found at {file_path}"
        
        if not file_path_obj.suffix.lower() == '.pdf':
            return f"❌ Error: Only PDF files supported, got {file_path_obj.suffix}"
        
        # Use provided name or extract from filename
        doc_name = document_name or file_path_obj.stem
        
        logger.info(f"Adding document: {doc_name}")
        
        # Add to PaperQA2 docs collection
        with open(file_path_obj, 'rb') as f:
            await docs.aadd_file(
                file=f,
                docname=doc_name,
                settings=settings
            )
        
        # Copy to our papers directory for persistence
        import shutil
        dest_path = paper_directory / file_path_obj.name
        if not dest_path.exists():
            shutil.copy2(file_path_obj, dest_path)
        
        # PaperQA2 handles all persistence automatically through IndexSettings
        logger.info(f"✅ Document added - PaperQA2 handles persistence automatically")
        
        doc_count = len(docs.docs)
        text_count = len(docs.texts)
        
        response = f"""✅ Successfully added document to library

**Document**: {doc_name}
**File**: {file_path}
**Size**: {file_path_obj.stat().st_size:,} bytes

**Library Status**: {doc_count} documents, {text_count} searchable segments
**Ready for**: Literature search and citation queries
"""
        
        logger.info(f"Document added: {doc_name} (total: {doc_count} docs)")
        return response
        
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        return f"❌ Upload failed: {str(e)}"


@server.tool()
async def get_library_status() -> str:
    """
    Get current status of the research library.
    
    Returns comprehensive information about indexed documents, 
    configuration, and system status.
    
    Returns:
        Detailed library and system status
    """
    try:
        doc_count = len(docs.docs)
        text_count = len(docs.texts)
        
        if doc_count == 0:
            return """📚 Research Library Status

**Status**: Empty library
**Documents**: 0 indexed
**Recommendation**: Use `add_document` to upload PDF papers for research

**Configuration**:
- Embedding Model: {settings.embedding}
- LLM Model: {settings.llm}  
- Paper Directory: {paper_directory}

**Ready to**: Accept documents and begin research"""

        # Get document details
        doc_names = []
        total_size = 0
        
        for doc in docs.docs.values():
            doc_names.append(doc.docname)
        
        # Check paper directory
        paper_files = list(paper_directory.glob("*.pdf"))
        for pf in paper_files:
            total_size += pf.stat().st_size
        
        doc_summary = ", ".join(doc_names[:5])
        if doc_count > 5:
            doc_summary += f" and {doc_count - 5} more..."
        
        response = f"""📚 Research Library Status

**Library Statistics**:
- Documents: {doc_count} indexed  
- Text Segments: {text_count:,} searchable chunks
- Storage: {total_size / 1024 / 1024:.1f} MB in paper directory
- Status: ✅ Ready for research

**Documents**: {doc_summary}

**Configuration**:
- Embedding Model: {settings.embedding}  
- LLM Model: {settings.llm}
- Evidence Sources: {settings.answer.evidence_k} per query
- Paper Directory: {paper_directory}

**Available Commands**:
- `search_literature`: Research questions and topics
- `add_document`: Upload new PDF papers
- `configure_embedding`: Switch embedding models
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
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise