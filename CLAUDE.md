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

## Core Features to Implement

1. **Intelligent Literature Search** - Natural language queries across PDF library
2. **Argument Chain Tracking** - Trace theoretical development across sources
3. **Contradiction Detection** - Identify disagreements between authors
4. **Research Gap Analysis** - Find unexplored areas in literature
5. **Citation Management** - Generate properly formatted citations

## Technical Architecture

**MCP Tools to Implement:**
- Literature search with context and confidence scoring
- Full document/chapter retrieval with structure preservation
- Citation finding with exact location verification
- Multi-source synthesis preparation
- Contradiction checking with nuance detection
- Argument chain tracking with logical structure
- Research gap identification
- Citation export with format validation

**Quality Requirements:**
- 100% citation accuracy (zero tolerance for errors)
- Intelligent chunking that preserves complete argumentative units
- High-quality embeddings optimized for academic language
- Context preservation around chunks (full paragraphs minimum)
- Hierarchical document understanding

## Code Standards

- Prioritize academic-grade quality over speed
- Every result must include exact source attribution (page/paragraph)
- Preserve document structure and cross-references
- Include confidence scoring for all operations
- Handle academic PDF complexity (multi-column, footnotes, references)
- Document both implementation and academic rationale

## Development Phases

1. **Phase 1**: MCP server setup + basic PDF processing + search
2. **Phase 2**: Document intelligence + cross-reference resolution
3. **Phase 3**: Synthesis capabilities + argument tracking
4. **Phase 4**: Production quality + scale optimization

## Special Instructions

- Test with diverse academic PDFs from different publishers
- Validate chunking preserves complete thoughts/arguments
- Academic terminology requires specialized embedding approaches
- Cross-reference resolution ("see Chapter 2") is critical
- All features must integrate seamlessly with Claude conversation flow

## Context Files

@academic-mcp-server/prd.md - Complete technical specification and requirements