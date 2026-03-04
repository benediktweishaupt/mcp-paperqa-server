# mcp-paperqa-server

MCP server that makes your research library searchable from Claude. You put PDFs in a folder, build an index, and then ask questions against your books. It uses PaperQA2 for retrieval and returns passages with page numbers.

## How it works

1. You drop PDFs (or scanned books after OCR) into `paperqa-mcp/papers/`
2. You build a search index once with `python archive/utilities/build_index.py`
3. You point Claude Desktop at the MCP server
4. You ask questions, it searches your library

Two search modes: full synthesis (agent finds evidence, writes an answer with citations, ~$0.05) or raw context extraction (returns matching passages directly, much cheaper).

## Setup

```bash
git clone https://github.com/benediktweishaupt/mcp-paperqa-server.git
cd mcp-paperqa-server
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add API keys (OpenAI required, Voyage optional)
```

Add your books and build the index:

```bash
cp your-books/*.pdf paperqa-mcp/papers/
python archive/utilities/build_index.py
```

For scanned books, run OCR first: `python archive/utilities/ocr_papers.py`

Add to Claude Desktop config:

```json
{
  "mcpServers": {
    "paperqa-academic": {
      "command": "python",
      "args": ["paperqa-mcp/server.py"],
      "cwd": "/path/to/mcp-paperqa-server"
    }
  }
}
```

## Tools

- `search_literature` — ask a question, get a synthesized answer with citations
- `get_contexts` — get raw text chunks matching a query (no LLM synthesis)
- `get_library_status` — check what's indexed
- `configure_embedding` — switch embedding model

## Built with

Python, FastMCP, PaperQA2, OpenAI.
