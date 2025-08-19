# PaperQA2 MCP Integration - Product Requirements Document

**Project**: Academic Research MCP Server  
**Based On**: PaperQA2 Fork with MCP Wrapper  
**Date**: August 19, 2025  
**Timeline**: 5-7 days (testing + integration)

---

## Executive Summary

**Goal**: Create a production-ready MCP server that exposes PaperQA2's research capabilities to Claude Desktop, enabling natural academic research workflows for PhD students and researchers.

**Approach**: Fork PaperQA2, add lightweight MCP wrapper, and thoroughly test both components separately before integration.

**Value Proposition**: Transform Claude Desktop into a sophisticated academic research assistant with evidence-based answers, proper citations, and multi-step reasoning.

---

## Phase 1: Component Testing & Validation (2-3 days)

### 1.1 PaperQA2 Standalone Testing

**Objective**: Validate PaperQA2 functionality with our academic use case and latest embedding APIs.

**Test Environment Setup**:
```bash
# Clone and setup PaperQA2
git clone https://github.com/Future-House/paper-qa.git
cd paper-qa
pip install -e .

# Test with academic PDFs
mkdir test_papers/
# Add 5-10 academic PDFs from different domains
```

**Configuration Testing**:
```python
# Test current embedding setup
settings = Settings(
    embedding="text-embedding-3-small",  # Current default
    llm="gpt-4o",
    temperature=0.0
)

# Test Voyage AI embedding upgrade
settings_voyage = Settings(
    embedding="voyage-ai/voyage-3-lite",  # Best cost/performance
    llm="gpt-4o",
    temperature=0.0
)

# Test Gemini embedding option
settings_gemini = Settings(
    embedding="gemini/gemini-embedding-001",  # Latest performance leader
    llm="gpt-4o", 
    temperature=0.0
)
```

**Test Cases**:
1. **PDF Processing**: Load 10 academic PDFs, verify extraction quality
2. **Search Quality**: Test paper search with academic queries
3. **Evidence Gathering**: Validate context extraction and scoring
4. **Answer Generation**: Check citation quality and academic writing style
5. **Performance**: Measure response times and memory usage
6. **Embedding Comparison**: Benchmark OpenAI vs Voyage vs Gemini

**Success Criteria**:
- [ ] All PDFs process without errors
- [ ] Search returns relevant papers (>80% relevance for test queries)
- [ ] Evidence extraction preserves academic context
- [ ] Citations are properly formatted with page numbers
- [ ] Response time <10 seconds for typical queries
- [ ] Memory usage <2GB for 10-document library

### 1.2 MCP Server Standalone Testing

**Objective**: Build and test basic MCP server functionality before PaperQA2 integration.

**Basic MCP Server Setup**:
```python
# test_mcp_server.py
from mcp.server import Server
import asyncio

server = Server("test-academic")

@server.tool()
async def test_search(query: str) -> str:
    """Test MCP tool functionality"""
    return f"Mock search result for: {query}"

@server.tool()
async def test_upload(file_path: str) -> str:
    """Test file handling"""
    return f"Mock upload of: {file_path}"

if __name__ == "__main__":
    server.run()
```

**Claude Desktop Integration Test**:
```json
// .mcp.json test configuration
{
  "mcpServers": {
    "test-academic": {
      "command": "python",
      "args": ["test_mcp_server.py"],
      "env": {}
    }
  }
}
```

**Test Cases**:
1. **MCP Protocol**: Verify server starts and registers tools
2. **Claude Integration**: Test tool calls from Claude Desktop
3. **Error Handling**: Validate graceful failure modes
4. **Concurrent Requests**: Test multiple simultaneous calls
5. **Configuration**: Verify settings loading and validation

**Success Criteria**:
- [ ] MCP server starts without errors
- [ ] Tools visible and callable from Claude Desktop
- [ ] Error messages are clear and actionable
- [ ] Server handles 5+ concurrent requests
- [ ] Configuration changes apply correctly

---

## Phase 2: MCP Wrapper Development (2-3 days)

### 2.1 Architecture Design

