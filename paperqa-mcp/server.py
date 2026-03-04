#!/usr/bin/env python3
"""
PaperQA2 MCP Server — search your research library from Claude.
"""

import asyncio
import logging
import os
import sys
import uuid
import shutil
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession

from paperqa import Settings, Docs
from paperqa.agents.main import agent_query
from paperqa.agents.search import get_directory_index
import paperqa

# Logging → stderr to avoid breaking JSON-RPC
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)
logging.getLogger("paperqa").setLevel(logging.WARNING)

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import config
sys.path.insert(0, os.path.dirname(__file__))
from config import get_paperqa_settings

settings = get_paperqa_settings()
paper_directory = Path(__file__).parent / "papers"
cache_directory = Path(__file__).parent / "cache"

# MCP server
server = FastMCP("paperqa-academic")

# Session tracking
_session_total_cost: float = 0.0
_session_query_count: int = 0

# Background indexing jobs
_indexing_jobs: dict[str, dict] = {}


@server.tool()
async def search_literature(
    query: str,
    ctx: Context[ServerSession, None],
    mode: str = "thorough",
    max_sources: Optional[int] = None,
) -> str:
    """
    Search your research library with synthesis.

    Args:
        query: Research question or topic
        mode: "fast" (3 sources, cheaper) or "thorough" (15 sources, full synthesis)
        max_sources: Override number of evidence sources (1-15)
    """
    global _session_total_cost, _session_query_count

    try:
        await ctx.info(f"Searching: {query[:60]}...")
        await ctx.report_progress(progress=0.1, total=1.0)

        current_settings = settings.model_copy(deep=True)

        # Apply mode
        if mode == "fast":
            current_settings.answer.evidence_k = max_sources or 3
            current_settings.answer.answer_max_sources = 3
        else:
            current_settings.answer.evidence_k = max_sources or 15
            current_settings.answer.answer_max_sources = 10

        await ctx.report_progress(progress=0.3, total=1.0)
        await get_directory_index(settings=current_settings)

        await ctx.report_progress(progress=0.5, total=1.0)
        result = await agent_query(query=query, settings=current_settings)

        answer = result.session.answer
        cost = result.session.cost
        source_count = len(result.session.contexts)

        _session_total_cost += cost
        _session_query_count += 1

        # Session transparency
        details = ""
        if hasattr(result.session, "tool_history") and result.session.tool_history:
            steps = result.session.tool_history
            details += "\n**Agent steps**:\n" + "\n".join(
                f"  {i}. {step}" for i, step in enumerate(steps, 1)
            )
        if hasattr(result.session, "token_counts") and result.session.token_counts:
            details += f"\n**Tokens**: {result.session.token_counts}"

        await ctx.report_progress(progress=1.0, total=1.0)

        return f"""# Literature Search Results

{answer}

---
**Sources**: {source_count} | **Cost**: ${cost:.4f} | **Mode**: {mode}
**Session**: ${_session_total_cost:.4f} across {_session_query_count} queries{details}
"""

    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"Search failed: {e}"


@server.tool()
async def get_contexts(
    query: str,
    ctx: Context[ServerSession, None],
    max_sources: int = 10,
) -> str:
    """
    Get raw text chunks matching a query. Uses the search index directly for
    low-cost retrieval without full agent synthesis.

    Args:
        query: Search query
        max_sources: Number of text chunks to return (1-20)
    """
    global _session_total_cost, _session_query_count

    try:
        await ctx.info(f"Retrieving contexts: {query[:60]}...")

        current_settings = settings.model_copy(deep=True)
        # Minimal agent run — just search + evidence, skip full synthesis
        current_settings.answer.evidence_k = min(max_sources, 20)
        current_settings.answer.answer_max_sources = min(max_sources, 20)
        current_settings.answer.evidence_skip_summary = True

        await get_directory_index(settings=current_settings)
        result = await agent_query(query=query, settings=current_settings)

        contexts = result.session.contexts
        cost = result.session.cost

        _session_total_cost += cost
        _session_query_count += 1

        if not contexts:
            return f'No contexts found for: "{query}"'

        formatted = []
        for i, context in enumerate(contexts[:max_sources], 1):
            text_name = context.text.name
            doc_info = context.text.doc
            citation = getattr(doc_info, "formatted_citation", doc_info.docname)

            formatted.append(
                f"## Context {i}\n\n"
                f"**Source**: {text_name}\n"
                f"**Citation**: {citation}\n"
                f"**Score**: {context.score}\n\n"
                f"{context.context}\n\n---"
            )

        return f"""# Raw Context Search Results

Query: "{query}"

{chr(10).join(formatted)}

**Contexts**: {len(contexts)} chunks | **Cost**: ${cost:.4f}
"""

    except Exception as e:
        logger.error(f"Context search failed: {e}")
        return f"Context search failed: {e}"


