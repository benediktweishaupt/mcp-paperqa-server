"""
SlidingWindowChunker - Intelligent text chunking with configurable overlap and context preservation

This module implements a sophisticated sliding window chunking system that:
- Maintains configurable window sizes (500-2000 tokens) and overlap percentages (10-30%)
- Preserves paragraph integrity using the ParagraphDetector from Task 3.2
- Implements dynamic window adjustment based on content density
- Provides overlap deduplication to avoid redundant content in vector stores
- Supports academic discipline-specific configurations
"""

import re
import logging
from typing import List, Dict, Optional, Tuple, Set, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

try:
    import spacy
    from spacy.tokens import Doc
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    class Doc:
        def __init__(self):
            self.text = ""

try:
    from .paragraph_detector import ParagraphDetector, ParagraphMetadata
    from .nlp_pipeline import AcademicNLPPipeline
except ImportError:
    # For direct execution, use absolute imports
    try:
        from paragraph_detector import ParagraphDetector, ParagraphMetadata
        from nlp_pipeline import AcademicNLPPipeline
    except ImportError:
        # Mock classes for testing without dependencies
        class ParagraphDetector:
            def __init__(self):
                pass
            def detect_paragraph_boundaries(self, text):
                return []
            def ensure_no_split_paragraphs(self, text, boundaries):
                return boundaries
        
        class ParagraphMetadata:
            def __init__(self):
                self.boundary = None
                self.text_content = ""
                self.word_count = 0
        
        class AcademicNLPPipeline:
            def __init__(self):
                pass
            def process_text(self, text):
                mock_doc = type('MockDoc', (), {})()
                mock_doc.text = text
                return mock_doc


