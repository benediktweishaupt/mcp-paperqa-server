#!/usr/bin/env python3
"""
Demo sliding window chunker - Simplified version without spaCy dependencies
"""

import re
from typing import List, Dict, Optional, Tuple, Set, Any
from dataclasses import dataclass
from enum import Enum


class ChunkOverlapStrategy(Enum):
    """Strategies for handling chunk overlaps"""
    SENTENCE_BOUNDARY = "sentence_boundary"
    PARAGRAPH_BOUNDARY = "paragraph_boundary"
    FIXED_PERCENTAGE = "fixed_percentage"


class AcademicDiscipline(Enum):
    """Academic disciplines with different chunking parameters"""
    GENERAL = "general"
    HUMANITIES = "humanities"
    SOCIAL_SCIENCES = "social_sciences"
    STEM = "stem"
    LAW = "law"
    PHILOSOPHY = "philosophy"


@dataclass
class ChunkingConfig:
    """Configuration parameters for sliding window chunking"""
    window_size: int = 1000
    min_window_size: int = 500
    max_window_size: int = 2000
    overlap_percentage: float = 0.2
    min_overlap_percentage: float = 0.1
    max_overlap_percentage: float = 0.3
    
    overlap_strategy: ChunkOverlapStrategy = ChunkOverlapStrategy.SENTENCE_BOUNDARY
    preserve_paragraphs: bool = True
    preserve_sentences: bool = True
    dynamic_adjustment: bool = True
    
    high_density_threshold: float = 0.8
    low_density_threshold: float = 0.3
    
    discipline: AcademicDiscipline = AcademicDiscipline.GENERAL


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata"""
    content: str
    start_pos: int
    end_pos: int
    chunk_id: str
    sequence_number: int
    
    token_count: int
    word_count: int
    
    overlap_with_previous: Optional[str] = None
    overlap_with_next: Optional[str] = None
    overlap_start: Optional[int] = None
    overlap_end: Optional[int] = None
    
    paragraph_count: int = 0
    sentence_count: int = 0
    citation_count: int = 0
    has_mathematical_content: bool = False
    content_density_score: float = 0.0
    
    contains_paragraphs: List[str] = None
    parent_document_id: Optional[str] = None
    
    def __post_init__(self):
        if self.contains_paragraphs is None:
            self.contains_paragraphs = []


class SimpleSlidingWindowChunker:
    """
    Simplified sliding window text chunker without spaCy dependencies
    
    Demonstrates core sliding window functionality for Task 3.4
    """
    
    def __init__(self, config: Optional[ChunkingConfig] = None):
        self.config = config if config else ChunkingConfig()
        
        # Load discipline-specific configurations
        self.discipline_configs = {
            AcademicDiscipline.GENERAL: {
                'preferred_window_size': 1000,
                'overlap_percentage': 0.2,
                'density_adjustment_factor': 1.0
            },
            AcademicDiscipline.HUMANITIES: {
                'preferred_window_size': 1200,
                'overlap_percentage': 0.25,
                'density_adjustment_factor': 1.2
            },
            AcademicDiscipline.STEM: {
                'preferred_window_size': 800,
                'overlap_percentage': 0.15,
                'density_adjustment_factor': 0.8
            },
            AcademicDiscipline.LAW: {
                'preferred_window_size': 1500,
                'overlap_percentage': 0.3,
                'density_adjustment_factor': 1.3
            },
            AcademicDiscipline.PHILOSOPHY: {
                'preferred_window_size': 1400,
                'overlap_percentage': 0.25,
                'density_adjustment_factor': 1.25
            }
        }
        
        print(f"🔧 SimpleSlidingWindowChunker initialized:")
        print(f"   Window size: {self.config.window_size} tokens")
        print(f"   Overlap: {self.config.overlap_percentage:.1%}")
        print(f"   Discipline: {self.config.discipline.value}")
    
    def chunk_text(self, text: str, document_id: Optional[str] = None) -> List[TextChunk]:
        """
        Chunk text using sliding window approach
        """
        if not text.strip():
            return []
        
        print(f"\n🪟 Chunking text of {len(text)} characters...")
        
        # Step 1: Calculate chunk boundaries
        boundaries = self._calculate_boundaries(text)
        print(f"📏 Calculated {len(boundaries)} boundaries")
        
        # Step 2: Create chunks with overlap
        chunks = self._create_chunks_with_overlap(text, boundaries, document_id)
        print(f"📝 Created {len(chunks)} chunks")
        
        # Step 3: Analyze content
        self._analyze_chunks(chunks)
        
        return chunks
    
    def _calculate_boundaries(self, text: str) -> List[int]:
        """Calculate chunk boundary positions"""
        text_length = len(text)
        if text_length == 0:
            return []
        
        # Convert token-based window size to character-based (rough approximation)
        chars_per_token = 4.5  # Average characters per token
        target_chunk_chars = int(self.config.window_size * chars_per_token)
        min_chunk_chars = int(self.config.min_window_size * chars_per_token)
        max_chunk_chars = int(self.config.max_window_size * chars_per_token)
        
        boundaries = []
        current_pos = 0
        
        while current_pos < text_length:
            # Calculate target end position
            target_end = current_pos + target_chunk_chars
            
            # Adjust for content density if enabled
            if self.config.dynamic_adjustment:
                target_end = self._adjust_for_content_density(text, current_pos, target_end)
            
            # Ensure we don't exceed text length
            target_end = min(target_end, text_length)
            
            # Find optimal boundary
            optimal_boundary = self._find_optimal_boundary(text, current_pos, target_end, min_chunk_chars, max_chunk_chars)
            
            if optimal_boundary > current_pos:
                boundaries.append(optimal_boundary)
                
                # Calculate overlap for next chunk
                overlap_size = int((optimal_boundary - current_pos) * self.config.overlap_percentage)
                current_pos = optimal_boundary - overlap_size
                
                # Ensure we advance sufficiently
                min_advance = int(target_chunk_chars * (1 - self.config.max_overlap_percentage))
                if len(boundaries) > 1:
                    current_pos = max(current_pos, boundaries[-2] + min_advance)
                current_pos = max(0, current_pos)
            else:
                # Advance by minimum amount if no good boundary found
                current_pos += min_chunk_chars
        
        # Ensure final boundary captures end of text
        if not boundaries or boundaries[-1] < text_length:
            boundaries.append(text_length)
        
        return boundaries
    
    def _adjust_for_content_density(self, text: str, start_pos: int, target_end: int) -> int:
        """Adjust chunk size based on content density"""
        chunk_text = text[start_pos:target_end]
        
        # Calculate density metrics
        citation_count = len(re.findall(r'\([^)]*\d{4}[^)]*\)|\[\d+\]', chunk_text))
        math_content = len(re.findall(r'[∀∃∈∉∪∩⊂⊃∑∏∫]|\$.*\$|\\\\.*\\\\', chunk_text))
        structure_markers = len(re.findall(r'\b(theorem|definition|proof|example|lemma)\b', chunk_text.lower()))
        
        text_length = len(chunk_text)
        if text_length == 0:
            return target_end
        
        # Density score (0.0 to 1.0)
        density_score = min(1.0, (citation_count * 10 + math_content * 15 + structure_markers * 20) / text_length)
        
        # Adjust based on discipline and density
        discipline_config = self.discipline_configs[self.config.discipline]
        adjustment_factor = discipline_config['density_adjustment_factor']
        
        if density_score > self.config.high_density_threshold:
            size_factor = 0.8 * adjustment_factor  # Smaller chunks for high density
        elif density_score < self.config.low_density_threshold:
            size_factor = 1.2 * adjustment_factor  # Larger chunks for low density
        else:
            size_factor = adjustment_factor
        
        adjusted_end = start_pos + int((target_end - start_pos) * size_factor)
        return min(adjusted_end, len(text))
    
    def _find_optimal_boundary(self, text: str, start_pos: int, target_end: int, min_chars: int, max_chars: int) -> int:
        """Find optimal boundary position"""
        search_window = 200
        search_start = max(start_pos + min_chars, target_end - search_window)
        search_end = min(len(text), target_end + search_window)
        
        # Priority 1: Double newlines (paragraph boundaries)
        if self.config.preserve_paragraphs:
            for match in re.finditer(r'\n\s*\n', text[search_start:search_end]):
                pos = search_start + match.end()
                if pos > start_pos + min_chars:
                    return pos
        
        # Priority 2: Sentence boundaries
        if self.config.preserve_sentences:
            sentence_ends = []
            for match in re.finditer(r'[.!?]+\s+', text[search_start:search_end]):
                pos = search_start + match.end()
                if pos > start_pos + min_chars:
                    sentence_ends.append(pos)
            
            if sentence_ends:
                return min(sentence_ends, key=lambda x: abs(x - target_end))
        
        # Priority 3: Line breaks
        for match in re.finditer(r'\n', text[search_start:search_end]):
            pos = search_start + match.end()
            if pos > start_pos + min_chars:
                return pos
        
        # Priority 4: Word boundaries
        for match in re.finditer(r'\s+', text[search_start:search_end]):
            pos = search_start + match.end()
            if pos > start_pos + min_chars:
                return pos
        
        # Fallback: target position
        return min(target_end, start_pos + max_chars)
    
    def _create_chunks_with_overlap(self, text: str, boundaries: List[int], document_id: Optional[str]) -> List[TextChunk]:
        """Create chunks with overlap information"""
        chunks = []
        
        for i, end_pos in enumerate(boundaries):
            # Calculate start position with overlap
            if i == 0:
                start_pos = 0
            else:
                prev_chunk_size = boundaries[i] - boundaries[i-1] if i > 0 else boundaries[i]
                overlap_size = int(prev_chunk_size * self.config.overlap_percentage)
                start_pos = boundaries[i-1] - overlap_size
                start_pos = max(0, start_pos)
            
            chunk_content = text[start_pos:end_pos].strip()
            if not chunk_content:
                continue
            
            chunk_id = f"{document_id or 'doc'}_{i:03d}" if document_id else f"chunk_{i:03d}"
            
            # Basic metrics
            token_count = len(re.findall(r'\b\w+\b', chunk_content))
            word_count = len(chunk_content.split())
            
            # Overlap information
            overlap_info = {}
            if i > 0 and start_pos < boundaries[i-1]:
                overlap_info['overlap_with_previous'] = f"{document_id or 'doc'}_{i-1:03d}"
                overlap_info['overlap_start'] = start_pos
                overlap_info['overlap_end'] = min(boundaries[i-1], end_pos)
            
            if i < len(boundaries) - 1:
                next_overlap_size = int((boundaries[i+1] - end_pos) * self.config.overlap_percentage) if i+1 < len(boundaries) else 0
                if next_overlap_size > 0:
                    overlap_info['overlap_with_next'] = f"{document_id or 'doc'}_{i+1:03d}"
            
            chunk = TextChunk(
                content=chunk_content,
                start_pos=start_pos,
                end_pos=end_pos,
                chunk_id=chunk_id,
                sequence_number=i,
                token_count=token_count,
                word_count=word_count,
                parent_document_id=document_id,
                **overlap_info
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _analyze_chunks(self, chunks: List[TextChunk]):
        """Analyze chunk content for metadata"""
        for chunk in chunks:
            # Count sentences
            chunk.sentence_count = len(re.findall(r'[.!?]+', chunk.content))
            
            # Count paragraphs (double newlines)
            chunk.paragraph_count = len(re.findall(r'\n\s*\n', chunk.content)) + 1
            
            # Count citations
            chunk.citation_count = len(re.findall(r'\([^)]*\d{4}[^)]*\)|\[\d+\]', chunk.content))
            
            # Detect mathematical content
            chunk.has_mathematical_content = bool(re.search(r'[∀∃∈∉∪∩⊂⊃∑∏∫]|\$.*\$|\\\\.*\\\\', chunk.content))
            
            # Content density score
            text_length = len(chunk.content)
            if text_length > 0:
                density = (chunk.citation_count * 0.1 + chunk.sentence_count * 0.05 + chunk.paragraph_count * 0.15)
                chunk.content_density_score = min(1.0, density)
    
    def get_chunk_statistics(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """Get statistics about generated chunks"""
        if not chunks:
            return {}
        
        token_counts = [chunk.token_count for chunk in chunks]
        word_counts = [chunk.word_count for chunk in chunks]
        overlap_counts = len([c for c in chunks if c.overlap_with_previous])
        
        return {
            'total_chunks': len(chunks),
            'avg_token_count': sum(token_counts) / len(token_counts),
            'min_token_count': min(token_counts),
            'max_token_count': max(token_counts),
            'avg_word_count': sum(word_counts) / len(word_counts),
            'chunks_with_overlap': overlap_counts,
            'overlap_percentage': overlap_counts / len(chunks) if chunks else 0,
            'total_citations': sum(c.citation_count for c in chunks),
            'chunks_with_math': len([c for c in chunks if c.has_mathematical_content]),
            'avg_content_density': sum(c.content_density_score for c in chunks) / len(chunks)
        }


def create_config_for_discipline(discipline: AcademicDiscipline) -> ChunkingConfig:
    """Create optimized configuration for specific academic discipline"""
    config = ChunkingConfig(discipline=discipline)
    
    # Apply discipline-specific parameters
    chunker = SimpleSlidingWindowChunker()
    discipline_params = chunker.discipline_configs.get(discipline, {})
    
    if discipline_params:
        config.window_size = discipline_params.get('preferred_window_size', config.window_size)
        config.overlap_percentage = discipline_params.get('overlap_percentage', config.overlap_percentage)
    
    return config


def demonstrate_sliding_window():
    """Demonstrate sliding window chunker functionality"""
    print("🎯 Task 3.4: Sliding Window with Configurable Overlap Demo")
    print("=" * 70)
    
    # Academic sample text with various structures
    sample_text = """
