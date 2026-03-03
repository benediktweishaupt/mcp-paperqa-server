# Academic Research Assistant

MCP server that connects Claude Desktop to your personal academic library. Ask questions in natural language, get answers with citations from your own books and papers.

## What it does

You drop PDFs into a folder, build a search index, and then ask Claude things like "What does Hito Steyerl write about truth and representation?" — and it finds the relevant passages across your entire library, with proper citations and page numbers.

## Why it works well

The retrieval is surprisingly good. It uses Voyage AI embeddings (voyage-3-lite) for semantic search via PaperQA2, which means it understands what you're asking for, not just keyword matching. A query costs about $0.02–0.05. Setting up a 50-paper library costs around $10 total.

The architecture is simple on purpose: heavy operations (OCR, indexing) happen offline. The MCP server loads pre-built indices and starts in under a second. Production code is 256 lines.

## What I learned building it

The interesting part was the pivot. I started with a custom RAG solution that was expensive and fragile. Integrating PaperQA2 cut the codebase by 80% and made everything more reliable. The other discovery: switching from OpenAI's text-embedding-3-small to Voyage AI's voyage-3-lite reduced embedding costs by 6x with equal or better retrieval quality for academic texts. Adding a dual-mode architecture (raw extraction vs. LLM synthesis) brought another 100x cost reduction for simple lookups.

## Stack

Python, FastMCP, PaperQA2, Voyage AI, OpenAI, Tesseract OCR.

## Setup

```bash
git clone https://github.com/benediktweishaupt/academic-research-assistant.git
cd academic-research-assistant
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your API keys
```

Add PDFs, build the index, configure Claude Desktop:

```bash
cp your-papers/*.pdf paperqa-mcp/papers/
python archive/utilities/build_index.py
```

```json
{
  "mcpServers": {
    "paperqa-academic": {
      "command": "python",
      "args": ["paperqa-mcp/server.py"],
      "cwd": "/path/to/academic-research-assistant"
    }
  }
}
```

Scanned PDFs work too — there's an OCR pipeline built in (`python archive/utilities/ocr_papers.py`).
