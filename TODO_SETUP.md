# 📋 **TODO: Complete Setup for PaperQA2 MCP Server**

## **📌 Overview**

This checklist will get your PaperQA2 MCP server working with Claude Desktop so you can search through your academic books using AI.

**Expected Time**: 30-60 minutes setup + processing time for your books
**Cost**: ~$22.50 one-time + ~$0.01-0.05 per question

---

## **✅ Pre-Setup Checklist**

- [x] **Have Claude Desktop installed** and working
- [x] **Have Python 3.8+** installed on your computer
- [x] **Have your PDF books** ready (up to 50 books recommended)
- [x] **Have a credit card** for API services (OpenAI + Voyage AI)

---

## **🔧 STEP 1: Install Python Dependencies**

### **Task**: Set up virtual environment and install packages

- [ ] Open terminal/command prompt
- [ ] **Set up pyenv and Python 3.8.10**:
  ```bash
  export PYENV_ROOT="$HOME/.pyenv"
  [[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
  eval "$(pyenv init -)"
  pyenv shell 3.8.10
  ```
- [ ] **Create virtual environment**: `python3 -m venv venv`
- [ ] **Activate virtual environment**: `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows)
- [ ] **Upgrade pip**: `pip install --upgrade pip`
- [ ] **Install packages**: `pip install paper-qa mcp`
- [ ] **Verify installation**: `python -c "import paperqa, mcp; print('Success!')"`

**❌ If you get errors**:

- Try: `python3 -m pip install paper-qa mcp`
- Or: `pip install --user paper-qa mcp`

**✅ Success looks like**: No error messages, "Success!" prints

---

## **🔑 STEP 2: Set Up API Keys**

- [x] Get [OpenAI API key](https://platform.openai.com/api-keys) and [Voyage AI key](https://docs.voyageai.com)
- [x] Create `.env` file in project root:

```
OPENAI_API_KEY=your-openai-key-here
VOYAGE_API_KEY=your-voyage-key-here
```

**✅ Test**: `echo $OPENAI_API_KEY` should show your key

---

## **📚 STEP 3: Prepare Your Documents**

### **Organize Your PDF Books**

- [ ] **Navigate** to your project folder (where `paperqa-mcp/server.py` is)
- [ ] **Check**: The `paperqa-mcp/papers/` folder should exist (created automatically)
  - If not: `mkdir paperqa-mcp/papers`
- [ ] **Copy your PDF books** into the `papers/` folder
- [ ] **Use clear filenames**:
  - ✅ Good: `Luhmann_Social_Systems_Theory.pdf`
  - ❌ Avoid: `book1.pdf`, `scan_004.pdf`

### **Recommended Folder Structure**

```
academic-research-assistant/
├── venv/                      ← Virtual environment
├── paperqa-mcp/
│   ├── server.py             ← Main MCP server
│   ├── papers/               ← Your PDF books go here
│   │   ├── Luhmann_Social_Systems.pdf
│   │   ├── Parsons_Social_Action.pdf
│   │   └── Weber_Economy_Society.pdf
│   └── cache/                ← Auto-created for processed data
└── .env                      ← Your API keys
```

**💡 Limits**: 50 books max recommended for good performance

---

## **🧪 STEP 4: Test the Server**

### **Test Server**

```bash
source venv/bin/activate
python paperqa-mcp/server.py
```

### **✅ Success Looks Like**:

```
INFO:server:PaperQA2 MCP Server starting with Voyage AI embedding: voyage/voyage-3-large
INFO:server:💡 Using voyage-3-large: 9.74% better than OpenAI + 2x cheaper + 32K context
INFO:server:Found X papers in directory
INFO:server:PaperQA2 MCP Server ready - connecting to Claude Desktop...
```

### **❌ Common Issues**:

- **ModuleNotFoundError** → Activate venv: `source venv/bin/activate`
- **API key errors** → Check `.env` file
- **No papers found** → Add PDFs to `paperqa-mcp/papers/`

**✅ Success**: Server shows "ready" message

---

## **🖥️ STEP 5: Configure Claude Desktop**

- [ ] Get project path: `pwd` (outputs like `/Users/you/Documents/academic-research-assistant`)
- [ ] Edit Claude config file:
  - **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
  - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
  - **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "paperqa-academic": {
      "command": "/YOUR/PROJECT/PATH/venv/bin/python",
      "args": ["/YOUR/PROJECT/PATH/paperqa-mcp/server.py"],
      "env": {
        "OPENAI_API_KEY": "your-key-here",
        "VOYAGE_API_KEY": "your-key-here"
      }
    }
  }
}
```

**⚠️ Use full paths and venv Python!**

---

## **🔄 STEP 6: Connect to Claude Desktop**

- [ ] Restart Claude Desktop completely
- [ ] Check server terminal for connection messages
- [ ] Look for MCP indicator in Claude Desktop

**✅ Success**: Connection messages appear in server terminal

---

## **🎯 STEP 7: Test Everything**

**In Claude Desktop, ask:**

1. `"Check my research library status"`
2. `"What are the main concepts in [your field] according to my library?"`

**✅ Success**: Claude searches your books and provides cited answers!

---

## **🚨 Quick Troubleshooting**

**Server won't start:**

- Activate venv: `source venv/bin/activate`
- Check API keys: `echo $OPENAI_API_KEY`

**Claude won't connect:**

- Use absolute paths in config
- Restart Claude Desktop completely
- Check server is still running

**No documents:**

- Add PDFs to `paperqa-mcp/papers/`
- Wait 5-30 min for first processing

---

## **📊 First Run Info**

**Initial processing:**

- ~1-5 min per PDF
- ~$0.45 per book (one-time)
- Creates `paperqa-mcp/cache/` folder

**After setup:**

- Startup: 2-5 seconds
- Questions: ~$0.01-0.05 each

---

## **🎉 You're Done! 🎓**

**Final test**: Ask Claude to search your library for a topic in your field.

**Success**: Claude provides detailed answers with citations from your books!

---

## **📝 Notes**

**Issues encountered:**

- Issue: **********\_\_\_\_**********
- Solution: **********\_**********

**Your paths:**

- Project: **********\_\_**********
- Config: **********\_\_\_**********
