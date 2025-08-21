# From Custom RAG to PaperQA2 - The Architecture Pivot

*Part 1 of "Building an Academic Research Assistant with PaperQA2 and MCP"*

## The Problem That Started Everything

PhD students spend 40-60% of their research time on literature search and management, yet existing tools fail at the most critical task: **understanding academic content semantically**. Traditional reference managers like Zotero excel at organizing citations but can't answer questions like "What contradictions exist between different authors on systemic boundaries?"

This is the story of building an AI-powered research assistant that transforms scattered PDFs into conversational academic insights - and why the biggest lesson was **not building it from scratch**.

## Initial Vision: The Custom RAG Approach

**Commit `f12d8fa`** marked the beginning with ambitious goals: a custom-built Retrieval-Augmented Generation system specifically designed for academic workflows. The plan was comprehensive:

```python
# Original architecture concept
TypeScript MCP Server → Python Bridge → Custom RAG Engine
                                    ↓
Custom PDF Parser → Custom Embeddings → Custom Vector Store → Custom Citation Engine
```

The reasoning seemed sound: academic papers have unique formatting, citation requirements, and quality standards that general-purpose tools might miss. We'd build everything from scratch, optimized for PhD-level research.

**Three weeks and 500+ lines later, we had a working prototype with concerning complexity.**

## The Discovery: PaperQA2 Analysis

**Commit `102f696`** introduced a monorepo structure, but more importantly, triggered deep research into existing solutions. During this analysis phase, we discovered **PaperQA2** - a production-ready academic RAG system that solved exactly our problems.

The analysis revealed shocking overlap:

| Our Custom Requirements | PaperQA2 Built-in Features | Match % |
|------------------------|----------------------------|---------|
| Academic PDF processing | PyMuPDF with publisher optimization | 95% |
| Citation management | Journal quality scoring, metadata extraction | 90% |
| Multi-step reasoning | Agent workflow with evidence gathering | 95% |
| Embedding flexibility | LiteLLM with all major providers | 100% |

**The realization hit: We were rebuilding a production-ready system that already existed.**

## The Pivot Decision

**Commit `7a9c003`** showed our first attempt at a TypeScript MCP foundation - technically sound but fundamentally misguided. We were solving a solved problem.

The pivot came from a simple question: *"What if we just wrapped PaperQA2 in an MCP server?"*

**Commit `efa836b`** marked the turning point: "feat: implement lean PaperQA2 MCP server." This single commit replaced weeks of custom development with:

```python
# The entire MCP server foundation
from paperqa.agents.main import agent_query
from mcp.server.fastmcp import FastMCP

@server.tool()
async def search_literature(query: str) -> str:
    result = await agent_query(query=query, settings=settings)
    return result.session.answer
```

**256 lines. Production-ready. Full academic RAG functionality.**

## Architecture Comparison

### Before: Custom Everything
- **Lines of code**: 500+ and growing
- **Dependencies**: 15+ custom modules  
- **Maintenance**: Every feature built and maintained by us
- **Testing**: Custom test suite for every component
- **Documentation**: Everything from scratch

### After: PaperQA2 Integration  
- **Lines of code**: 256 total
- **Dependencies**: 1 primary (PaperQA2)
- **Maintenance**: Focus on MCP integration only
- **Testing**: Test integration, not reimplemented features
- **Documentation**: Usage-focused, not implementation details

## Key Technical Insights

### 1. The "Build vs Buy" Framework
When evaluating whether to build custom vs integrate existing:

**Build Custom If**:
- No existing solution covers >60% of requirements
- Unique constraints require novel approaches
- Learning/research is primary goal

**Integrate Existing If**:
- Existing solution covers >80% of requirements  
- Production readiness matters more than customization
- Time-to-value is critical

**PaperQA2 scored 90%+ on our requirements.**

### 2. Complexity Debt Accumulates Fast
Our custom approach grew from "simple wrapper" to complex system:
- Week 1: Basic PDF parsing (looks manageable)
- Week 2: Citation extraction + metadata (getting complex)
- Week 3: Vector search + embeddings (now we're rebuilding scientific infrastructure)

**The complexity trajectory was unsustainable.**

### 3. Integration > Implementation for Academic Tools
Academic research has solved problems:
- **Citation formatting**: BibTeX, CSL have decades of edge cases solved
- **PDF parsing**: Academic publishers have specific formatting quirks
- **Evidence synthesis**: Multi-step reasoning patterns are well-established

**PaperQA2 encoded this domain knowledge. Our custom approach would need years to match it.**

## Lessons Learned

### ❌ What Went Wrong

**1. "Not Invented Here" Syndrome**
- Assumed academic domain was too specialized for existing tools
- Underestimated maturity of academic RAG solutions
- Conflated "custom requirements" with "need custom implementation"

**2. Premature Optimization**
- Started with TypeScript for "performance" before measuring bottlenecks
- Designed complex bridge architecture before validating simple approaches
- Optimized for theoretical scale before proving core concept

**3. Feature Creep Before Foundation**
- Added embedding model selection before basic search worked
- Implemented caching systems before understanding storage patterns
- Built configuration complexity before settling on core functionality

### ✅ What Went Right

**1. Systematic Tool Evaluation**
- Comprehensive analysis documented in `PAPERQA2_ANALYSIS.md`
- Feature-by-feature comparison with requirements
- Evidence-based decision making with clear criteria

**2. Clean Pivot Execution**
- Archived failed approaches instead of gradual refactoring
- Started fresh with lessons learned applied
- Maintained git history for learning retrospectives

**3. Focus on Integration Quality**
- Deep dive into PaperQA2 API patterns
- MCP protocol compliance over custom features
- Production-ready error handling and logging

## What We'd Do Differently

### 1. Research Phase First
**Timeline**: Spend 20% of project time on tool evaluation
- Survey existing solutions systematically
- Build integration prototypes before custom code
- Measure gap between existing tools and requirements

### 2. Complexity Budget
**Rule**: Justify every line over 300 in core system
- Simple solutions beat complex ones 90% of the time
- Maintenance burden grows exponentially with complexity
- Academic users prefer reliability over customization

### 3. Domain Knowledge Acquisition
**Strategy**: Learn from existing academic tooling
- Academic software has decades of edge case handling
- Citation standards are complex and constantly evolving
- PDF parsing quirks vary by publisher and era

### 4. Integration-First Development
**Approach**: Wrap existing tools, don't reimplement
- Focus expertise on unique value (MCP integration)
- Leverage domain experts' work (PaperQA2 team)
- Contribute back to ecosystem instead of fragmenting it

## The Bottom Line

The architecture pivot from custom RAG to PaperQA2 integration taught us the most valuable lesson in academic tool development: **The smartest code is often the code you don't write.**

PaperQA2 represented thousands of hours of academic domain expertise, battle-tested with real researchers, and actively maintained by a dedicated team. Our custom approach, no matter how well-intentioned, couldn't compete with that foundation.

**The result? A production-ready academic research assistant in 256 lines instead of the 2000+ we were heading toward.**

In the next article, we'll dive into the data pipeline challenges that even PaperQA2 couldn't solve for us: OCR processing for scanned academic papers and the embedding model optimization that saved us 6x on API costs.

---

*Continue to [Part 2: OCR, Embeddings, and Academic Content - The Data Pipeline](article-2-data-pipeline.md)*