**Directory Structure**:
```
paper-qa-fork/
├── src/paperqa/
│   ├── mcp/                    # New MCP integration module
│   │   ├── __init__.py
│   │   ├── server.py           # Main MCP server implementation
│   │   ├── tools.py            # PaperQA2 tool wrappers
│   │   ├── config.py           # MCP-specific configuration
│   │   └── utils.py            # Helper functions
│   └── cli.py                  # Modified: add mcp-server command
├── examples/
│   └── mcp/
│       ├── basic_usage.py      # Simple usage example
│       ├── claude_setup.md     # Claude Desktop configuration guide
│       └── test_queries.md     # Sample research queries for testing
├── tests/
│   └── test_mcp/
│       ├── test_server.py      # MCP server tests
│       ├── test_tools.py       # Tool wrapper tests
│       └── test_integration.py # End-to-end integration tests
└── docs/
    └── mcp_integration.md      # Comprehensive documentation
```

### 2.2 Core Implementation

**MCP Server (src/paperqa/mcp/server.py)**:
```python
"""PaperQA2 MCP Server Implementation"""
import asyncio
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from mcp.server import Server
from paperqa import Docs, Settings, agent_query
from paperqa.types import PQASession

logger = logging.getLogger(__name__)

class PaperQAMCPServer:
    """MCP Server that exposes PaperQA2 functionality to Claude Desktop"""
    
    def __init__(self, 
                 settings_config: str = "default",
                 paper_directory: Optional[Path] = None,
                 embedding_model: str = "voyage-ai/voyage-3-lite"):
        
        self.server = Server("paperqa-academic")
        self.settings = self._load_settings(settings_config, embedding_model)
        self.docs = Docs()
        self.paper_directory = paper_directory or Path.cwd() / "papers"
        
        # Initialize paper directory if it doesn't exist
        self.paper_directory.mkdir(exist_ok=True)
        
        # Load existing papers on startup
        asyncio.create_task(self._load_existing_papers())
        
        self._register_tools()
    
    def _load_settings(self, config: str, embedding_model: str) -> Settings:
        """Load and configure PaperQA2 settings"""
        if config == "default":
            settings = Settings()
        else:
            settings = Settings.from_name(config)
        
        # Override embedding model with latest best practice
        settings.embedding = embedding_model
        
        # Optimize for MCP usage
        settings.answer.evidence_k = 8  # More evidence for better answers
        settings.answer.max_concurrent_requests = 2  # Conservative for API limits
        
        return settings
    
    async def _load_existing_papers(self):
        """Load any PDFs already in the paper directory"""
        try:
            pdf_files = list(self.paper_directory.glob("*.pdf"))
            logger.info(f"Found {len(pdf_files)} PDF files to index")
            
            for pdf_file in pdf_files:
                await self.docs.aadd_file(
                    file=open(pdf_file, 'rb'),
                    docname=pdf_file.stem,
                    settings=self.settings
                )
            
            logger.info(f"Successfully indexed {len(pdf_files)} papers")
            
        except Exception as e:
            logger.error(f"Error loading existing papers: {e}")
    
    def _register_tools(self):
        """Register PaperQA2 tools with MCP server"""
        
        @self.server.tool()
        async def search_literature(
            query: str,
            max_results: int = 5,
            min_year: Optional[int] = None,
            max_year: Optional[int] = None
        ) -> str:
            """
            Search academic literature and return evidence-based answers.
            
            Args:
                query: Research question or topic to search for
                max_results: Maximum number of results to return (1-20)
                min_year: Earliest publication year to include
                max_year: Latest publication year to include
                
            Returns:
                Comprehensive answer with citations and source attribution
            """
            try:
                # Use PaperQA2's agent_query for full research workflow
                response = await agent_query(
                    query=query,
                    settings=self.settings,
                    docs=self.docs
                )
                
                # Format response for Claude
                answer = response.session.answer
                contexts_info = f"Used {len(response.session.contexts)} evidence sources"
                cost_info = f"Query cost: ${response.session.cost:.4f}"
                
                return f"{answer}\n\n---\n{contexts_info} | {cost_info}"
                
            except Exception as e:
                logger.error(f"Literature search failed: {e}")
                return f"Search failed: {str(e)}"
        
        @self.server.tool()
        async def add_document(
            file_path: str,
            document_name: Optional[str] = None
        ) -> str:
            """
            Add a PDF document to the research library.
            
            Args:
                file_path: Path to PDF file to add
                document_name: Optional custom name for the document
                
            Returns:
                Success message with document details
            """
            try:
                file_path = Path(file_path)
                if not file_path.exists():
                    return f"Error: File not found at {file_path}"
                
                if file_path.suffix.lower() != '.pdf':
                    return f"Error: Only PDF files are supported, got {file_path.suffix}"
                
                # Add to PaperQA2 docs collection
                with open(file_path, 'rb') as f:
                    doc_name = document_name or file_path.stem
                    await self.docs.aadd_file(
                        file=f,
                        docname=doc_name,
                        settings=self.settings
                    )
                
                # Copy to paper directory for persistence
                import shutil
                dest_path = self.paper_directory / file_path.name
                if not dest_path.exists():
                    shutil.copy2(file_path, dest_path)
                
                doc_count = len(self.docs.docs)
                return f"Successfully added '{doc_name}' to library. Total documents: {doc_count}"
                
            except Exception as e:
                logger.error(f"Document upload failed: {e}")
                return f"Upload failed: {str(e)}"
        
        @self.server.tool() 
        async def get_library_status() -> str:
            """
            Get current status of the research library.
            
            Returns:
                Summary of indexed documents and library statistics
            """
            try:
                doc_count = len(self.docs.docs)
                text_count = len(self.docs.texts)
                
                if doc_count == 0:
                    return "Library is empty. Use add_document to add PDFs for research."
                
                # Get document details
                doc_names = [doc.docname for doc in self.docs.docs.values()]
                doc_summary = ", ".join(doc_names[:5])
                if doc_count > 5:
                    doc_summary += f" and {doc_count - 5} more..."
                
                return f"""Research Library Status:
- Documents: {doc_count} indexed
- Text segments: {text_count} searchable chunks  
- Documents: {doc_summary}
- Directory: {self.paper_directory}
- Ready for literature search queries"""
                
            except Exception as e:
                logger.error(f"Status check failed: {e}")
                return f"Status check failed: {str(e)}"
        
        @self.server.tool()
        async def configure_embedding_model(
            model_name: str = "voyage-ai/voyage-3-lite"
        ) -> str:
            """
            Change the embedding model used for semantic search.
            
            Args:
                model_name: Embedding model identifier
                           Options: voyage-ai/voyage-3-lite, gemini/gemini-embedding-001, 
                           text-embedding-3-small, text-embedding-3-large
                           
            Returns:
                Confirmation message with current model
            """
            try:
                old_model = self.settings.embedding
                self.settings.embedding = model_name
                
                # Note: Existing embeddings won't be re-computed automatically
                # Users would need to re-add documents for new embeddings
                
                return f"""Embedding model updated:
- Previous: {old_model}
- Current: {model_name}

Note: Re-add documents to use new embedding model for best search quality."""
                
            except Exception as e:
                logger.error(f"Model configuration failed: {e}")
                return f"Configuration failed: {str(e)}"
    
    def run(self, host: str = "localhost", port: int = 8000):
        """Start the MCP server"""
        logger.info(f"Starting PaperQA MCP Server on {host}:{port}")
        logger.info(f"Paper directory: {self.paper_directory}")
        logger.info(f"Embedding model: {self.settings.embedding}")
        
        try:
            self.server.run(host=host, port=port)
        except KeyboardInterrupt:
            logger.info("Server shutting down...")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
```