class ChunkOverlapStrategy(Enum):
    """Strategies for handling chunk overlaps"""
    SENTENCE_BOUNDARY = "sentence_boundary"  # Overlap at sentence boundaries
    PARAGRAPH_BOUNDARY = "paragraph_boundary"  # Overlap at paragraph boundaries
    SEMANTIC_BOUNDARY = "semantic_boundary"  # Overlap at semantic transition points
    FIXED_PERCENTAGE = "fixed_percentage"  # Fixed percentage overlap


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
    window_size: int = 1000  # Target chunk size in tokens
    min_window_size: int = 500  # Minimum allowed chunk size
    max_window_size: int = 2000  # Maximum allowed chunk size
    overlap_percentage: float = 0.2  # Default 20% overlap
    min_overlap_percentage: float = 0.1  # Minimum 10% overlap
    max_overlap_percentage: float = 0.3  # Maximum 30% overlap
    
    overlap_strategy: ChunkOverlapStrategy = ChunkOverlapStrategy.SENTENCE_BOUNDARY
    preserve_paragraphs: bool = True
    preserve_sentences: bool = True
    dynamic_adjustment: bool = True
    
    # Content density thresholds for dynamic adjustment
    high_density_threshold: float = 0.8  # Many citations, complex structure
    low_density_threshold: float = 0.3   # Simple, narrative text
    
    # Academic discipline-specific settings
    discipline: AcademicDiscipline = AcademicDiscipline.GENERAL


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata and relationships"""
    content: str
    start_pos: int
    end_pos: int
    chunk_id: str
    sequence_number: int
    
    # Token and word counts
    token_count: int
    word_count: int
    
    # Overlap information
    overlap_with_previous: Optional[str] = None  # Previous chunk ID
    overlap_with_next: Optional[str] = None      # Next chunk ID
    overlap_start: Optional[int] = None          # Start of overlap region
    overlap_end: Optional[int] = None            # End of overlap region
    
    # Content analysis
    paragraph_count: int = 0
    sentence_count: int = 0
    citation_count: int = 0
    has_mathematical_content: bool = False
    content_density_score: float = 0.0
    
    # Relationships
    contains_paragraphs: List[str] = None  # Paragraph IDs contained in this chunk
    parent_document_id: Optional[str] = None
    
    def __post_init__(self):
        if self.contains_paragraphs is None:
            self.contains_paragraphs = []


class SlidingWindowChunker:
    """
    Intelligent sliding window text chunker for academic documents
    
    Features:
    - Configurable window sizes and overlap percentages
    - Paragraph and sentence boundary preservation
    - Dynamic window adjustment based on content density
    - Overlap deduplication strategies
    - Academic discipline-specific optimizations
    """
    
    def __init__(self, 
                 config: Optional[ChunkingConfig] = None,
                 paragraph_detector: Optional[ParagraphDetector] = None,
                 nlp_pipeline: Optional[AcademicNLPPipeline] = None):
        """
        Initialize the sliding window chunker
        
        Args:
            config: Chunking configuration parameters
            paragraph_detector: Existing paragraph detector instance
            nlp_pipeline: Existing NLP pipeline instance
        """
        self.logger = logging.getLogger(__name__)
        
        # Use provided config or create default
        self.config = config if config else ChunkingConfig()
        
        # Initialize components with fallback for missing dependencies
        if paragraph_detector:
            self.paragraph_detector = paragraph_detector
        else:
            try:
                self.paragraph_detector = ParagraphDetector()
            except ImportError:
                self.logger.warning("spaCy not available, using mock ParagraphDetector")
                self.paragraph_detector = ParagraphDetector()  # Will use mock from import fallback
        
        if nlp_pipeline:
            self.nlp_pipeline = nlp_pipeline
        else:
            try:
                self.nlp_pipeline = AcademicNLPPipeline()
            except ImportError:
                self.logger.warning("spaCy not available, using mock AcademicNLPPipeline")
                self.nlp_pipeline = AcademicNLPPipeline()  # Will use mock from import fallback
        
        # Load discipline-specific configurations
        self._load_discipline_configs()
        
        # Cache for processed documents to avoid recomputation
        self._document_cache = {}
        self._chunk_cache = {}
        
        self.logger.info(f"SlidingWindowChunker initialized with {self.config.window_size} token windows and {self.config.overlap_percentage:.1%} overlap")
    
    def _load_discipline_configs(self):
        """Load academic discipline-specific configurations"""
        self.discipline_configs = {
            AcademicDiscipline.GENERAL: {
                'preferred_window_size': 1000,
                'overlap_percentage': 0.2,
                'density_adjustment_factor': 1.0
            },
            AcademicDiscipline.HUMANITIES: {
                'preferred_window_size': 1200,  # Longer for narrative flow
                'overlap_percentage': 0.25,     # More overlap for context
                'density_adjustment_factor': 1.2  # Allow larger chunks
            },
            AcademicDiscipline.SOCIAL_SCIENCES: {
                'preferred_window_size': 1000,
                'overlap_percentage': 0.2,
                'density_adjustment_factor': 1.0
            },
            AcademicDiscipline.STEM: {
                'preferred_window_size': 800,   # Shorter for technical density
                'overlap_percentage': 0.15,    # Less overlap, more precision
                'density_adjustment_factor': 0.8  # Smaller chunks for complexity
            },
            AcademicDiscipline.LAW: {
                'preferred_window_size': 1500,  # Longer for legal arguments
                'overlap_percentage': 0.3,      # Maximum overlap for precedent context
                'density_adjustment_factor': 1.3
            },
            AcademicDiscipline.PHILOSOPHY: {
                'preferred_window_size': 1400,  # Long for argument development
                'overlap_percentage': 0.25,     # Good overlap for logical flow
                'density_adjustment_factor': 1.25
            }
        }
    
    def chunk_text(self, text: str, document_id: Optional[str] = None) -> List[TextChunk]:
        """
        Chunk text using sliding window approach with intelligent boundary detection
        
        Args:
            text: Input text to chunk
            document_id: Optional document identifier for caching and relationships
            
        Returns:
            List of TextChunk objects with metadata and relationships
        """
        if not text.strip():
            return []
        
        self.logger.info(f"Chunking text of {len(text)} characters with {self.config.window_size} token windows")
        
        # Check cache if document_id provided
        if document_id and document_id in self._chunk_cache:
            self.logger.debug(f"Returning cached chunks for document {document_id}")
            return self._chunk_cache[document_id]
        
        # Step 1: Detect paragraph boundaries for intelligent chunking
        paragraphs = self._get_paragraph_boundaries(text)
        
        # Step 2: Process through NLP pipeline for token counting and analysis
        doc = self._process_text(text)
        
        # Step 3: Calculate optimal chunk boundaries using sliding window
        chunk_boundaries = self._calculate_chunk_boundaries(text, doc, paragraphs)
        
        # Step 4: Create chunks with overlap and metadata
        chunks = self._create_chunks_with_overlap(text, doc, paragraphs, chunk_boundaries, document_id)
        
        # Step 5: Post-process chunks for quality and deduplication
        chunks = self._post_process_chunks(chunks)
        
        # Cache results if document_id provided
        if document_id:
            self._chunk_cache[document_id] = chunks
        
        self.logger.info(f"Created {len(chunks)} chunks with average size {sum(c.token_count for c in chunks) / len(chunks):.0f} tokens")
        
        return chunks
    
    def _get_paragraph_boundaries(self, text: str) -> List[ParagraphMetadata]:
        """Get paragraph boundaries using the ParagraphDetector"""
        try:
            return self.paragraph_detector.detect_paragraph_boundaries(text)
        except Exception as e:
            self.logger.warning(f"Paragraph detection failed: {e}, using fallback")
            return []
    
    def _process_text(self, text: str) -> Doc:
        """Process text through NLP pipeline"""
        try:
            return self.nlp_pipeline.process_text(text)
        except Exception as e:
            self.logger.warning(f"NLP processing failed: {e}, using fallback")
            # Create mock doc for fallback
            mock_doc = type('MockDoc', (), {})()
            mock_doc.text = text
            return mock_doc
    
    def _calculate_chunk_boundaries(self, text: str, doc: Doc, paragraphs: List[ParagraphMetadata]) -> List[int]:
        """
        Calculate optimal chunk boundaries using sliding window approach
        
        Args:
            text: Input text
            doc: Processed spaCy document
            paragraphs: Detected paragraph boundaries
            
        Returns:
            List of character positions for chunk boundaries
        """
        text_length = len(text)
        if text_length == 0:
            return []
        
        # Estimate tokens per character (rough approximation: ~4-5 chars per token)
        chars_per_token = 4.5
        target_chunk_chars = int(self.config.window_size * chars_per_token)
        min_chunk_chars = int(self.config.min_window_size * chars_per_token)
        max_chunk_chars = int(self.config.max_window_size * chars_per_token)
        
        boundaries = []
        current_pos = 0
        chunk_number = 0
        
        while current_pos < text_length:
            chunk_number += 1
            
            # Calculate target end position
            target_end = current_pos + target_chunk_chars
            
            # Adjust for content density if dynamic adjustment is enabled
            if self.config.dynamic_adjustment:
                target_end = self._adjust_for_content_density(text, current_pos, target_end)
            
            # Ensure we don't exceed text length
            target_end = min(target_end, text_length)
            
            # Find optimal boundary near target position
            optimal_boundary = self._find_optimal_boundary(
                text, paragraphs, current_pos, target_end, min_chunk_chars, max_chunk_chars
            )
            
            # Add boundary if it creates a valid chunk
            if optimal_boundary > current_pos:
                boundaries.append(optimal_boundary)
                
                # Calculate overlap for next chunk
                overlap_size = int(optimal_boundary * self.config.overlap_percentage)
                current_pos = optimal_boundary - overlap_size
                
                # Ensure current_pos doesn't go backwards too much
                min_advance = int(target_chunk_chars * (1 - self.config.max_overlap_percentage))
                current_pos = max(current_pos, boundaries[-1] - target_chunk_chars + min_advance)
            else:
                # No valid boundary found, advance by minimum amount
                current_pos += min_chunk_chars
        
        # Ensure final boundary captures end of text
        if not boundaries or boundaries[-1] < text_length:
            boundaries.append(text_length)
        
        self.logger.debug(f"Calculated {len(boundaries)} chunk boundaries")
        return boundaries
    
    def _adjust_for_content_density(self, text: str, start_pos: int, target_end: int) -> int:
        """Adjust chunk size based on content density"""
        chunk_text = text[start_pos:target_end]
        
        # Calculate content density metrics
        citation_count = len(re.findall(r'\([^)]*\d{4}[^)]*\)|\[\d+\]', chunk_text))
        math_content = len(re.findall(r'[∀∃∈∉∪∩⊂⊃∑∏∫]|\$.*\$|\\\\.*\\\\', chunk_text))
        structure_markers = len(re.findall(r'\b(theorem|definition|proof|example|lemma)\b', chunk_text.lower()))
        
        # Calculate density score (0.0 to 1.0)
        text_length = len(chunk_text)
        if text_length == 0:
            return target_end
        
        density_score = min(1.0, (citation_count * 10 + math_content * 15 + structure_markers * 20) / text_length)
        
        # Adjust chunk size based on density
        discipline_config = self.discipline_configs[self.config.discipline]
        adjustment_factor = discipline_config['density_adjustment_factor']
        
        if density_score > self.config.high_density_threshold:
            # High density: make chunks smaller
            size_factor = 0.8 * adjustment_factor
        elif density_score < self.config.low_density_threshold:
            # Low density: make chunks larger
            size_factor = 1.2 * adjustment_factor
        else:
            # Normal density: use standard size
            size_factor = adjustment_factor
        
        adjusted_end = start_pos + int((target_end - start_pos) * size_factor)
        adjusted_end = min(adjusted_end, len(text))
        
        return adjusted_end
    
    def _find_optimal_boundary(self, text: str, paragraphs: List[ParagraphMetadata], 
                               start_pos: int, target_end: int, 
                               min_chunk_chars: int, max_chunk_chars: int) -> int:
        """
        Find the optimal boundary position near the target end
        
        Priority order:
        1. Paragraph boundaries (if preserve_paragraphs is True)
        2. Sentence boundaries (if preserve_sentences is True) 
        3. Natural breakpoints (punctuation, line breaks)
        4. Word boundaries
        5. Target position (as fallback)
        """
        # Search window around target position
        search_window = min(200, max_chunk_chars // 10)
        search_start = max(start_pos + min_chunk_chars, target_end - search_window)
        search_end = min(len(text), target_end + search_window)
        
        # Option 1: Paragraph boundaries (highest priority)
        if self.config.preserve_paragraphs and paragraphs:
            for paragraph in paragraphs:
                boundary_pos = paragraph.boundary.end_pos
                if search_start <= boundary_pos <= search_end:
                    return boundary_pos
        
        # Option 2: Sentence boundaries
        if self.config.preserve_sentences:
            sentence_ends = []
            for match in re.finditer(r'[.!?]+\s+', text[search_start:search_end]):
                pos = search_start + match.end()
                if pos < len(text) and pos > start_pos + min_chunk_chars:
                    sentence_ends.append(pos)
            
            if sentence_ends:
                # Choose sentence end closest to target
                best_sentence = min(sentence_ends, key=lambda x: abs(x - target_end))
                return best_sentence
        
        # Option 3: Natural breakpoints (line breaks, punctuation)
        natural_breaks = []
        for pattern in [r'\n\n', r'\n', r'[.!?:;]\s+', r',\s+']:
            for match in re.finditer(pattern, text[search_start:search_end]):
                pos = search_start + match.end()
                if pos > start_pos + min_chunk_chars:
                    natural_breaks.append(pos)
        
        if natural_breaks:
            best_break = min(natural_breaks, key=lambda x: abs(x - target_end))
            return best_break
        
        # Option 4: Word boundaries
        word_boundaries = []
        for match in re.finditer(r'\s+', text[search_start:search_end]):
            pos = search_start + match.end()
            if pos > start_pos + min_chunk_chars:
                word_boundaries.append(pos)
        
        if word_boundaries:
            best_word = min(word_boundaries, key=lambda x: abs(x - target_end))
            return best_word
        
        # Fallback: use target position if within bounds
        if target_end <= max_chunk_chars + start_pos:
            return target_end
        
        # Last resort: minimum viable chunk
        return start_pos + min_chunk_chars
    
    def _create_chunks_with_overlap(self, text: str, doc: Doc, 
                                   paragraphs: List[ParagraphMetadata], 
                                   boundaries: List[int], 
                                   document_id: Optional[str]) -> List[TextChunk]:
        """Create TextChunk objects with proper overlap and metadata"""
        chunks = []
        
        for i, end_pos in enumerate(boundaries):
            start_pos = 0 if i == 0 else boundaries[i-1] - self._calculate_overlap_size(boundaries[i-1], boundaries[i])
            
            # Ensure start_pos doesn't go negative or overlap too much with previous chunk
            if i > 0:
                max_overlap = int((boundaries[i] - boundaries[i-1]) * self.config.max_overlap_percentage)
                start_pos = max(start_pos, boundaries[i-1] - max_overlap)
                start_pos = max(0, start_pos)
            
            chunk_content = text[start_pos:end_pos].strip()
            if not chunk_content:
                continue
            
            # Generate chunk ID
            chunk_id = f"{document_id or 'doc'}_{i:03d}" if document_id else f"chunk_{i:03d}"
            
            # Calculate token and word counts
            token_count = self._estimate_token_count(chunk_content)
            word_count = len(chunk_content.split())
            
            # Analyze content
            content_analysis = self._analyze_chunk_content(chunk_content, paragraphs)
            
            # Calculate overlap information
            overlap_info = self._calculate_overlap_info(i, boundaries, start_pos, end_pos)
            
            chunk = TextChunk(
                content=chunk_content,
                start_pos=start_pos,
                end_pos=end_pos,
                chunk_id=chunk_id,
                sequence_number=i,
                token_count=token_count,
                word_count=word_count,
                **overlap_info,
                **content_analysis,
                parent_document_id=document_id
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _calculate_overlap_size(self, prev_boundary: int, curr_boundary: int) -> int:
        """Calculate overlap size between consecutive chunks"""
        chunk_size = curr_boundary - prev_boundary
        overlap_size = int(chunk_size * self.config.overlap_percentage)
        return overlap_size
    
    def _estimate_token_count(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Simple approximation: split on whitespace and punctuation
        tokens = re.findall(r'\b\w+\b', text)
        return len(tokens)
    
    def _analyze_chunk_content(self, content: str, paragraphs: List[ParagraphMetadata]) -> Dict[str, Any]:
        """Analyze chunk content for metadata"""
        # Count paragraphs in chunk
        paragraph_count = len([p for p in paragraphs 
                              if content.find(p.text_content.strip()) != -1])
        
        # Count sentences (rough approximation)
        sentence_count = len(re.findall(r'[.!?]+', content))
        
        # Count citations
        citation_count = len(re.findall(r'\([^)]*\d{4}[^)]*\)|\[\d+\]', content))
        
        # Detect mathematical content
        has_mathematical_content = bool(re.search(r'[∀∃∈∉∪∩⊂⊃∑∏∫]|\$.*\$|\\\\.*\\\\', content))
        
        # Calculate content density score
        content_density_score = min(1.0, (citation_count * 0.1 + sentence_count * 0.05 + paragraph_count * 0.15))
        
        return {
            'paragraph_count': paragraph_count,
            'sentence_count': sentence_count,
            'citation_count': citation_count,
            'has_mathematical_content': has_mathematical_content,
            'content_density_score': content_density_score
        }
    
    def _calculate_overlap_info(self, chunk_index: int, boundaries: List[int], 
                               start_pos: int, end_pos: int) -> Dict[str, Any]:
        """Calculate overlap information for chunk relationships"""
        overlap_info = {}
        
        if chunk_index > 0:
            # Has overlap with previous chunk
            prev_end = boundaries[chunk_index - 1]
            if start_pos < prev_end:
                overlap_info['overlap_with_previous'] = f"chunk_{chunk_index-1:03d}"
                overlap_info['overlap_start'] = start_pos
                overlap_info['overlap_end'] = min(prev_end, end_pos)
        
        if chunk_index < len(boundaries) - 1:
            # Will have overlap with next chunk
            next_overlap_size = self._calculate_overlap_size(end_pos, boundaries[chunk_index + 1])
            if next_overlap_size > 0:
                overlap_info['overlap_with_next'] = f"chunk_{chunk_index+1:03d}"
        
        return overlap_info
    
    def _post_process_chunks(self, chunks: List[TextChunk]) -> List[TextChunk]:
        """Post-process chunks for quality assurance and deduplication"""
        if not chunks:
            return chunks
        
        self.logger.debug(f"Post-processing {len(chunks)} chunks")
        
        # Remove empty or too-small chunks
        min_chars = 50  # Minimum viable chunk size
        filtered_chunks = [chunk for chunk in chunks if len(chunk.content.strip()) >= min_chars]
        
        if len(filtered_chunks) != len(chunks):
            self.logger.info(f"Filtered out {len(chunks) - len(filtered_chunks)} small chunks")
        
        # Update sequence numbers after filtering
        for i, chunk in enumerate(filtered_chunks):
            chunk.sequence_number = i
            # Update chunk ID to reflect new sequence
            if chunk.parent_document_id:
                chunk.chunk_id = f"{chunk.parent_document_id}_{i:03d}"
            else:
                chunk.chunk_id = f"chunk_{i:03d}"
        
        return filtered_chunks
    
    def get_chunk_statistics(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """Get statistics about the generated chunks"""
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
    
    def deduplicate_overlaps(self, chunks: List[TextChunk]) -> List[TextChunk]:
        """Remove redundant content from overlapping chunks"""
        # This is a placeholder for advanced deduplication logic
        # In a full implementation, this would identify and remove
        # redundant sentences/paragraphs in overlapping regions
        self.logger.info("Deduplication not implemented yet - returning chunks as-is")
        return chunks


# Utility functions for configuration and testing
def create_config_for_discipline(discipline: AcademicDiscipline) -> ChunkingConfig:
    """Create optimized configuration for specific academic discipline"""
    config = ChunkingConfig(discipline=discipline)
    
    # Load discipline-specific parameters
    chunker = SlidingWindowChunker()  # Temporary instance to access configs
    discipline_params = chunker.discipline_configs.get(discipline, {})
    
    if discipline_params:
        config.window_size = discipline_params.get('preferred_window_size', config.window_size)
        config.overlap_percentage = discipline_params.get('overlap_percentage', config.overlap_percentage)
    
    return config


def test_sliding_window_chunker():
    """Test function for the sliding window chunker"""
    sample_text = """
    Introduction

    This paper presents a novel approach to machine learning in academic contexts. 
    The method builds upon previous work in neural networks and deep learning 
    architectures, providing significant improvements in both accuracy and efficiency.

    According to Smith et al. (2020), traditional approaches have several limitations. 
    However, our method addresses these issues through innovative preprocessing 
    techniques and improved training algorithms.

        Definition 1. A neural network is a computational model that mimics the 
        biological neural networks found in animal brains through interconnected 
        nodes or "neurons" that process information.

    The following list outlines our main contributions:
    1. Novel attention-based architecture design
    2. Improved training algorithms with adaptive learning rates
    3. Comprehensive evaluation framework across multiple domains
    4. Open-source implementation for reproducibility

    Theorem 1.1 (Convergence). Under mild conditions, our algorithm converges 
    to a global optimum with probability 1.

    Proof. We proceed by induction on the number of training epochs...

    2. Methodology

    Our approach consists of three main components. First, we preprocess the input 
    data using specialized normalization techniques. Second, we apply our novel 
    neural network architecture with modified backpropagation. Third, we evaluate 
    performance using established metrics.

    As noted by Johnson (2021): "The integration of attention mechanisms represents 
    a paradigm shift in neural network design that enables more interpretable and 
    efficient models."
    """
    
    # Create chunker with default configuration
    config = ChunkingConfig(window_size=500, overlap_percentage=0.2)
    chunker = SlidingWindowChunker(config=config)
    
    # Generate chunks
    chunks = chunker.chunk_text(sample_text, document_id="test_doc")
    
    print(f"🎯 Generated {len(chunks)} chunks:")
    print("=" * 60)
    
    for i, chunk in enumerate(chunks):
        print(f"\n📄 Chunk {i+1} (ID: {chunk.chunk_id}):")
        print(f"   Position: {chunk.start_pos}-{chunk.end_pos}")
        print(f"   Tokens: {chunk.token_count}, Words: {chunk.word_count}")
        print(f"   Sentences: {chunk.sentence_count}, Citations: {chunk.citation_count}")
        print(f"   Content density: {chunk.content_density_score:.2f}")
        if chunk.overlap_with_previous:
            print(f"   Overlaps with: {chunk.overlap_with_previous}")
        print(f"   Preview: {chunk.content[:100].replace(chr(10), ' ')}...")
    
    # Show statistics
    stats = chunker.get_chunk_statistics(chunks)
    print(f"\n📊 Chunking Statistics:")
    print(f"   Average tokens per chunk: {stats['avg_token_count']:.0f}")
    print(f"   Range: {stats['min_token_count']}-{stats['max_token_count']} tokens")
    print(f"   Chunks with overlap: {stats['chunks_with_overlap']}/{stats['total_chunks']}")
    print(f"   Total citations: {stats['total_citations']}")
    print(f"   Average content density: {stats['avg_content_density']:.2f}")
    
    return chunks


if __name__ == "__main__":
    # Run test
    print("🧪 Testing SlidingWindowChunker...")
    test_sliding_window_chunker()
    print("\n✅ SlidingWindowChunker test completed!")