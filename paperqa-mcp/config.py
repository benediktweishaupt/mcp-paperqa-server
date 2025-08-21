"""
Configuration settings for PaperQA2 MCP Server
Extracted from main server file for easier management
"""

from pathlib import Path
from paperqa import Settings
from paperqa.settings import AgentSettings, IndexSettings, ParsingSettings, AnswerSettings


def get_paperqa_settings(base_dir: Path = None) -> Settings:
    """
    Get optimized PaperQA2 settings for academic research
    
    Args:
        base_dir: Base directory for papers and cache (defaults to current directory)
    
    Returns:
        Configured Settings object
    """
    if base_dir is None:
        base_dir = Path(__file__).parent
        
    paper_directory = base_dir / "papers"
    cache_directory = base_dir / "cache"
    
    # Ensure directories exist
    paper_directory.mkdir(exist_ok=True)
    cache_directory.mkdir(exist_ok=True)
    
    # PaperQA2 Settings optimized for academic content
    settings = Settings(
        # Use free local embedding model instead of paid Voyage AI
        embedding="text-embedding-3-small",  # OpenAI embedding that works with existing API keys
        
        # LLM Configuration
        llm="gpt-4o-2024-11-20",
        temperature=0.0,  # Deterministic for academic accuracy
        
        # Built-in index management (no custom caching needed)
        agent=AgentSettings(
            index=IndexSettings(
                paper_directory=paper_directory,
                index_directory=cache_directory / "index",
                sync_with_paper_directory=True,  # Auto-detect file changes
            ),
            rebuild_index=False  # Don't auto-rebuild unless explicitly requested
        ),
        
        # Academic-optimized parsing
        parsing=ParsingSettings(
            chunk_size=4000,  # Good balance for academic papers
            overlap=200,      # Sufficient context preservation
            use_doc_details=False,  # Skip external API calls to avoid SSL issues
        ),
        
        # Quality-focused answer generation
        answer=AnswerSettings(
            evidence_k=8,                    # More evidence for comprehensive answers
            answer_max_sources=5,            # Detailed source attribution
            max_concurrent_requests=2,       # Conservative for API limits
        )
    )
    
    return settings


def get_supported_embedding_models() -> list[str]:
    """Get list of validated embedding models"""
    return [
        "voyage/voyage-3-large",        # State-of-the-art (current default)
        "voyage/voyage-3.5",            # High performance alternative
        "voyage/voyage-3-lite",         # Budget option (6x cheaper than OpenAI)
        "voyage/voyage-3",              # Balanced performance/cost
        "gemini/text-embedding-004",    # Free Google option
        "text-embedding-3-large"        # OpenAI baseline
    ]


def get_model_info(model_name: str) -> str:
    """Get performance information for a specific model"""
    model_info = {
        "voyage/voyage-3-large": "State-of-the-art (+9.74% vs OpenAI, 2x cheaper)",
        "voyage/voyage-3.5": "High performance alternative",
        "voyage/voyage-3-lite": "Budget champion (6x cheaper than OpenAI)",
        "voyage/voyage-3": "Balanced option (+7.55% vs OpenAI, 2x cheaper)",
        "gemini/text-embedding-004": "Free but limited features",
        "text-embedding-3-large": "OpenAI baseline",
    }
    
    return model_info.get(model_name, "Unknown model")