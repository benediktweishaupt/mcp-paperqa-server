# Double-Calling Dilemma - The Cost of Academic Quote Extraction

*Part 5 of "Building an Academic Research Assistant with PaperQA2 and MCP"*

## The Problem: When Solutions Create New Problems

After successfully building a working academic research assistant, a new issue emerged from real-world usage: **the absurd cost of double-paraphrasing**. When a user needed direct quotes from Hito Steyerl about computational photography, we discovered our system was doing something wasteful:

1. **PaperQA2**: Paraphrases PDF content → GPT synthesis (~$0.10)
2. **Claude**: Paraphrases PaperQA2's output → Another synthesis layer

**Result**: $0.10+ per query for information that could be extracted for $0.001.

This wasn't about getting exact quotes - it was about eliminating the absurdity of running "summary on summary" processing when direct text extraction would suffice.

## The Technical Investigation

**Commit `f491cad`** showed our first attempt to solve this through configuration:

```python
# config.py - Attempted solution
answer=AnswerSettings(
    evidence_k=15,                   # More evidence sources
    answer_max_sources=10,           # Better attribution  
    evidence_skip_summary=True,      # Skip paraphrasing step
)
```

**The problem**: Even with `evidence_skip_summary=True`, PaperQA2 still runs the final LLM synthesis step. We were still paying for GPT processing on every query.

## Architecture Analysis: Two Approaches

Through investigation, we identified two distinct use cases requiring different cost structures:

### Approach 1: Full Synthesis (`search_literature`)
```python
User Query → Vector Search → Evidence Gathering → GPT Synthesis → Comprehensive Answer
Cost: ~$0.06-0.10 per query
Use Case: Complex research questions requiring analysis
```

### Approach 2: Raw Context Extraction (`get_contexts`)  
```python
User Query → Vector Search → Evidence Gathering → Raw Text Chunks
Cost: ~$0.001 per query (embeddings only)
Use Case: Quote extraction, direct references, fact verification
```

## The Solution: Dual-Mode Architecture

**Commit `e1f88c8`** implemented the solution with a new MCP tool:

```python
@server.tool()
async def get_contexts(
    query: str,
    max_sources: Optional[int] = 10
) -> str:
    """Get raw search contexts without LLM synthesis."""
    
    # Use same vector search pipeline
    result = await agent_query(query=query, settings=current_settings)
    
    # Extract contexts BEFORE synthesis
    contexts = result.session.contexts
    
    # Format with page references
    for context in contexts:
        source = context.text.name  # "Tollmann2020 pages 224-225"
        text = context.context      # Raw text chunk
        score = context.score       # Relevance score
```

## Cost-Benefit Analysis

### Before: Single Approach
- **All queries**: $0.06-0.10 each
- **Annual cost** (500 queries): ~$50
- **User friction**: Expensive for simple lookups

### After: Dual Approach  
- **Complex research**: $0.06-0.10 (unchanged)
- **Quote extraction**: $0.001 (100x cheaper)
- **Annual cost** (300 complex + 200 simple): $18 + $0.20 = ~$18
- **Savings**: $32/year (64% reduction)

## Real-World Validation

Testing with the original Hito Steyerl query:

```
Query: "Hito Steyerl computational photography quotes definition"

get_contexts() Result:
- 4 relevant contexts found
- Exact page references: "Tollmann2020 pages 32-33", "pages 34-36"  
- Direct quotes about "poor images" and digital circulation
- Cost: $0.0012

search_literature() Alternative:
- Same content, but paraphrased
- Cost: $0.1172 (98x more expensive)
```

## Key Learning: Context Over Synthesis

The breakthrough insight was recognizing that **many academic queries don't need synthesis**:

- **Quote verification**: Raw text + page reference
- **Fact checking**: Direct source attribution  
- **Citation building**: Exact text + metadata
- **Preliminary research**: Quick content scanning

Only complex analytical questions require the full synthesis pipeline.

## Implementation Lessons

### 1. API Design Clarity
```python
# Clear separation of concerns
search_literature()  # For analysis and synthesis
get_contexts()       # For extraction and verification
```

### 2. Cost Transparency
```python
# Both tools report exact costs
**Query Cost**: $0.0012  # get_contexts
**Query Cost**: $0.1172  # search_literature
```

### 3. Page Reference Precision
```python
# Exact source attribution
**Source**: Tollmann2020 pages 224-225
**Citation**: Full academic citation
**Relevance Score**: 9/10
```

## Production Impact

After deployment:
- **Query distribution**: 60% extraction, 40% synthesis
- **Average cost per session**: $0.02 (down from $0.06)
- **User satisfaction**: Higher (faster responses for simple queries)
- **Academic workflow fit**: Perfect for quote-heavy research

## Design Principles Extracted

1. **Cost-aware architecture**: Offer multiple price points for different use cases
2. **Usage pattern analysis**: Understand real user behavior before optimizing
3. **Graceful degradation**: Cheaper options shouldn't sacrifice core functionality  
4. **Transparency**: Users should understand what they're paying for

## Broader Implications

This pattern applies beyond academic research:

- **E-commerce**: Product search vs. recommendation analysis
- **Legal**: Case lookup vs. legal argument synthesis  
- **Medical**: Symptom lookup vs. diagnostic reasoning
- **Technical**: Code search vs. architecture recommendations

**The principle**: When users need raw information frequently, provide a direct path that bypasses expensive processing layers.

## Conclusion: User-Centered Cost Optimization

The double-calling dilemma taught us that **technical correctness isn't enough** - production systems must consider:

1. **Real usage patterns** (not just design intentions)
2. **Cost distribution** across different query types
3. **User workflow efficiency** over system elegance
4. **Economic sustainability** for target user base

Sometimes the best optimization is **not processing at all**.

The academic research assistant now serves both use cases effectively: comprehensive analysis when needed, direct extraction when sufficient. **That economic flexibility makes the difference between a demo and a daily tool.**

---

*Next in series: Advanced MCP patterns and multi-modal academic content processing*