**CLI Integration (modified src/paperqa/cli.py)**:
```python
# Add to existing CLI commands

@cli.command()
@click.option("--config", default="default", help="Configuration name to use")
@click.option("--paper-directory", type=click.Path(), help="Directory containing PDF papers") 
@click.option("--embedding-model", default="voyage-ai/voyage-3-lite", help="Embedding model to use")
@click.option("--host", default="localhost", help="Server host")
@click.option("--port", default=8000, help="Server port")
def mcp_server(config: str, paper_directory: str, embedding_model: str, host: str, port: int):
    """Start PaperQA MCP server for Claude Desktop integration"""
    from paperqa.mcp import PaperQAMCPServer
    
    paper_dir = Path(paper_directory) if paper_directory else None
    server = PaperQAMCPServer(
        settings_config=config,
        paper_directory=paper_dir,
        embedding_model=embedding_model
    )
    
    server.run(host=host, port=port)
```

### 2.3 Testing Framework

**Integration Tests (tests/test_mcp/test_integration.py)**:
```python
import pytest
import asyncio
from pathlib import Path
from paperqa.mcp.server import PaperQAMCPServer

@pytest.fixture
async def mcp_server():
    """Create test MCP server instance"""
    test_dir = Path("/tmp/test_papers")
    test_dir.mkdir(exist_ok=True)
    
    server = PaperQAMCPServer(
        paper_directory=test_dir,
        embedding_model="text-embedding-3-small"  # Reliable for testing
    )
    yield server
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)

@pytest.mark.asyncio
async def test_literature_search_workflow(mcp_server):
    """Test complete research workflow"""
    # Add test document
    test_pdf = "test_data/sample_paper.pdf" 
    result = await mcp_server.add_document(test_pdf)
    assert "Successfully added" in result
    
    # Search literature
    query = "What are the main findings about neural networks?"
    result = await mcp_server.search_literature(query, max_results=3)
    
    # Validate response format
    assert len(result) > 100  # Should be substantial answer
    assert "---" in result    # Should have metadata section
    assert "evidence sources" in result.lower()

@pytest.mark.asyncio 
async def test_error_handling(mcp_server):
    """Test graceful error handling"""
    # Test non-existent file
    result = await mcp_server.add_document("nonexistent.pdf")
    assert "Error: File not found" in result
    
    # Test invalid file type
    result = await mcp_server.add_document("test.txt") 
    assert "Only PDF files are supported" in result
```

