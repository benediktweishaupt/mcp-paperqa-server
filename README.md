# 🎓 Academic Research Assistant

**AI-powered research through your academic library using Claude Desktop**

Transform your PhD research workflow: Natural conversations with Claude to find relevant passages, track arguments across authors, and generate properly formatted citations from your personal academic library.

## ⚡ Quick Setup

### Prerequisites
- Python 3.11+
- OpenAI API key (required)
- Voyage AI API key (recommended for 6x cost savings)

### Installation
```bash
git clone <repository-url>
cd academic-research-assistant
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure API Keys
```bash
cp .env.example .env
# Edit .env with your keys:
# OPENAI_API_KEY=your-key-here
# VOYAGE_API_KEY=your-key-here
```

## 📄 Document Processing

### Modern PDFs (Text-Ready)
```bash
# 1. Add PDFs to library
cp your-papers/*.pdf paperqa-mcp/papers/

# 2. Build search index (~$3-5 cost)
python archive/utilities/build_index.py

# 3. Start MCP server
python paperqa-mcp/server.py
```

### Scanned PDFs (Need OCR)
```bash
# 1. Check which PDFs need OCR
python archive/utilities/test_pdf_text.py

# 2. Install OCR tools (one-time)
brew install tesseract ocrmypdf  # macOS

# 3. Convert scanned PDFs
python archive/utilities/ocr_papers.py

# 4. Build index and start server
python archive/utilities/build_index.py
python paperqa-mcp/server.py
```

## 🔌 Claude Desktop Setup

Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "paperqa-academic": {
      "command": "python",
      "args": ["paperqa-mcp/server.py"],
      "cwd": "/path/to/academic-research-assistant",
      "env": {
        "OPENAI_API_KEY": "your-key",
        "VOYAGE_API_KEY": "your-key"
      }
    }
  }
}
```

## 🎯 Usage

### Research Queries
```
"What's the current status of my research library?"
"What does Hito Steyerl write about truth and representation?"
"Find papers that mention both neural networks and interpretability"
"Compare methodological approaches across my papers"
```

### Example Output
```
# Literature Search Results

Hito Steyerl examines truth and representation in documentary practices...
[Detailed analysis with proper academic citations]

---
Research Summary: 5 evidence sources analyzed | Query Cost: $0.0373
Library Status: Using pre-built index | Embedding Model: text-embedding-3-small
```

## 🛠 Core Features

- **Literature Search**: Multi-source analysis with citations
- **Library Status**: Document count, storage, configuration
- **Embedding Config**: Switch between cost/performance models

## 🏗 Architecture

**Current Structure:**
```
paperqa-mcp/
├── server.py                # Main MCP server (FastMCP + PaperQA2)
├── config.py               # Settings and model configuration
├── papers/                 # Your PDF library
└── cache/index/           # Pre-built search indices

archive/utilities/          # Document processing scripts
├── test_pdf_text.py       # OCR readiness detection
├── ocr_papers.py          # Multi-language OCR processing
├── build_index.py         # Index building with cost tracking
└── rebuild_index.py       # Index rebuilding utility
```

**Design Philosophy:**
- **Offline processing**: Heavy lifting (OCR, indexing) done separately
- **Instant MCP**: Server loads pre-built indices in <1 second
- **Cost transparent**: Know embedding costs upfront
- **Production ready**: 256 lines, minimal dependencies

## 🧪 Testing

```bash
# Check OCR needs
python archive/utilities/test_pdf_text.py

# Test MCP functionality
python tests/run_all_tests.py

# Full integration test
python tests/test_paperqa_mcp_integration.py
```

## 🔧 Troubleshooting

**Empty search results:**
```bash
ls paperqa-mcp/papers/                    # Check PDFs exist
ls paperqa-mcp/cache/index/              # Check index built
python archive/utilities/rebuild_index.py # Rebuild if needed
```

**OCR issues:**
```bash
brew install tesseract ocrmypdf           # Install OCR tools
python archive/utilities/test_pdf_text.py # Test extraction
```

**MCP connection:**
- Verify Claude Desktop config path and Python paths
- Check API keys in environment
- Restart Claude Desktop after config changes

## 💰 Cost Management

**Embedding Models (Academic Performance):**
- **voyage-ai/voyage-3-lite**: $0.08/1M tokens (recommended)
- **text-embedding-3-small**: $0.52/1M tokens (baseline)

**Typical Costs:**
- **Index building**: $3-5 per 50 academic papers (one-time)
- **Research queries**: $0.02-0.05 per question
- **50-paper library**: ~$10 total setup cost

## 📚 Key Documents

- `docs/indexing-and-ocr-analysis.md` - Complete workflow analysis
- `docs/mcp-server-debugging-report.md` - Troubleshooting guide
- `TODO_SETUP.md` - Detailed setup instructions

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Test changes: `python tests/run_all_tests.py`
4. Submit pull request

---

**Ready to revolutionize your PhD research? Start with the Quick Setup above!**