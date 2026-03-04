# mcp-paperqa-server

An MCP server built on PaperQA2. Makes your research library searchable from Claude.

You put PDFs in a folder, build an index, and then ask questions against your books. It returns passages with page numbers.

## How it works

1. You drop PDFs (or scanned books after OCR) into `paperqa-mcp/papers/`
2. You build a search index once with `python paperqa-mcp/build_index.py`
3. You point Claude Desktop at the MCP server
4. You ask questions, it searches your library

Two search modes: full synthesis (agent finds evidence, writes an answer with citations, ~$0.05) or raw context extraction (returns matching passages directly, near-zero cost).

## Setup

Requires Python 3.11+.

```bash
git clone https://github.com/benediktweishaupt/mcp-paperqa-server.git
cd mcp-paperqa-server
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add API keys (OpenAI + Voyage required)
```

Add your books and build the index:

```bash
cp your-books/*.pdf paperqa-mcp/papers/
python paperqa-mcp/build_index.py
```

For scanned books, run OCR first: `python archive/utilities/ocr_papers.py`

Add to Claude Desktop config:

```json
{
  "mcpServers": {
    "paperqa-academic": {
      "command": "/path/to/mcp-paperqa-server/venv/bin/python",
      "args": ["/path/to/mcp-paperqa-server/paperqa-mcp/server.py"],
      "env": {
        "PYTHONPATH": "/path/to/mcp-paperqa-server"
      }
    }
  }
}
```

## Tools

- `search_literature` — synthesized answer with citations (mode: fast/thorough)
- `get_contexts` — raw text chunks, near-zero cost
- `add_document` — add a book to the library
- `remove_document` — remove a document
- `check_indexing_status` — check background indexing progress
- `get_library_status` — check what's indexed

## Built with

Python, FastMCP, PaperQA2, Voyage AI, OpenAI.
