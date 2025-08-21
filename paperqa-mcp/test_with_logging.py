#!/usr/bin/env python3
"""
Direct PaperQA request with detailed logging to compare with MCP
"""

import asyncio
import logging
from paperqa import Settings
from paperqa.agents.main import agent_query
from paperqa.agents.search import get_directory_index
from config import get_paperqa_settings

# Enable detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_with_logging():
    print('=== Direct PaperQA Request with Logging ===')
    
    settings = get_paperqa_settings()
    print(f'Settings: {settings.embedding}, {settings.llm}')
    
    print('Loading index...')
    built_index = await get_directory_index(settings=settings)
    
    print('Making query...')
    result = await agent_query(
        query='What does Hito Steyerl write about truth and representation?',
        settings=settings
    )
    
    print('=== RESULTS ===')
    print(f'Answer: {result.session.answer}')
    print(f'Sources: {len(result.session.contexts)}')
    print(f'Cost: ${result.session.cost:.4f}')
    
    print('\n=== SOURCES ===')
    for i, ctx in enumerate(result.session.contexts[:3], 1):
        print(f'{i}. {ctx.text.name} (score: {ctx.score})')

if __name__ == "__main__":
    asyncio.run(test_with_logging())