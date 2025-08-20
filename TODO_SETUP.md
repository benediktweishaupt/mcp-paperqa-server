# 📋 **TODO: Complete Setup for PaperQA2 MCP Server**

## **📌 Overview**
This checklist will get your PaperQA2 MCP server working with Claude Desktop so you can search through your academic books using AI.

**Expected Time**: 30-60 minutes setup + processing time for your books
**Cost**: ~$22.50 one-time + ~$0.01-0.05 per question

---

## **✅ Pre-Setup Checklist**

- [ ] **Have Claude Desktop installed** and working
- [ ] **Have Python 3.8+** installed on your computer
- [ ] **Have your PDF books** ready (up to 50 books recommended)
- [ ] **Have a credit card** for API services (OpenAI + Voyage AI)

---

## **🔧 STEP 1: Install Python Dependencies**

### **Task**: Install required packages

- [ ] Open terminal/command prompt
- [ ] Run: `pip install paper-qa mcp`
- [ ] **If that fails**, try: `pip3 install paper-qa mcp`
- [ ] **Verify installation**: `python -c "import paperqa, mcp; print('Success!')"`

**❌ If you get errors**:
- Try: `python3 -m pip install paper-qa mcp`
- Or: `pip install --user paper-qa mcp`

**✅ Success looks like**: No error messages, "Success!" prints

---

## **🔑 STEP 2: Get API Keys**

### **A) Get OpenAI API Key**

