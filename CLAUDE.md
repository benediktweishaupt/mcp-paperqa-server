# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Academic Research Assistant - An MCP server for PhD students to interact with their research library through Claude. The main development work is in the `academic-mcp-server/` directory.

## IMPORTANT: **ALLWAYS CHECK THE DOCS**

Since we are building on top of paper qa make all decissions considering the api of paperqa2 and what it offers:
https://github.com/Future-House/paper-qa

## Repository Structure

- `academic-mcp-server/` - Main MCP server development directory
  - `prd.md` - Product Requirements Document with detailed specifications
- `paper-qa/` - **NEVER MODIFY** - Clean PaperQA2 clone for dependency use only
- `agentic-coding/`, `expose/`, `expose-reviewer/` - Documentation directories (not relevant for MCP development)

## CRITICAL ARCHITECTURE RULE - NEVER VIOLATE

**PaperQA2 Integration Architecture - ABSOLUTELY MANDATORY:**

### ❌ NEVER DO:

- **NEVER** modify any files inside `paper-qa/` directory
- **NEVER** create new files in `paper-qa/src/`
- **NEVER** add code to the PaperQA2 repository
- **NEVER** commit changes to the `paper-qa/` directory

### ✅ CORRECT APPROACH:

- `paper-qa/` is a **READ-ONLY** dependency directory
- Only use `paper-qa/` for: installation (`pip install -e .`) and importing PaperQA2 classes
- Build our MCP server in `academic-mcp-server/` that USES PaperQA2 as external dependency
- Create tests in `/tests/` or root level that import PaperQA2
- Use Python subprocess or API calls to bridge TypeScript ↔ PaperQA2
- Keep `paper-qa/` clean so we can `git pull` updates anytime without conflicts

### PaperQA2 Usage Patterns:

- **Starting PaperQA2**: Import and use their classes/functions in our code
- **Testing**: We can reuse their test utilities and stub data for our integration tests
- **Execution**: Run PaperQA2 via Python imports, not by modifying their CLI or source

### Available PaperQA2 Test Categories (for reference/reuse):

- **agents**: Agent workflow testing with tools and memory
- **cli**: Command line interface testing
- **clients**: External API clients (Crossref, Semantic Scholar, etc.)
- **clinical_trials**: Medical research specific functionality
- **configs**: Settings and configuration validation
- **paperqa**: Core functionality, citations, document processing

### PaperQA2 Test Resources We Can Use:

### Directory Usage:

**This rule has been violated multiple times. NEVER make this mistake again.**

## Development Environment

- **Primary Language**: Python (for PDF processing, embeddings, search)
- **Framework**: MCP (Model Context Protocol) server architecture
- **Key Libraries**:
- **Testing**: pytest for Python components
- **Code Style**: Black for Python, Prettier for JS/TS

## Git

- when starting a new subtask create a new git feature branch.
- commit each subtask step when it makes sense.
- commit often.

## CLAUDE.md improvement Triggers

- **When to improve this claude.md Rule Document Triggers:**
  - New code patterns not covered by existing rules
  - Repeated similar implementations across files
  - Common error patterns that could be prevented
  - New libraries or tools being used consistently
  - Emerging best practices in the codebase

## MCP Servers

- **Task Master**:

  - If you want to call taskmaster use ´task-master´ as command
  - Task master is installed globally

- **Context7**:
  - if you look up Doumentation use context7 MCP
  - use context7 to reliably check for the right version of Documentation

## Code Standards

- Use Python and TypeScript/JavaScript Best Practices
- Test coverage minimum 80%
- Document complex logic
- Use English for Variable Names and Comments
- Use meaningful variable/function names
- Document all public APIs
- Handle errors gracefully

## Documentation

- If not already there, make a PROGRESS.md file in the root folder.
- After each task document what you have done and how you have implemented it.
- If you came across certain things you couldn't implement like you initially thought, document this DEFENITLEY.

- **Analysis Process:**
  - Compare new code with existing rules
  - Identify patterns that should be standardized
  - Look for references to external documentation
  - Check for consistent error handling patterns

## Architecture Principles

- Keep it simple (KISS)
- Don't repeat yourself (DRY)
- Single responsibility principle

## Special Instructions

- Ask when requirements are unclear
- Implement error handling
- Consider performance implications
- Use modern language features

## Special Instructions

- Ask for clarification when requirements are ambiguous
- Consider performance implications
- Think about edge cases
- Validate inputs
- Log important operations

## Task Master AI Instructions

**Import Task Master's development workflow commands and guidelines, treat as if import is in the main CLAUDE.md file.**
@./.taskmaster/CLAUDE.md

- No unnecessary custom builds

**For debugging:**
lets plan this debugging carefully. looking in the commit history and how many new packages came in, this does not look reasonable. │
please check:'/Users/benediktw/Documents/gitHub/academic-research-assistant/docs/mcp-server-debugging-report.md' what hase been tried so far.\ │
also check the most recent logs: │
/Users/benediktw/Library/Logs/Claude