Introduction

This paper presents a novel approach to machine learning in academic contexts. The method builds upon previous work in neural networks and deep learning architectures, providing significant improvements in both accuracy and efficiency.

According to Smith et al. (2020), traditional approaches have several limitations. However, our method addresses these issues through innovative preprocessing techniques and improved training algorithms. Furthermore, we demonstrate significant improvements on benchmark datasets.

    Definition 1. A neural network is a computational model that mimics the biological neural networks found in animal brains through interconnected nodes or "neurons" that process information using mathematical functions.

The following list outlines our main contributions:
1. Novel attention-based architecture design with transformer components
2. Improved training algorithms using adaptive learning rates and regularization
3. Comprehensive evaluation framework across multiple academic domains
4. Open-source implementation for reproducibility and community adoption

Theorem 1.1 (Convergence). Under mild regularity conditions, our proposed algorithm converges to a global optimum with probability 1 as the number of training epochs approaches infinity.

Proof. We proceed by mathematical induction on the number of training epochs. The base case holds trivially for epoch 1. For the inductive step, assume convergence holds at epoch k...

2. Methodology

Our approach consists of three main components that work synergistically. First, we preprocess the input data using specialized normalization techniques optimized for academic text analysis. Second, we apply our novel neural network architecture with modified backpropagation and attention mechanisms. Third, we evaluate performance using established metrics and statistical significance tests.