---

## Phase 3: Integration & Testing (1-2 days)

### 3.1 End-to-End Integration

**Claude Desktop Configuration**:
```json
{
  "mcpServers": {
    "paperqa-academic": {
      "command": "paperqa",
      "args": ["mcp-server", "--paper-directory", "~/research/papers"],
      "env": {
        "OPENAI_API_KEY": "your-key-here",
        "VOYAGE_API_KEY": "your-key-here"
      }
    }
  }
}
```

**Test Scenarios**:
1. **Fresh Start**: Empty library → add documents → search
2. **Existing Library**: Pre-loaded papers → immediate search capability
3. **Academic Workflow**: Multi-step research with evidence gathering
4. **Error Recovery**: Network failures, invalid files, API limits
5. **Performance**: Large libraries (20+ papers), concurrent queries

### 3.2 Quality Assurance

**Academic Quality Tests**:
```python
test_queries = [
    "What are the latest developments in transformer attention mechanisms?",
    "How do social media algorithms affect political polarization?", 
    "What are the key findings about climate change impacts on biodiversity?",
    "Compare different approaches to federated learning privacy",
    "What evidence exists for the effectiveness of remote learning?"
]

for query in test_queries:
    response = await search_literature(query)
    # Validate:
    # - Citations present and properly formatted
    # - Academic writing style
    # - Evidence-based claims
    # - Page number attributions
    # - Response length appropriate (>200 words)
```

**Success Criteria**:
- [ ] All test queries return academic-quality answers
- [ ] Citations include page numbers and proper formatting
- [ ] Response time <15 seconds for typical queries
- [ ] No errors with 20+ document library
- [ ] Concurrent queries handled gracefully
- [ ] Memory usage remains <4GB during heavy use

---

## Implementation Timeline

### Day 1-2: Component Testing
- [ ] Set up PaperQA2 development environment
- [ ] Test with academic PDF collection (10+ papers)
- [ ] Benchmark embedding models (OpenAI vs Voyage vs Gemini)
- [ ] Build and test basic MCP server skeleton
- [ ] Validate Claude Desktop MCP integration

### Day 3-4: MCP Wrapper Development  
- [ ] Implement PaperQAMCPServer class
- [ ] Create tool wrappers for core functionality
- [ ] Add CLI integration (`paperqa mcp-server`)
- [ ] Write comprehensive error handling
- [ ] Create configuration system

### Day 5: Integration Testing
- [ ] End-to-end testing with Claude Desktop
- [ ] Academic workflow validation
- [ ] Performance testing and optimization
- [ ] Documentation and examples
- [ ] Prepare for open source contribution

### Day 6-7: Documentation & Polish
- [ ] Write usage documentation
- [ ] Create video demo of academic workflow
- [ ] Prepare GitHub issue/PR for PaperQA2 contribution
- [ ] Final testing and bug fixes