- [ ] Go to: [platform.openai.com](https://platform.openai.com)
- [ ] **Sign up** or log in
- [ ] Go to **"API Keys"** section
- [ ] Click **"Create new secret key"**
- [ ] **Copy the key** (starts with `sk-`)
- [ ] **Write it down securely** (you can't see it again!)

### **B) Get Voyage AI API Key**

- [ ] Go to: [docs.voyageai.com](https://docs.voyageai.com)
- [ ] **Sign up** for an account
- [ ] Go to **"API Keys"** or **"Dashboard"**
- [ ] **Generate new API key**
- [ ] **Copy the key**
- [ ] **Write it down securely**

**💡 Tip**: Keep these keys in a password manager or secure note app.

---

## **🌍 STEP 3: Set Up Environment Variables**

Choose **ONE** method:

### **Method A: Terminal Commands (Temporary)**
- [ ] Run: `export OPENAI_API_KEY="your-openai-key-here"`
- [ ] Run: `export VOYAGE_API_KEY="your-voyage-key-here"`
- [ ] **Note**: These only work in the current terminal session

### **Method B: Create .env File (Recommended)**
- [ ] In your project folder, create file named `.env`
- [ ] Add these lines:
  ```
  OPENAI_API_KEY=your-openai-key-here
  VOYAGE_API_KEY=your-voyage-key-here
  ```
- [ ] **Save the file**
- [ ] **Don't share this file** with anyone!

**✅ Test**: Run `echo $OPENAI_API_KEY` - should show your key

---

## **📚 STEP 4: Prepare Your Documents**

### **Organize Your PDF Books**

- [ ] **Navigate** to your project folder (where `paperqa_mcp_server.py` is)
- [ ] **Check**: The `papers/` folder should exist (created automatically)
  - If not: `mkdir papers`
- [ ] **Copy your PDF books** into the `papers/` folder
- [ ] **Use clear filenames**:
  - ✅ Good: `Luhmann_Social_Systems_Theory.pdf`
  - ❌ Avoid: `book1.pdf`, `scan_004.pdf`

### **Recommended Folder Structure**
```
your-project-folder/
├── paperqa_mcp_server.py
├── papers/                    ← Your PDF books go here
│   ├── Luhmann_Social_Systems.pdf
│   ├── Parsons_Social_Action.pdf
│   └── Weber_Economy_Society.pdf
├── cache/                     ← Auto-created for processed data
└── .env                      ← Your API keys
```

**💡 Limits**: 50 books max recommended for good performance

---

## **🧪 STEP 5: Test the Server**

### **Run Server Standalone**

- [ ] **Open terminal** in your project folder
- [ ] **Run**: `python3 paperqa_mcp_server.py`
- [ ] **Wait for startup messages**

### **✅ Success Looks Like**:
```
INFO:paperqa_mcp_server:PaperQA2 MCP Server starting with Voyage AI embedding: voyage/voyage-3-large
INFO:paperqa_mcp_server:💡 Using voyage-3-large: 9.74% better than OpenAI + 2x cheaper + 32K context
INFO:paperqa_mcp_server:Found X papers in directory
INFO:paperqa_mcp_server:PaperQA2 MCP Server ready - connecting to Claude Desktop...
```

### **❌ Common Errors & Fixes**:

- [ ] **"ModuleNotFoundError"** → Re-install: `pip install paper-qa mcp`
- [ ] **"API key not found"** → Check your .env file or environment variables
- [ ] **"No papers found"** → Check PDFs are in `papers/` folder
- [ ] **"Permission denied"** → Try: `python paperqa_mcp_server.py` instead

**✅ Test Complete**: Server runs without errors and shows "ready" message

---

## **🖥️ STEP 6: Configure Claude Desktop**

### **Find Claude Desktop Config File**

**Location depends on your system**:
- [ ] **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- [ ] **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- [ ] **Linux**: `~/.config/Claude/claude_desktop_config.json`

### **Get Your Server's Full Path**

- [ ] **In your project folder**, run: `pwd` (Mac/Linux) or `cd` (Windows)
- [ ] **Note the full path** (like `/Users/you/Documents/academic-mcp-server`)
- [ ] **Your server path** = `[full path]/paperqa_mcp_server.py`

### **Update Config File**

- [ ] **Open** `claude_desktop_config.json` in a text editor
- [ ] **Add this configuration**:

```json
{
  "mcpServers": {
    "paperqa-academic": {
      "command": "python3",
      "args": ["/FULL/PATH/TO/YOUR/paperqa_mcp_server.py"],
      "env": {
        "OPENAI_API_KEY": "your-actual-openai-key-here",
        "VOYAGE_API_KEY": "your-actual-voyage-key-here"
      }
    }
  }
}
```

- [ ] **Replace** `/FULL/PATH/TO/YOUR/` with your actual path
- [ ] **Replace** the API keys with your actual keys
- [ ] **Save the file**

**⚠️ CRITICAL**: Use the **exact full path** to your server file!

---

## **🔄 STEP 7: Connect to Claude Desktop**

### **Restart Claude Desktop**

- [ ] **Completely quit** Claude Desktop (don't just minimize)
- [ ] **Wait 5 seconds**
- [ ] **Start Claude Desktop** again
- [ ] **Wait for it to fully load**

### **Check Connection**

- [ ] **Look at your server terminal** - should show connection messages
- [ ] **In Claude Desktop**, you should see MCP server connected (look for indicator)

**✅ Success**: Server terminal shows Claude Desktop connected

---

## **🎯 STEP 8: Test Everything Works**

### **First Test: Library Status**

- [ ] **In Claude Desktop**, ask:
  ```
  "Check my research library status"
  ```

**✅ Expected Response**: Information about your documents and system status

### **Second Test: Add Document (if needed)**

- [ ] **If no documents were found**, ask:
  ```
  "Add this document to my library: /path/to/your/book.pdf"
  ```

### **Third Test: Research Question**

- [ ] **Ask a real research question** about your books:
  ```
  "What are the main concepts in [your field] according to my library?"
  ```

**✅ Success**: Claude searches your books and gives detailed answers with citations!

---

## **🚨 Troubleshooting Checklist**

### **Server Won't Start**
- [ ] Check Python installation: `python3 --version`
- [ ] Check packages: `pip list | grep paperqa`
- [ ] Check API keys: `echo $OPENAI_API_KEY`
- [ ] Check file permissions: `ls -la paperqa_mcp_server.py`

### **Claude Desktop Won't Connect**
- [ ] Check config file path is correct
- [ ] Check server file path in config is absolute (starts with `/`)
- [ ] Check API keys in config file
- [ ] Restart Claude Desktop completely
- [ ] Check server is still running

### **No Documents Found**
- [ ] Check PDFs are in `papers/` folder
- [ ] Check PDF files aren't corrupted
- [ ] Check file permissions on PDFs
- [ ] Wait - first processing takes 5-30 minutes

### **API Errors**
- [ ] Check API keys are valid
- [ ] Check you have credits/billing set up
- [ ] Check internet connection
- [ ] Try different API key

---

## **📊 First Run Expectations**

### **What Happens During First Run**
- [ ] **Server processes** each PDF (extracts text, creates embeddings)
- [ ] **Time**: 1-5 minutes per book (depends on size)
- [ ] **Cost**: ~$0.45 per book for embeddings
- [ ] **Storage**: ~4-20MB per book in cache

### **Progress Indicators**
- [ ] Watch server terminal for processing messages
- [ ] `cache/` folder grows in size
- [ ] First questions take longer (server is still processing)

### **After First Run**
- [ ] **Subsequent startups**: 2-5 seconds
- [ ] **Questions**: Answered in seconds
- [ ] **Cost**: Only LLM costs (~$0.01-0.05 per question)

---

## **🎉 Success Criteria**

**✅ You're done when**:
- [ ] Server starts without errors
- [ ] Claude Desktop connects to server
- [ ] Library status shows your documents
- [ ] Research questions get answers with citations
- [ ] Everything works smoothly

**🎯 Final Test**: Ask Claude:
```
"Search my library for information about [topic in your field] and provide a comprehensive summary with citations"
```

If Claude searches through your books and provides detailed, cited answers, **congratulations! Your academic research assistant is ready!** 🎓

---

## **📝 Notes Section**

**Write down any issues you encounter**:

- Issue 1: ________________________________
  - Solution: ____________________________

- Issue 2: ________________________________
  - Solution: ____________________________

**Your API Keys** (keep secure):
- OpenAI: sk-___________________________
- Voyage: ______________________________

**Your File Paths**:
- Project folder: _______________________
- Server file: __________________________
- Claude config: ________________________

---

**🔄 Need Help?** Check the error messages in the server terminal and match them against the troubleshooting section above.