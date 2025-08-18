# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Academic Research Assistant - An MCP server for PhD students to interact with their research library through Claude. The main development work is in the `academic-mcp-server/` directory.

## Repository Structure

- `academic-mcp-server/` - Main MCP server development directory
  - `prd.md` - Product Requirements Document with detailed specifications
- `agentic-coding/`, `expose/`, `expose-reviewer/` - Documentation directories (not relevant for MCP development)

## Development Environment

- **Primary Language**: Python (for PDF processing, embeddings, search)
- **Secondary Language**: TypeScript/JavaScript (for MCP protocol implementation)
- **Framework**: MCP (Model Context Protocol) server architecture
- **Key Libraries**:
  - PDF processing: PyMuPDF, pdfplumber
  - Embeddings: sentence-transformers, openai
  - Vector search: FAISS, ChromaDB
  - Citation handling: pybtex, citeproc-py
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

## Context Files

@academic-mcp-server/prd.md - Complete technical specification and requirements

## Task Master AI Instructions

**Import Task Master's development workflow commands and guidelines, treat as if import is in the main CLAUDE.md file.**
@./.taskmaster/CLAUDE.md