---

## Technical Requirements

### Dependencies
```toml
# Additional dependencies for MCP integration
[dependencies]
mcp-server = ">=1.0.0"
click = ">=8.0.0"  # For enhanced CLI
pathlib2 = ">=2.3.0"  # For robust path handling

[dev-dependencies]
pytest-asyncio = ">=0.21.0"
pytest-mock = ">=3.0.0"
```

### Environment Variables
```bash
# Required API keys
OPENAI_API_KEY=your-openai-key
VOYAGE_API_KEY=your-voyage-key  
GEMINI_API_KEY=your-gemini-key

# Optional configuration
PAPERQA_PAPER_DIRECTORY=~/research/papers
PAPERQA_EMBEDDING_MODEL=voyage-ai/voyage-3-lite
PAPERQA_LOG_LEVEL=INFO
```

### System Requirements
- Python 3.9+
- 4GB RAM minimum (8GB recommended for large libraries)
- 2GB disk space for indexes and embeddings
- Internet connection for API calls
- Claude Desktop installed and configured

---

## Success Metrics

### Functional Metrics
- [ ] **Library Management**: Successfully add/index 50+ academic PDFs
- [ ] **Search Quality**: >85% relevant results for academic queries
- [ ] **Citation Accuracy**: 100% accuracy in page/paragraph attribution  
- [ ] **Response Quality**: PhD-level academic writing with proper evidence
- [ ] **Performance**: <10 second response time for typical queries

### Technical Metrics  
- [ ] **Reliability**: 99%+ uptime during testing period
- [ ] **Error Handling**: Graceful degradation for all failure modes
- [ ] **Memory Efficiency**: <4GB usage with 50+ document library
- [ ] **Concurrency**: Handle 5+ simultaneous research queries
- [ ] **API Efficiency**: Optimize token usage and costs

### User Experience Metrics
- [ ] **Setup Time**: <15 minutes from clone to working system
- [ ] **Learning Curve**: PhD students productive within 30 minutes
- [ ] **Research Workflow**: Complete literature review tasks 3x faster
- [ ] **Citation Workflow**: Zero manual citation formatting needed
- [ ] **Integration**: Seamless experience within Claude Desktop

---

## Risk Mitigation

### Technical Risks
- **API Rate Limits**: Implement exponential backoff and usage monitoring
- **Memory Usage**: Add document pagination and lazy loading for large libraries  
- **PDF Processing**: Robust error handling for malformed academic PDFs
- **Embedding Costs**: Monitor usage and provide cost estimation tools

### Integration Risks
- **MCP Protocol Changes**: Pin MCP version and test compatibility
- **PaperQA2 Updates**: Fork at stable release, track upstream changes
- **Claude Desktop Updates**: Test with each Claude Desktop release
- **Dependency Conflicts**: Use virtual environment and lock file versions

### Academic Quality Risks
- **Citation Accuracy**: Implement validation and confidence scoring
- **Source Attribution**: Cross-reference all claims with source documents
- **Academic Style**: Validate writing style matches academic standards
- **Evidence Quality**: Filter low-quality or irrelevant evidence

---

## Future Enhancements (Post-MVP)

### Advanced Features
- [ ] **Multi-modal Support**: Images, figures, and tables in academic papers
- [ ] **Reference Manager Export**: Zotero, Mendeley, EndNote integration
- [ ] **Collaborative Research**: Shared libraries and annotations
- [ ] **Domain Specialization**: Custom prompts for different academic fields

### Performance Optimizations
- [ ] **Caching Layer**: Redis-based caching for frequent queries
- [ ] **Batch Processing**: Efficient handling of document uploads
- [ ] **Local Models**: Optional local LLM deployment for privacy
- [ ] **GPU Acceleration**: CUDA support for embedding generation

### Integration Expansions
- [ ] **Research Databases**: PubMed, arXiv, Google Scholar integration
- [ ] **Writing Tools**: LaTeX generation and academic writing assistance
- [ ] **Analysis Tools**: Statistical analysis and data visualization
- [ ] **Workflow Automation**: Systematic literature review pipelines

---

This PRD provides a comprehensive roadmap for building a production-ready academic research MCP server based on PaperQA2, with thorough testing at each phase and clear success criteria for academic quality assurance.