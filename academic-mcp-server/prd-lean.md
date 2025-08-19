# Academic Research Assistant - Lean MVP for 3-Day Delivery

## Executive Summary

**Goal**: Working MCP server for academic literature search in 3 days using proven frameworks + our existing academic processing.

**Approach**: KISS (Keep It Simple, Stupid) + LEAN principles with pluggable architecture for easy component swapping.

**Target**: PhD students can search across 10-20 PDFs with natural language queries through Claude Desktop.

## Core Value Proposition

- **Primary**: Natural language search across academic PDFs via Claude
- **Secondary**: Basic citation extraction and source attribution
- **Tertiary**: Document structure preservation (leverage existing work)

## Pluggable Architecture Design

### Core Principle: Interface-Based Components

Each component implements a standard interface, allowing easy swapping without breaking the system.

```python
# Abstract interfaces for pluggability
class DocumentProcessor(ABC):
    def extract_text(self, pdf_path: str) -> Document: pass

class TextChunker(ABC):
    def chunk_text(self, text: str) -> List[Chunk]: pass

class VectorStore(ABC):
    def add_documents(self, chunks: List[Chunk]): pass
    def search(self, query: str) -> List[Result]: pass
```

### Foundation Stack (Research-Optimized)

**Document Processing** (Pluggable):

- **Primary**: `PyMuPDF` - Superior academic PDF processing (42ms vs 2.5s, better layout handling)
- **Fallback**: `LangChain PyPDFLoader` - Integration ease
- **Enhancement**: Our existing multi-column + citation detection

**Text Chunking** (Hybrid Approach):

- **Base**: `LangChain RecursiveCharacterTextSplitter` - Proven foundation
- **Enhancement**: Our existing paragraph preservation + academic patterns
- **Academic**: Citation-aware splitting, preserve "et al." patterns

**Embeddings** (API vs Local Choice):

- **MVP**: `OpenAI text-embedding-3-small` - Fast, high-quality, zero setup
- **Production**: `OpenAI text-embedding-3-large` - Best-in-class academic understanding
- **Privacy**: `sentence-transformers all-mpnet-base-v2` - Local option for sensitive research

**Vector Storage** (Prototyping to Production):

- **MVP**: `Chroma` - Production-ready, easy prototyping
- **Future**: `FAISS` with custom wrappers - Maximum performance
- **Production**: `Qdrant` - 4x performance gains (2025 leader)

**MCP Server Foundation**:

- `@modelcontextprotocol/sdk` - Standard MCP implementation
- Pluggable tool architecture

### Core Features (MVP)

#### 1. Literature Search Tool

```python
@mcp_tool
def search_literature(query: str, max_results: int = 5) -> SearchResults:
    """Search across all indexed academic documents"""
    # LangChain retrieval with academic context
```

#### 2. Document Upload Tool

```python
@mcp_tool
def add_document(pdf_path: str) -> DocumentInfo:
    """Add new PDF to the searchable library"""
    # PyPDFLoader + chunking + FAISS indexing
```

#### 3. Citation Extraction Tool

```python
@mcp_tool
def get_citation(document_id: str, page: int) -> Citation:
    """Extract formatted citation for a document"""
    # Basic metadata extraction + formatting
```

### Academic Enhancements (Leverage Existing Work)

**PyMuPDF Academic Processor** (REUSE from Task 2):

- Multi-column layout detection and handling
- Academic publisher format recognition (IEEE, ACM, Springer)
- Footnote/endnote extraction and linking
- Mathematical content and equation detection

**Enhanced Text Splitter** (REUSE + Extend):

