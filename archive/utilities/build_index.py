#!/usr/bin/env python3
"""
Build PaperQA2 Index Script
Pre-builds the search index for academic papers to avoid MCP server timeouts.
"""

import os
import sys
from pathlib import Path

def main():
    print("🚀 Building PaperQA2 index for MCP server...")
    
    # Get paths
    project_root = Path(__file__).parent
    papers_dir = project_root / "paperqa-mcp" / "papers"
    index_dir = project_root / "paperqa-mcp" / "cache" / "index"
    
    # Check if papers directory exists and has PDFs
    if not papers_dir.exists():
        print(f"❌ Papers directory not found: {papers_dir}")
        return 1
    
    pdf_files = list(papers_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ No PDF files found in: {papers_dir}")
        return 1
    
    print(f"📚 Found {len(pdf_files)} PDF files:")
    for pdf in pdf_files:
        print(f"  - {pdf.name}")
    
    # Create index directory if it doesn't exist
    index_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        from paperqa.agents import build_index
        from paperqa.settings import Settings
        print("✅ PaperQA2 modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import PaperQA2: {e}")
        print("💡 Make sure you're in the virtual environment: source venv/bin/activate")
        return 1
    
    # Create settings matching your MCP server configuration
    print("⚙️ Configuring PaperQA2 settings...")
    try:
        settings = Settings(
            embedding="text-embedding-3-small",  # Use OpenAI (more reliable rate limits)
            llm="gpt-4o-2024-11-20",             # Match your server config
            temperature=0.0,
            agent=Settings().agent.model_copy(update={
                "index": Settings().agent.index.model_copy(update={
                    "paper_directory": str(papers_dir),
                    "index_directory": str(index_dir),
                    "sync_with_paper_directory": True,
                    "recurse_subdirectories": True,
                    "concurrency": 1,  # Very conservative for rate limits
                    "batch_size": 1,
                })
            })
        )
        print("✅ Settings configured successfully")
    except Exception as e:
        print(f"❌ Failed to configure settings: {e}")
        return 1
    
    # Build the index
    print("\n🔨 Building index... This will take 5-15 minutes and cost ~$3-5")
    print("💡 Watch for API calls and progress messages...")
    
    try:
        # Import and check environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Verify API keys are available
        openai_key = os.getenv("OPENAI_API_KEY")
        voyage_key = os.getenv("VOYAGE_API_KEY")
        
        if not openai_key:
            print("⚠️  OPENAI_API_KEY not found in environment")
        else:
            print("✅ OpenAI API key loaded")
            
        if not voyage_key:
            print("⚠️  VOYAGE_API_KEY not found in environment")  
        else:
            print("✅ Voyage AI API key loaded")
        
        if not openai_key or not voyage_key:
            print("❌ Missing required API keys. Check your .env file")
            return 1
        
        # Build the index
        build_index(settings=settings)
        
        print("\n🎉 Index built successfully!")
        print(f"📁 Index saved to: {index_dir}")
        print("🚀 Your MCP server should now start instantly!")
        
        # Check if index files were created
        index_files = list(index_dir.glob("*"))
        if index_files:
            print(f"✅ Created {len(index_files)} index files:")
            for file in sorted(index_files)[:5]:  # Show first 5
                print(f"  - {file.name}")
            if len(index_files) > 5:
                print(f"  ... and {len(index_files) - 5} more files")
        else:
            print("⚠️  No index files found - something may have gone wrong")
        
        return 0
        
    except Exception as e:
        print(f"❌ Failed to build index: {e}")
        print("\n🔍 Troubleshooting tips:")
        print("- Check your API keys in .env file")
        print("- Ensure you have sufficient API credits")
        print("- Try running with fewer PDFs first")
        print("- Check internet connection")
        return 1

if __name__ == "__main__":
    sys.exit(main())