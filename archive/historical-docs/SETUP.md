# 🚀 Setup Guide - Academic Research Assistant

## Quick Start

This guide will get your PaperQA2 MCP server running with Claude Desktop in 30-60 minutes.

**What you'll get**: AI-powered search through your academic books using state-of-the-art Voyage AI embeddings.

---

## 📋 Prerequisites

- Python 3.8+
- Claude Desktop installed
- Your PDF books ready
- Credit card for API services (~$22.50 one-time for 50 books)

---

## 🔧 Installation

### 1. Install Dependencies
```bash
pip install paper-qa mcp
```

### 2. Get API Keys

**OpenAI API Key**:
- Go to [platform.openai.com](https://platform.openai.com)
- Create account → API Keys → Create new key
- Copy key (starts with `sk-`)

**Voyage AI API Key**:
- Go to [docs.voyageai.com](https://docs.voyageai.com)  
- Sign up → Generate API key
- Copy key

### 3. Configure Environment

Create `.env` file in project root:
```
OPENAI_API_KEY=your-openai-key-here
VOYAGE_API_KEY=your-voyage-key-here
```

### 4. Add Your Books

Copy your PDF books to:
```
paperqa-mcp/papers/
```

### 5. Test Server

```bash
python3 paperqa-mcp/server.py
```

Should show:
```
INFO: PaperQA2 MCP Server starting with Voyage AI embedding: voyage/voyage-3-large
INFO: PaperQA2 MCP Server ready - connecting to Claude Desktop...
```

### 6. Configure Claude Desktop

Edit `claude_desktop_config.json`:

**Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

Add:
```json
{
  "mcpServers": {
    "paperqa-academic": {
      "command": "python3",
      "args": ["/full/path/to/academic-research-assistant/paperqa-mcp/server.py"],
      "env": {
        "OPENAI_API_KEY": "your-openai-key",
        "VOYAGE_API_KEY": "your-voyage-key"
      }
    }
  }
}
```

**⚠️ Use your actual full path!**

### 7. Test with Claude Desktop

1. Restart Claude Desktop completely
2. Ask: "Check my research library status"
3. Ask: "Search my library for [your research topic]"

---

## 🎯 Success!

You should now be able to:
- ✅ Search through all your PDF books instantly
- ✅ Get detailed answers with citations  
- ✅ Ask complex research questions
- ✅ Compare concepts across authors

---

## 🔧 Troubleshooting

See detailed troubleshooting in `TODO_SETUP.md`.

**Common issues**:
- Module not found → `pip install paper-qa mcp`
- API key errors → Check `.env` file and Claude config
- Path errors → Use full absolute paths in Claude config
- No documents found → Check PDFs are in `paperqa-mcp/papers/`

---

## 📊 What to Expect

**First Run**:
- Processing: 1-5 minutes per book
- Cost: ~$0.45 per book (one-time)
- Storage: ~4-20MB per book

**Ongoing Use**:
- Questions: Answered in seconds
- Cost: ~$0.01-0.05 per question
- No re-processing needed

---

For detailed step-by-step instructions, see `TODO_SETUP.md` in the root folder.