As noted by Johnson (2021): "The integration of attention mechanisms represents a paradigm shift in neural network design that enables more interpretable and efficient models for academic text processing."

This comprehensive methodology ensures robust performance across diverse academic domains while maintaining computational efficiency and theoretical rigor.
    """
    
    print(f"📝 Sample text: {len(sample_text)} characters, ~{len(sample_text.split())} words")
    
    # Test 1: Basic sliding window chunking
    print("\\n🧪 Test 1: Basic sliding window with 20% overlap")
    config1 = ChunkingConfig(window_size=500, overlap_percentage=0.2)
    chunker1 = SimpleSlidingWindowChunker(config1)
    chunks1 = chunker1.chunk_text(sample_text, document_id="demo")
    
    print(f"\\n📊 Generated {len(chunks1)} chunks:")
    for i, chunk in enumerate(chunks1):
        print(f"   Chunk {i+1}: {chunk.token_count} tokens, pos {chunk.start_pos}-{chunk.end_pos}")
        if chunk.overlap_with_previous:
            print(f"      Overlaps with: {chunk.overlap_with_previous}")
        print(f"      Preview: {chunk.content[:100].replace(chr(10), ' ')}...")
    
    # Test 2: Different academic disciplines
    print("\\n🧪 Test 2: Academic discipline configurations")
    disciplines = [
        (AcademicDiscipline.HUMANITIES, "Longer chunks, more overlap for narrative flow"),
        (AcademicDiscipline.STEM, "Shorter chunks, less overlap for technical precision"),
        (AcademicDiscipline.LAW, "Longest chunks, maximum overlap for legal context")
    ]
    
    for discipline, description in disciplines:
        config = create_config_for_discipline(discipline)
        config.window_size = min(config.window_size, 600)  # Keep reasonable for demo
        chunker = SimpleSlidingWindowChunker(config)
        chunks = chunker.chunk_text(sample_text, document_id=f"test_{discipline.value}")
        
        stats = chunker.get_chunk_statistics(chunks)
        print(f"\\n   {discipline.value.upper()}: {description}")
        print(f"      {len(chunks)} chunks, avg {stats['avg_token_count']:.0f} tokens")
        print(f"      {stats['chunks_with_overlap']} overlapping ({stats['overlap_percentage']:.1%})")
    
    # Test 3: Dynamic adjustment demonstration
    print("\\n🧪 Test 3: Dynamic content adjustment")
    config3 = ChunkingConfig(window_size=400, overlap_percentage=0.25, dynamic_adjustment=True)
    chunker3 = SimpleSlidingWindowChunker(config3)
    chunks3 = chunker3.chunk_text(sample_text, document_id="dynamic_test")
    
    print("\\n   Content analysis per chunk:")
    for i, chunk in enumerate(chunks3[:3]):  # Show first 3 chunks
        print(f"   Chunk {i+1}:")
        print(f"      Citations: {chunk.citation_count}")
        print(f"      Sentences: {chunk.sentence_count}")
        print(f"      Math content: {chunk.has_mathematical_content}")
        print(f"      Density score: {chunk.content_density_score:.3f}")
    
    # Test 4: Overlap strategies
    print("\\n🧪 Test 4: Different overlap percentages")
    overlaps = [0.1, 0.2, 0.3]
    
    for overlap_pct in overlaps:
        config = ChunkingConfig(window_size=400, overlap_percentage=overlap_pct)
        chunker = SimpleSlidingWindowChunker(config)
        chunks = chunker.chunk_text(sample_text, document_id=f"overlap_{overlap_pct}")
        
        stats = chunker.get_chunk_statistics(chunks)
        print(f"   {overlap_pct:.0%} overlap: {len(chunks)} chunks, {stats['chunks_with_overlap']} overlapping")
    
    # Overall statistics
    print("\\n📊 Overall Statistics (Dynamic Adjustment Test):")
    final_stats = chunker3.get_chunk_statistics(chunks3)
    for key, value in final_stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")
    
    print("\\n✅ Task 3.4 Implementation Complete!")
    print("🎯 Key Features Demonstrated:")
    print("   • Configurable window size (500-2000 tokens) and overlap (10-30%)")
    print("   • Dynamic window adjustment based on content density")
    print("   • Academic discipline-specific optimizations")
    print("   • Context preservation through intelligent boundary detection")
    print("   • Overlap relationship tracking between consecutive chunks")
    print("   • Content analysis (citations, math, sentences, paragraphs)")
    print("   • Boundary optimization at sentence/paragraph breaks")
    print("   • Deduplication-ready overlap metadata")
    
    return chunks3


if __name__ == "__main__":
    demonstrate_sliding_window()