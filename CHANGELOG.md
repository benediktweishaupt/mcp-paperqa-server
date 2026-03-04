# Changelog

## 2026-03-04

- Removed papers, cache, and index files from git tracking.
- Renamed repo from `academic-research-assistant` to `mcp-paperqa-server`.

## 2026-03-03

- Rewrote README.

## 2025-08-22

- Added `get_contexts` tool — returns raw text chunks without LLM synthesis, ~100x cheaper than full search.
- Enabled `evidence_skip_summary` — direct quotes instead of paraphrased evidence.

## 2025-08-21

This was the big day. Most of the actual working system came together here.

- Fixed async TaskGroup errors that broke MCP communication.
- Got `agent_query` working — the core search pipeline finally ran end to end.
- Built OCR pipeline for scanned PDFs (Tesseract).
- Achieved first successful PaperQA query against real documents.
- Cleaned up project structure heavily — archived debug files, redundant code, old docs.
- Removed `.mcp.json` from tracking (contains API keys).
- Wrote documentation and article series about the build process.

## 2025-08-20

- Added embedding cache to avoid re-processing already indexed documents.
- Various config cleanups.

## 2025-08-19 — The PaperQA2 pivot

Threw out the custom TypeScript MCP server and all the hand-rolled Python PDF/NLP code. Replaced everything with PaperQA2 as the backend.

- Removed custom PDF processing engine, chunking logic, NLP pipeline.
- Implemented lean MCP server (~250 lines) that wraps PaperQA2.
- Switched from TypeScript to Python-only stack.
- Adopted FastMCP for tool decoration.

This was the right call. Two weeks of custom code replaced by a library that does it better.

## 2025-08-12 — 2025-08-18

Built custom text chunking and argumentative unit detection. Sliding window chunker, semantic analysis for detecting argument boundaries. All of this got removed on Aug 19 when we switched to PaperQA2.

## 2025-08-08 — 2025-08-11

Built custom PDF processing engine in Python. Multi-column layout handling, academic text parsing. Also removed on Aug 19.

## 2025-08-07

- Initialized Task Master for project management.
- Built first MCP server skeleton in TypeScript with tool registration.
- Set up basic architecture.

## 2025-08-06

- Initial commit. Repository setup, research documentation, bibliography.
- Monorepo folder structure.