- Our existing paragraph boundary detection (Task 3.2)
- Academic abbreviation preservation: "et al.", "i.e.", "e.g.", "cf."
- Citation-aware chunking (don't split citations from context)
- Section header detection and preservation

**Academic Pattern Recognition** (REUSE from existing):

- Citation patterns: `(Author, Year)`, `[Number]`, `Author et al.`
- Academic structure detection: theorems, definitions, proofs
- Section header patterns: `# Section`, numbered patterns, LaTeX commands
- Author/year metadata extraction from PDF headers

**Smart Retrieval** (Simple but Effective):

- Metadata filtering by document, author, year, section
- Context expansion (surrounding paragraphs + citations)
- Source attribution with exact page + paragraph numbers
- Confidence scoring for result relevance

## 3-Day Development Plan (Leveraging Existing Work)

### Day 1: Foundation + Integration (60% Time Savings)

**Morning (3h)** - REUSE Existing Components:

- ✅ **MCP Server**: Already built and tested (Task 1)
- ✅ **PyMuPDF Processing**: Integrate existing academic PDF processor
- 🔧 **Quick Setup**: Chroma vector store + sentence-transformers

**Afternoon (3h)** - Core Pipeline:

- 🔧 **Text Chunking**: Enhance RecursiveCharacterTextSplitter with our academic patterns
- 🔧 **Embedding Pipeline**: all-MiniLM-L6-v2 integration
- ✅ **End-to-End Test**: Load PDF → chunk → embed → search

**Success Criteria**: Our existing PDF processor + new retrieval pipeline working

### Day 2: MCP Tools + Academic Features (Reuse Focus)

**Morning (3h)** - Tool Implementation:

- 🔧 **Literature Search Tool**: Chroma retrieval + our citation patterns
- 🔧 **Document Upload Tool**: PyMuPDF processor + chunking pipeline
- ✅ **Claude Desktop**: Test MCP integration (already working)

**Afternoon (3h)** - Academic Intelligence:

- ✅ **Citation Extraction**: Reuse existing regex patterns and metadata extraction
- ✅ **Source Attribution**: Leverage existing page/paragraph tracking
- 🔧 **Context Enhancement**: Add surrounding paragraph retrieval

**Success Criteria**: Claude can search across multiple PDFs with proper citations

### Day 3: Polish + Production Ready (Quality Focus)

**Morning (3h)** - Academic Optimization:

- 🔧 **Academic Text Processing**: Fine-tune chunking with our existing patterns
- ✅ **Multi-Column Layout**: Already handled by PyMuPDF processor
- 🔧 **Performance Tuning**: Optimize embedding and search speed

**Afternoon (3h)** - Testing + Deployment:

- 🔧 **Real Academic PDFs**: Test with diverse academic papers
- 🔧 **Error Handling**: Robust fallbacks and validation
- 📚 **Documentation**: Deployment guide and usage examples

**Success Criteria**: Production-ready system that PhD students can use immediately

### Component Reuse Map

- ✅ **100% Reuse**: MCP server, PDF processing, citation patterns, academic structure detection
- 🔧 **50% Reuse**: Text chunking (enhance existing), paragraph detection (adapt)
- 🆕 **New**: Vector storage integration, embedding pipeline, retrieval tools

## Pluggable Technical Implementation

### Component-Based Architecture

```
academic-mcp-server/
├── src/
│   ├── server.py                    # MCP server (REUSE from Task 1)
│   ├── interfaces/                  # Abstract interfaces for pluggability
│   │   ├── document_processor.py    # PDF processing interface
│   │   ├── text_chunker.py          # Text splitting interface
│   │   ├── vector_store.py          # Vector storage interface
│   │   └── embedder.py              # Embedding interface
│   ├── tools/                       # MCP tools (pluggable)
│   │   ├── search.py                # Literature search tool
│   │   ├── upload.py                # Document upload tool
│   │   └── citation.py              # Citation extraction tool
│   ├── processors/                  # Pluggable document processors
│   │   ├── pymupdf_processor.py     # Primary: PyMuPDF (REUSE Task 2)
│   │   └── langchain_processor.py   # Fallback: LangChain PyPDFLoader
│   ├── chunkers/                    # Pluggable text chunkers
│   │   ├── academic_chunker.py      # Enhanced RecursiveCharacterTextSplitter
│   │   └── paragraph_chunker.py     # REUSE from Task 3.2
│   ├── vectorstores/                # Pluggable vector stores
│   │   ├── chroma_store.py          # MVP: Chroma
│   │   ├── faiss_store.py           # Future: FAISS
│   │   └── qdrant_store.py          # Production: Qdrant
│   ├── embedders/                   # Pluggable embedding models
│   │   ├── openai_embedder.py       # Primary: OpenAI text-embedding-3-small/large
│   │   └── sentence_transformers_embedder.py # Local: all-mpnet-base-v2
│   └── utils/                       # Shared utilities (REUSE existing)
│       ├── citations.py             # Citation parsing (REUSE)
│       ├── academic_patterns.py     # Academic structure detection (REUSE)
│       └── metadata.py              # Document metadata (REUSE)
├── config/
│   ├── development.yaml             # Dev configuration
│   ├── production.yaml              # Production configuration
│   └── components.yaml              # Component selection configuration
├── tests/
├── requirements/
│   ├── base.txt                     # Core dependencies
│   ├── dev.txt                      # Development dependencies
│   └── optional.txt                 # Optional component dependencies
└── README.md
```

### Pluggable Dependencies (Component Selection)

```yaml
# config/components.yaml - Easy component swapping
document_processor: 'pymupdf' # or "langchain"
text_chunker: 'academic' # or "paragraph"
vector_store: 'chroma' # or "faiss" or "qdrant"
embedder: 'openai-small' # or "openai-large" or "sentence-transformers"
```

### Core Dependencies (Minimal + Pluggable)

```
# Base requirements
@modelcontextprotocol/sdk>=1.0.0
openai>=1.0.0                     # Primary: OpenAI embeddings API
pymupdf>=1.23.0                   # Superior PDF processing
chromadb>=0.4.0                   # Easy vector storage

# Pluggable Framework Support
langchain>=0.1.0                  # Optional: fallback PDF processing
langchain-community>=0.0.10       # Optional: additional loaders
faiss-cpu>=1.7.4                  # Optional: performance vector storage
sentence-transformers>=2.2.2      # Optional: local embeddings

# Academic Processing (REUSE our existing work)
spacy>=3.7.0                      # Optional: NLP pipeline
scikit-learn>=1.3.0               # Optional: TF-IDF, similarity
```

### Interface-Based Component Design

**DocumentProcessor Interface**:

```python
from abc import ABC, abstractmethod

class DocumentProcessor(ABC):
    @abstractmethod
    def extract_text(self, pdf_path: str) -> Document:
        """Extract text and metadata from PDF"""
        pass

    @abstractmethod
    def get_page_info(self, pdf_path: str) -> List[PageInfo]:
        """Get page-level information for attribution"""
        pass

# Implementations: PyMuPDFProcessor, LangChainProcessor
```

**TextChunker Interface**:

```python
class TextChunker(ABC):
    @abstractmethod
    def chunk_text(self, document: Document) -> List[Chunk]:
        """Split text into semantically coherent chunks"""
        pass

# Implementations: AcademicChunker, ParagraphChunker
```

**VectorStore Interface**:

```python
class VectorStore(ABC):
    @abstractmethod
    def add_documents(self, chunks: List[Chunk]) -> None:
        """Add document chunks to vector store"""
        pass

    @abstractmethod
    def search(self, query: str, k: int = 5) -> List[SearchResult]:
        """Search for similar chunks"""
        pass

# Implementations: ChromaStore, FAISSStore, QdrantStore
```

### Component Factory (Easy Swapping)

```python
class ComponentFactory:
    @staticmethod
    def create_processor(config: dict) -> DocumentProcessor:
        processor_type = config.get('document_processor', 'pymupdf')
        if processor_type == 'pymupdf':
            return PyMuPDFProcessor()  # REUSE Task 2
        elif processor_type == 'langchain':
            return LangChainProcessor()
        else:
            raise ValueError(f"Unknown processor: {processor_type}")

    @staticmethod
    def create_embedder(config: dict) -> Embedder:
        embedder_type = config.get('embedder', 'openai-small')
        if embedder_type == 'openai-small':
            return OpenAIEmbedder(model="text-embedding-3-small")
        elif embedder_type == 'openai-large':
            return OpenAIEmbedder(model="text-embedding-3-large")
        elif embedder_type == 'sentence-transformers':
            return SentenceTransformersEmbedder(model="all-mpnet-base-v2")
        else:
            raise ValueError(f"Unknown embedder: {embedder_type}")

    # Similar factories for chunker, vector_store
```

### OpenAI Embedder Implementation

```python
class OpenAIEmbedder(Embedder):
    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [embedding.embedding for embedding in response.data]

    def embed_query(self, query: str) -> List[float]:
        return self.embed_texts([query])[0]
```

### Cost Optimization Strategies

```python
class CostOptimizedEmbedder(Embedder):
    """Automatically falls back to local models if costs exceed thresholds"""

    def __init__(self, monthly_budget: float = 100.0):
        self.monthly_budget = monthly_budget
        self.current_usage = 0.0
        self.primary = OpenAIEmbedder("text-embedding-3-small")
        self.fallback = SentenceTransformersEmbedder()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        estimated_cost = len(' '.join(texts)) * 0.00002 / 1000

        if self.current_usage + estimated_cost > self.monthly_budget:
            logger.warning("Switching to local embeddings due to budget")
            return self.fallback.embed_texts(texts)

        self.current_usage += estimated_cost
        return self.primary.embed_texts(texts)
```

## Quality Assurance

### Testing Strategy

- **Unit Tests**: Each tool and component
- **Integration Tests**: Full MCP workflow
- **Academic Tests**: Real PhD paper samples
- **Performance Tests**: 20+ PDF library

### Success Metrics (LEAN KPIs)

- **Speed**: Search response time <3 seconds (leverage PyMuPDF 42ms advantage)
- **Relevance**: 80%+ useful results on 10 academic test queries
- **Accuracy**: 95%+ correct page attribution (leverage existing PDF processing)
- **Stability**: 100 consecutive queries without crashes
- **Usability**: PhD student finds relevant passage in <30 seconds

## LEAN Risk Mitigation

### Technical Risks (Pluggable Solutions)

- **PDF parsing failures**: PyMuPDF primary + LangChain fallback via interfaces
- **Vector store performance**: Start Chroma → swap to FAISS/Qdrant via config
- **Embedding dependency**: OpenAI API primary + sentence-transformers local fallback
- **API costs/limits**: Monitor OpenAI usage + automatic fallback to local models
- **Memory issues**: Component-level limits + efficient chunking strategies

### Architecture Risks (KISS Approach)

- **Over-abstraction**: Only abstract what we know will change (PDF, vector store, embeddings)
- **Component coupling**: Clear interfaces prevent lock-in to specific implementations
- **Configuration complexity**: Simple YAML-based component selection
- **Testing complexity**: Interface-based testing + component-specific unit tests

### Scope Risks (LEAN Focus)

- **Feature creep**: Implement only 3 MCP tools (search, upload, citation)
- **Perfect vs working**: 80% solution that works > 100% solution that doesn't exist
- **Complex chunking**: Start with enhanced RecursiveCharacterTextSplitter + our patterns

## Success Criteria

### Minimum Viable Product

1. Upload 10+ academic PDFs
2. Natural language search through Claude Desktop
3. Results include source attribution (document + page)
4. Basic citation formatting
5. Stable for 30-minute demo session

### Quality Indicators

- PhD student can find relevant passages in <30 seconds
- Results include sufficient context to be useful
- No crashes during normal usage
- Citations traceable to source documents

## Evolutionary Upgrade Path (Pluggable Components Enable Easy Enhancement)

### Phase 2: Performance Optimization (Easy Component Swaps)

- **Vector Store**: Chroma → FAISS (5-10x speed with GPU)
- **Embeddings**: OpenAI text-embedding-3-small → text-embedding-3-large (better accuracy)
- **Chunking**: Enhanced RecursiveCharacterTextSplitter → Our advanced argument detection

### Phase 3: Advanced Academic Features (Reuse Existing Work)

- **Argument Detection**: Integrate our existing ArgumentAnalyzer (Task 3.3)
- **Breakpoint Detection**: Add our existing BreakpointDetector (Task 3.5)
- **Advanced Citations**: Reference manager export, multiple formats
- **Cross-Reference Resolution**: "see Chapter 2" linking

### Phase 4: Production Scale (Component Replacement)

- **Vector Store**: FAISS → Qdrant (4x performance gains)
- **Processing**: Single-document → Batch processing pipeline
- **Storage**: Local files → Production database
- **Deployment**: Local → Cloud deployment

### Pluggable Architecture Benefits

- ✅ **No rewrites**: Swap components via configuration
- ✅ **Risk reduction**: Test new components alongside existing ones
- ✅ **Performance tuning**: Upgrade bottlenecks individually
- ✅ **Future-proof**: Add new vector stores, embeddings, processors easily

---

## LEAN + KISS Philosophy

**This approach prioritizes:**

- ✅ **Working over perfect**: 80% solution that PhD students can use today
- ✅ **Proven over innovative**: Battle-tested frameworks + our academic domain expertise
- ✅ **Pluggable over monolithic**: Easy upgrades without system rewrites
- ✅ **Reuse over rebuild**: Leverage 60% of existing work from Tasks 1-3

**The goal**: Functional academic search tool in 3 days that can evolve into a production system without architectural rewrites.
