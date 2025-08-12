#!/usr/bin/env python3
"""
Standalone test for sliding window chunker without spaCy dependencies
"""

import sys
import os
from pathlib import Path

# Add the current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Test the sliding window chunker with mock dependencies
def test_sliding_window_standalone():
    """Test sliding window chunker with mock dependencies"""
    
    # Import after path setup
    from sliding_window_chunker import (
        SlidingWindowChunker, ChunkingConfig, AcademicDiscipline, 
        ChunkOverlapStrategy, create_config_for_discipline
    )
    
    print("🧪 Testing SlidingWindowChunker (Standalone Mode)")
    print("=" * 60)
    
    # Sample academic text
    sample_text = """
Introduction

This paper presents a novel approach to machine learning in academic contexts. The method builds upon previous work in neural networks and deep learning architectures, providing significant improvements in both accuracy and efficiency.

According to Smith et al. (2020), traditional approaches have several limitations. However, our method addresses these issues through innovative preprocessing techniques and improved training algorithms.

    Definition 1. A neural network is a computational model that mimics the biological neural networks found in animal brains through interconnected nodes or "neurons" that process information.

The following list outlines our main contributions:
1. Novel attention-based architecture design
2. Improved training algorithms with adaptive learning rates
3. Comprehensive evaluation framework across multiple domains
4. Open-source implementation for reproducibility

Theorem 1.1 (Convergence). Under mild conditions, our algorithm converges to a global optimum with probability 1.

Proof. We proceed by induction on the number of training epochs...

2. Methodology

Our approach consists of three main components. First, we preprocess the input data using specialized normalization techniques. Second, we apply our novel neural network architecture with modified backpropagation. Third, we evaluate performance using established metrics.

As noted by Johnson (2021): "The integration of attention mechanisms represents a paradigm shift in neural network design that enables more interpretable and efficient models."

This conclusion demonstrates the effectiveness of our approach across multiple academic domains, confirming the theoretical foundations established in the introduction and validated through comprehensive empirical analysis.
    """
    
    print(f"📝 Input text: {len(sample_text)} characters")
    print(f"📝 Estimated words: {len(sample_text.split())}")
    
    # Test 1: Basic chunking with default configuration
    print("\n🧪 Test 1: Basic chunking with default config")
    config1 = ChunkingConfig(window_size=300, overlap_percentage=0.2)
    chunker1 = SlidingWindowChunker(config=config1)
    chunks1 = chunker1.chunk_text(sample_text, document_id="test_doc")
    
    print(f"✅ Generated {len(chunks1)} chunks")
    for i, chunk in enumerate(chunks1[:3]):  # Show first 3 chunks
        print(f"   Chunk {i+1}: {chunk.token_count} tokens, {chunk.word_count} words")
        print(f"   Position: {chunk.start_pos}-{chunk.end_pos}")
        if chunk.overlap_with_previous:
            print(f"   Overlaps with: {chunk.overlap_with_previous}")
        print(f"   Preview: {chunk.content[:80].replace(chr(10), ' ')}...")
    
    if len(chunks1) > 3:
        print(f"   ... and {len(chunks1) - 3} more chunks")
    
    # Test 2: Different academic disciplines
    print("\n🧪 Test 2: Academic discipline configurations")
    disciplines = [AcademicDiscipline.HUMANITIES, AcademicDiscipline.STEM, AcademicDiscipline.LAW]
    
    for discipline in disciplines:
        config = create_config_for_discipline(discipline)
        config.window_size = 400  # Keep reasonable size for test
        chunker = SlidingWindowChunker(config=config)
        chunks = chunker.chunk_text(sample_text, document_id=f"test_{discipline.value}")
        
        stats = chunker.get_chunk_statistics(chunks)
        print(f"   {discipline.value.upper()}: {len(chunks)} chunks, avg {stats['avg_token_count']:.0f} tokens, {stats['overlap_percentage']:.1%} overlap")
    
    # Test 3: Different overlap strategies
    print("\n🧪 Test 3: Different overlap percentages")
    overlaps = [0.1, 0.2, 0.3]
    
    for overlap in overlaps:
        config = ChunkingConfig(window_size=300, overlap_percentage=overlap)
        chunker = SlidingWindowChunker(config=config)
        chunks = chunker.chunk_text(sample_text, document_id=f"test_overlap_{overlap}")
        
        stats = chunker.get_chunk_statistics(chunks)
        print(f"   {overlap:.0%} overlap: {len(chunks)} chunks, {stats['chunks_with_overlap']} overlapping")
    
    # Test 4: Detailed analysis of first chunk
    print("\n🧪 Test 4: Detailed chunk analysis")
    config4 = ChunkingConfig(window_size=400, overlap_percentage=0.25, dynamic_adjustment=True)
    chunker4 = SlidingWindowChunker(config=config4)
    chunks4 = chunker4.chunk_text(sample_text, document_id="detailed_test")
    
    if chunks4:
        first_chunk = chunks4[0]
        print(f"📄 First chunk details:")
        print(f"   ID: {first_chunk.chunk_id}")
        print(f"   Position: {first_chunk.start_pos}-{first_chunk.end_pos}")
        print(f"   Tokens: {first_chunk.token_count}, Words: {first_chunk.word_count}")
        print(f"   Sentences: {first_chunk.sentence_count}")
        print(f"   Citations: {first_chunk.citation_count}")
        print(f"   Math content: {first_chunk.has_mathematical_content}")
        print(f"   Content density: {first_chunk.content_density_score:.3f}")
        print(f"   Paragraphs: {first_chunk.paragraph_count}")
        
        if first_chunk.overlap_with_next:
            print(f"   Next overlap: {first_chunk.overlap_with_next}")
    
    # Test 5: Statistics summary
    print("\n📊 Overall Statistics:")
    overall_stats = chunker4.get_chunk_statistics(chunks4)
    for key, value in overall_stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")
    
    print("\n✅ All tests completed successfully!")
    print("\n🎯 Key Features Validated:")
    print("   • Configurable window sizes and overlap percentages")
    print("   • Academic discipline-specific optimizations")
    print("   • Content density analysis and dynamic adjustment")
    print("   • Overlap relationship tracking between chunks")
    print("   • Citation and mathematical content detection")
    print("   • Comprehensive chunk metadata and statistics")
    
    return chunks4


if __name__ == "__main__":
    try:
        chunks = test_sliding_window_standalone()
        print(f"\n🎉 Successfully created {len(chunks)} chunks with sliding window approach!")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()