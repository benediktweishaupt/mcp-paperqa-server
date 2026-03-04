"""
Configuration settings for PaperQA2 MCP Server.
Optimized for scanned books and cultural theory texts.
"""

from pathlib import Path
from paperqa import Settings
from paperqa.settings import AgentSettings, IndexSettings, ParsingSettings, AnswerSettings


def get_paperqa_settings(base_dir: Path = None) -> Settings:
    """
    Get PaperQA2 settings optimized for scanned cultural/humanities books.

    Args:
        base_dir: Base directory for papers and cache (defaults to paperqa-mcp/)

    Returns:
        Configured Settings object
    """
    if base_dir is None:
        base_dir = Path(__file__).parent

    paper_directory = base_dir / "papers"
    cache_directory = base_dir / "cache"

    paper_directory.mkdir(exist_ok=True)
    cache_directory.mkdir(exist_ok=True)

    settings = Settings(
        # OpenAI embedding — works out of the box with existing API key
        # Switch to "voyage/voyage-3" for +7.5% quality + 32K context
        # (requires VOYAGE_API_KEY + payment method on Voyage dashboard)
        embedding="text-embedding-3-small",

        llm="gpt-4o-2024-11-20",
        temperature=0.0,

        # MMR diversity: 0.0 = max diversity, 1.0 = pure relevance (default)
        # 0.5 balances relevance with diversity across chapters/books
        texts_index_mmr_lambda=0.5,

        agent=AgentSettings(
            index=IndexSettings(
                paper_directory=paper_directory,
                index_directory=cache_directory / "index",
                sync_with_paper_directory=True,
            ),
            rebuild_index=False,
        ),

        # Tuned for scanned books with complex layouts
        parsing=ParsingSettings(
            # Books have longer arguments than papers — bigger chunks preserve flow
            reader_config={"chunk_chars": 6000, "overlap": 400},
            use_doc_details=False,  # No journal metadata for books
            # Multimodal disabled — image enrichment makes LLM calls per image,
            # which hits rate limits on low-tier OpenAI accounts.
            # Set to True when on a higher OpenAI tier.
            multimodal=False,
        ),

        answer=AnswerSettings(
            evidence_k=15,
            answer_max_sources=10,
            max_concurrent_requests=1,  # Low to avoid rate limits on low-tier OpenAI
            evidence_skip_summary=True,  # Direct quotes, no paraphrasing
        ),

        # Keep batch size low for rate limit safety
        batch_size=1,
    )

    return settings