@server.tool()
async def get_library_status() -> str:
    """Check what's in your research library and system status."""
    try:
        paper_files = list(paper_directory.glob("*.pdf"))
        paper_files += list(paper_directory.glob("*.txt"))
        paper_files += list(paper_directory.glob("*.html"))
        paper_files += list(paper_directory.glob("*.docx"))

        index_dir = Path(settings.agent.index.index_directory)
        index_files = list(index_dir.glob("**/*")) if index_dir.exists() else []

        total_size = sum(f.stat().st_size for f in paper_files if f.is_file())

        if not paper_files:
            return f"""Library Status

No documents found in {paper_directory}

Setup:
1. Copy PDFs to: {paper_directory}
2. Run: python paperqa-mcp/build_index.py
3. Restart Claude Desktop

Config: {settings.embedding} | {settings.llm}
"""

        has_index = bool(index_files)
        status = "Ready" if has_index else "Documents found but no index — run build_index.py"

        names = [f.stem for f in paper_files[:10]]
        paper_list = "\n".join(f"  - {n}" for n in names)
        if len(paper_files) > 10:
            paper_list += f"\n  ... and {len(paper_files) - 10} more"

        # Show indexing jobs if any
        jobs_str = ""
        if _indexing_jobs:
            jobs_str = "\n\nIndexing Jobs:\n" + "\n".join(
                f"  [{info['status']}] {info['filename']}"
                for info in _indexing_jobs.values()
            )

        return f"""Library Status: {status}

Documents: {len(paper_files)} ({total_size / 1024 / 1024:.1f} MB)
{paper_list}

Config:
  Embedding: {settings.embedding}
  LLM: {settings.llm}
  Chunk size: {settings.parsing.reader_config.get('chunk_chars', 'default')}
  MMR lambda: {settings.texts_index_mmr_lambda}
  Index: {index_dir}

Tools:
  search_literature — synthesized answers (mode: fast/thorough)
  get_contexts — raw text chunks, near-zero cost
  add_document — add a book/document
  remove_document — remove a document
  get_library_status — this view

Session: ${_session_total_cost:.4f} across {_session_query_count} queries{jobs_str}
"""

    except Exception as e:
        return f"Status check failed: {e}"


@server.tool()
async def add_document(
    file_path: str,
    ctx: Context[ServerSession, None],
) -> str:
    """
    Add a document to the library. Copies file and starts background indexing.

    Args:
        file_path: Absolute path to the file (PDF, TXT, HTML, DOCX)
    """
    source = Path(file_path)
    if not source.exists():
        return f"File not found: {file_path}"

    valid_extensions = {".pdf", ".txt", ".md", ".html", ".docx"}
    if source.suffix.lower() not in valid_extensions:
        return f"Unsupported format: {source.suffix}. Supported: {', '.join(valid_extensions)}"

    dest = paper_directory / source.name
    shutil.copy2(source, dest)

    job_id = str(uuid.uuid4())[:8]
    _indexing_jobs[job_id] = {"status": "indexing", "filename": source.name, "error": None}

    async def _index():
        try:
            idx_settings = settings.model_copy(deep=True)
            await get_directory_index(settings=idx_settings)
            _indexing_jobs[job_id]["status"] = "complete"
        except Exception as e:
            _indexing_jobs[job_id]["status"] = "failed"
            _indexing_jobs[job_id]["error"] = str(e)

    asyncio.create_task(_index())

    return f"'{source.name}' copied to library. Indexing in background (job: {job_id}).\nUse get_library_status to check progress."


@server.tool()
async def remove_document(filename: str) -> str:
    """
    Remove a document from the library.

    Args:
        filename: Name of the file to remove (e.g. 'book.pdf')
    """
    target = paper_directory / filename
    if not target.exists():
        available = [f.name for f in paper_directory.iterdir() if f.is_file()]
        return f"File not found: {filename}\nAvailable: {available}"

    target.unlink()
    return f"Removed '{filename}'. The index will refresh on next search."


@server.tool()
async def check_indexing_status() -> str:
    """Check status of background document indexing jobs."""
    if not _indexing_jobs:
        return "No indexing jobs."

    lines = []
    for job_id, info in _indexing_jobs.items():
        line = f"[{info['status']}] {info['filename']} (job: {job_id})"
        if info.get("error"):
            line += f"\n  Error: {info['error']}"
        lines.append(line)

    return "Indexing Jobs:\n" + "\n".join(lines)


async def main():
    logger.info(f"PaperQA2 MCP Server v{paperqa.__version__}")
    logger.info(f"Embedding: {settings.embedding}")
    logger.info(f"Papers: {paper_directory}")

    await server.run()


if __name__ == "__main__":
    try:
        import anyio
        logger.info(f"Starting PaperQA2 MCP Server v{paperqa.__version__}")
        server.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
