#!/usr/bin/env python3
"""Build PaperQA2 search index using shared config."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from config import get_paperqa_settings
from paperqa.agents.search import get_directory_index


async def main():
    settings = get_paperqa_settings()

    paper_dir = settings.agent.index.paper_directory
    papers = list(paper_dir.glob("*.pdf")) + list(paper_dir.glob("*.txt")) + list(paper_dir.glob("*.html"))

    if not papers:
        print(f"No documents found in {paper_dir}")
        sys.exit(1)

    print(f"Building index for {len(papers)} documents")
    print(f"  Paper dir: {paper_dir}")
    print(f"  Index dir: {settings.agent.index.index_directory}")
    print(f"  Embedding: {settings.embedding}")
    print(f"  Chunk size: {settings.parsing.reader_config.get('chunk_chars', 'default')}")
    print()

    # Force rebuild
    settings.agent.rebuild_index = True

    idx = await get_directory_index(settings=settings)
    files = await idx.index_files
    print(f"\nDone. Indexed {len(files)} files:")
    for name in files:
        print(f"  - {name}")


if __name__ == "__main__":
    asyncio.run(main())
