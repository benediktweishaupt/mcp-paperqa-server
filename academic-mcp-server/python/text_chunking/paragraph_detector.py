"""
ParagraphDetector - Core logic for maintaining complete paragraphs as atomic units

This module implements intelligent paragraph boundary detection for academic text chunking,
ensuring that paragraphs are never split across chunks to preserve argumentative coherence.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

try:
    import spacy
    from spacy.tokens import Doc, Span, Token
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    # Create mock classes for when spaCy is not available
    class Doc:
        def __init__(self):
            self.sents = []
        
    class Span:
        def __init__(self):
            self.start_char = 0
            self.end_char = 0
    
    class Token:
        def __init__(self):
            self.lemma_ = ""
            self.is_stop = False
            self.is_punct = False
            self.is_alpha = False

try:
    from .nlp_pipeline import AcademicNLPPipeline
except ImportError:
    # For direct execution, use absolute import
    try:
        from nlp_pipeline import AcademicNLPPipeline
    except ImportError:
        # If NLP pipeline not available, create a mock for testing
        class AcademicNLPPipeline:
            def __init__(self):
                pass
            def process_text(self, text):
                # Return a mock doc-like object
                mock_doc = type('MockDoc', (), {})()
                mock_doc.sents = []
                return mock_doc
            def extract_citations(self, doc):
                return []


class ParagraphType(Enum):
    """Types of paragraphs in academic texts"""
    REGULAR = "regular"
    QUOTE = "quote"
    LIST_ITEM = "list_item"
    CODE_BLOCK = "code_block"
    CAPTION = "caption"
    FOOTNOTE = "footnote"
    INDENTED_BLOCK = "indented_block"
    TABLE_CONTENT = "table_content"


@dataclass
class ParagraphBoundary:
    """Represents a detected paragraph boundary with metadata"""
    start_pos: int
    end_pos: int
    paragraph_type: ParagraphType
    confidence: float
    signals: List[str]  # List of detection signals that identified this boundary
    topic_sentence_pos: Optional[int] = None
    concluding_sentence_pos: Optional[int] = None
    internal_structure: Optional[Dict] = None


@dataclass
class ParagraphMetadata:
    """Rich metadata for a detected paragraph"""
    boundary: ParagraphBoundary
    text_content: str
    sentence_count: int
    word_count: int
    semantic_coherence_score: float
    has_citations: bool
    citation_count: int
    has_mathematical_content: bool
    indentation_level: int
    formatting_markers: List[str]


class ParagraphDetector:
    """
    Intelligent paragraph boundary detection for academic texts
    
    Uses multiple signals including:
    - Visual formatting (newlines, indentation)
    - Semantic coherence analysis
    - Academic structure patterns
    - Citation and reference patterns
    """
    
    def __init__(self, nlp_pipeline: Optional[AcademicNLPPipeline] = None):
        """
        Initialize the paragraph detector
        
        Args:
            nlp_pipeline: Existing academic NLP pipeline, creates new one if None
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize or use existing NLP pipeline
        if nlp_pipeline is None:
            if not SPACY_AVAILABLE:
                raise ImportError("spaCy not available. Install with: pip install spacy")
            self.nlp_pipeline = AcademicNLPPipeline()
        else:
            self.nlp_pipeline = nlp_pipeline
        
        # Configuration for detection sensitivity
        self.config = {
            'min_paragraph_length': 20,  # Minimum characters for a paragraph
            'max_paragraph_length': 2000,  # Maximum characters before forced split
            'semantic_coherence_threshold': 0.7,  # Minimum coherence score
            'double_newline_weight': 0.8,  # Weight for double newline signal
            'indentation_weight': 0.6,  # Weight for indentation changes
            'semantic_break_weight': 0.7,  # Weight for semantic discontinuity
            'citation_boundary_weight': 0.5,  # Weight for citation boundaries
        }
        
        # Patterns for academic text structures
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for different text structures"""
        self.patterns = {
            # Quote patterns (indented blocks, quotation marks)
            'quote_block': re.compile(r'^\\s{4,}(?:["""].*["""]|.*)', re.MULTILINE),
            'quote_markers': re.compile(r'^\\s*["""].*["""]\\s*$', re.MULTILINE),
            
            # List patterns (numbered, bulleted)
            'numbered_list': re.compile(r'^\\s*(?:\\d+[.):]|[a-zA-Z][.):]|[ivx]+[.):])', re.MULTILINE),
            'bulleted_list': re.compile(r'^\\s*[•\\-\\*]\\s+', re.MULTILINE),
            
            # Academic structures
            'theorem_like': re.compile(r'^\\s*(?:Theorem|Lemma|Corollary|Proposition|Definition|Example)\\s*\\d*[.:)]', re.MULTILINE | re.IGNORECASE),
            'proof_start': re.compile(r'^\\s*(?:Proof|Demonstration)[.:)]?\\s*', re.MULTILINE | re.IGNORECASE),
            'proof_end': re.compile(r'(?:∎|□|QED|\\s*$)', re.MULTILINE),
            
            # Code and technical content
            'code_block': re.compile(r'^\\s*```|^\\s*\\|.*\\|\\s*$|^\\s*\\+[-+]+\\+', re.MULTILINE),
            
            # Captions and labels
            'figure_caption': re.compile(r'^\\s*(?:Figure|Fig|Table|Algorithm)\\s*\\d+[.:)]', re.MULTILINE | re.IGNORECASE),
            
            # Footnotes
            'footnote': re.compile(r'^\\s*\\d+\\s+', re.MULTILINE),
        }
    
    def detect_paragraph_boundaries(self, text: str, preserve_structure: bool = True) -> List[ParagraphMetadata]:
        """
        Detect paragraph boundaries in academic text
        
        Args:
            text: Input academic text
            preserve_structure: Whether to preserve special academic structures
            
        Returns:
            List of ParagraphMetadata objects with detected boundaries
        """
        if not text.strip():
            return []
        
        self.logger.debug(f"Detecting paragraph boundaries in text of length {len(text)}")
        
        # Process text through NLP pipeline
        doc = self.nlp_pipeline.process_text(text)
        
        # Detect boundaries using multiple signals
        visual_boundaries = self._detect_visual_boundaries(text)
        semantic_boundaries = self._detect_semantic_boundaries(doc)
        structural_boundaries = self._detect_structural_boundaries(text)
        
        # Combine and score all boundaries
        combined_boundaries = self._combine_boundaries(
            text, doc, visual_boundaries, semantic_boundaries, structural_boundaries
        )
        
        # Filter and validate boundaries
        validated_boundaries = self._validate_boundaries(text, combined_boundaries)
        
        # Generate metadata for each paragraph
        paragraphs = self._generate_paragraph_metadata(text, doc, validated_boundaries)
        
        self.logger.info(f"Detected {len(paragraphs)} paragraph boundaries")
        
        return paragraphs
    
    def _detect_visual_boundaries(self, text: str) -> List[Tuple[int, float, List[str]]]:
        """
        Detect paragraph boundaries based on visual formatting
        
        Returns:
            List of (position, confidence, signals) tuples
        """
        boundaries = []
        
        # Double newline detection (strongest visual signal)
        double_newlines = [(m.start(), self.config['double_newline_weight'], ['double_newline']) 
                          for m in re.finditer(r'\\n\\s*\\n', text)]
        boundaries.extend(double_newlines)
        
        # Indentation changes
        lines = text.split('\\n')
        for i in range(1, len(lines)):
            prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
            curr_indent = len(lines[i]) - len(lines[i].lstrip())
            
            if abs(curr_indent - prev_indent) >= 4:  # Significant indentation change
                pos = sum(len(line) + 1 for line in lines[:i])  # +1 for newline
                confidence = self.config['indentation_weight']
                boundaries.append((pos, confidence, ['indentation_change']))
        
        return boundaries
    
    def _detect_semantic_boundaries(self, doc: Doc) -> List[Tuple[int, float, List[str]]]:
        """
        Detect paragraph boundaries based on semantic coherence
        
        Args:
            doc: Processed spaCy document
            
        Returns:
            List of (position, confidence, signals) tuples
        """
        if not doc.sents:
            return []
        
        boundaries = []
        sentences = list(doc.sents)
        
        # Analyze semantic similarity between consecutive sentences
        for i in range(1, len(sentences)):
            prev_sent = sentences[i-1]
            curr_sent = sentences[i]
            
            # Calculate semantic similarity (simplified version)
            similarity = self._calculate_sentence_similarity(prev_sent, curr_sent)
            
            # Low similarity indicates potential paragraph boundary
            if similarity < self.config['semantic_coherence_threshold']:
                pos = curr_sent.start_char
                confidence = self.config['semantic_break_weight'] * (1 - similarity)
                boundaries.append((pos, confidence, ['semantic_break']))
        
        return boundaries
    
    def _calculate_sentence_similarity(self, sent1: Span, sent2: Span) -> float:
        """
        Calculate semantic similarity between two sentences
        
        This is a simplified implementation using token overlap.
        In a full implementation, this would use sentence embeddings.
        """
        # Get lemmatized tokens, excluding stop words and punctuation
        tokens1 = {token.lemma_.lower() for token in sent1 
                  if not token.is_stop and not token.is_punct and token.is_alpha}
        tokens2 = {token.lemma_.lower() for token in sent2 
                  if not token.is_stop and not token.is_punct and token.is_alpha}
        
        if not tokens1 or not tokens2:
            return 0.5  # Neutral similarity for empty token sets
        
        # Jaccard similarity
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _detect_structural_boundaries(self, text: str) -> List[Tuple[int, float, List[str]]]:
        """
        Detect paragraph boundaries based on academic text structures
        
        Returns:
            List of (position, confidence, signals) tuples
        """
        boundaries = []
        
        # Check each compiled pattern
        for structure_name, pattern in self.patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                pos = match.start()
                confidence = 0.8  # High confidence for structural markers
                signals = [f'structure_{structure_name}']
                boundaries.append((pos, confidence, signals))
        
        return boundaries
    
    def _combine_boundaries(self, text: str, doc: Doc, 
                           visual: List[Tuple[int, float, List[str]]],
                           semantic: List[Tuple[int, float, List[str]]],
                           structural: List[Tuple[int, float, List[str]]]) -> List[ParagraphBoundary]:
        """
        Combine boundaries from different detection methods
        
        Returns:
            List of combined ParagraphBoundary objects
        """
        # Combine all boundaries
        all_boundaries = visual + semantic + structural
        
        # Group nearby boundaries (within 10 characters)
        grouped_boundaries = {}
        for pos, confidence, signals in all_boundaries:
            # Find nearby positions
            key_pos = None
            for existing_pos in grouped_boundaries.keys():
                if abs(pos - existing_pos) <= 10:
                    key_pos = existing_pos
                    break
            
            if key_pos is None:
                key_pos = pos
                grouped_boundaries[key_pos] = {'confidence': 0.0, 'signals': []}
            
            # Combine confidences and signals
            grouped_boundaries[key_pos]['confidence'] = max(
                grouped_boundaries[key_pos]['confidence'], confidence
            )
            grouped_boundaries[key_pos]['signals'].extend(signals)
        
        # Create ParagraphBoundary objects
        boundaries = []
        sorted_positions = sorted(grouped_boundaries.keys())
        
        for i, pos in enumerate(sorted_positions):
            data = grouped_boundaries[pos]
            
            # Determine paragraph type based on signals
            paragraph_type = self._classify_paragraph_type(data['signals'])
            
            # Find end position (next boundary or end of text)
            end_pos = sorted_positions[i + 1] if i + 1 < len(sorted_positions) else len(text)
            
            boundary = ParagraphBoundary(
                start_pos=pos,
                end_pos=end_pos,
                paragraph_type=paragraph_type,
                confidence=data['confidence'],
                signals=data['signals']
            )
            
            boundaries.append(boundary)
        
        return boundaries
    
    def _classify_paragraph_type(self, signals: List[str]) -> ParagraphType:
        """Classify paragraph type based on detection signals"""
        signal_str = ' '.join(signals)
        
        if 'structure_quote' in signal_str:
            return ParagraphType.QUOTE
        elif 'structure_numbered_list' in signal_str or 'structure_bulleted_list' in signal_str:
            return ParagraphType.LIST_ITEM
        elif 'structure_code_block' in signal_str:
            return ParagraphType.CODE_BLOCK
        elif 'structure_figure_caption' in signal_str:
            return ParagraphType.CAPTION
        elif 'structure_footnote' in signal_str:
            return ParagraphType.FOOTNOTE
        elif 'indentation_change' in signal_str:
            return ParagraphType.INDENTED_BLOCK
        else:
            return ParagraphType.REGULAR
    
    def _validate_boundaries(self, text: str, boundaries: List[ParagraphBoundary]) -> List[ParagraphBoundary]:
        """
        Validate and filter paragraph boundaries
        
        Args:
            text: Original text
            boundaries: Detected boundaries
            
        Returns:
            Validated list of boundaries
        """
        validated = []
        
        for boundary in boundaries:
            paragraph_text = text[boundary.start_pos:boundary.end_pos].strip()
            
            # Skip empty or too short paragraphs
            if len(paragraph_text) < self.config['min_paragraph_length']:
                continue
            
            # Handle too long paragraphs
            if len(paragraph_text) > self.config['max_paragraph_length']:
                # Split long paragraphs at sentence boundaries
                self.logger.warning(f"Long paragraph detected ({len(paragraph_text)} chars), may need splitting")
                # For now, keep as is - could implement sentence-level splitting here
            
            validated.append(boundary)
        
        return validated
    
    def _generate_paragraph_metadata(self, text: str, doc: Doc, 
                                   boundaries: List[ParagraphBoundary]) -> List[ParagraphMetadata]:
        """
        Generate rich metadata for each detected paragraph
        
        Args:
            text: Original text
            doc: Processed spaCy document
            boundaries: Validated boundaries
            
        Returns:
            List of ParagraphMetadata objects
        """
        paragraphs = []
        
        for boundary in boundaries:
            paragraph_text = text[boundary.start_pos:boundary.end_pos].strip()
            
            # Find sentences in this paragraph
            paragraph_sentences = [sent for sent in doc.sents 
                                 if sent.start_char >= boundary.start_pos and 
                                    sent.end_char <= boundary.end_pos]
            
            # Extract citations in this paragraph
            citations = self.nlp_pipeline.extract_citations(doc)
            paragraph_citations = [cite for cite in citations 
                                 if cite['start'] >= boundary.start_pos and 
                                    cite['end'] <= boundary.end_pos]
            
            # Calculate semantic coherence
            coherence_score = self._calculate_paragraph_coherence(paragraph_sentences)
            
            # Detect mathematical content
            has_math = bool(re.search(r'[∀∃∈∉∪∩⊂⊃∑∏∫]|\\$.*\\$|\\\\.*\\\\', paragraph_text))
            
            # Calculate indentation level
            indentation = len(paragraph_text) - len(paragraph_text.lstrip())
            
            # Detect formatting markers
            formatting_markers = []
            if re.search(r'\\*\\*.*\\*\\*|__.*__', paragraph_text):
                formatting_markers.append('bold')
            if re.search(r'\\*.*\\*|_.*_', paragraph_text):
                formatting_markers.append('italic')
            if re.search(r'`.*`', paragraph_text):
                formatting_markers.append('code')
            
            metadata = ParagraphMetadata(
                boundary=boundary,
                text_content=paragraph_text,
                sentence_count=len(paragraph_sentences),
                word_count=len(paragraph_text.split()),
                semantic_coherence_score=coherence_score,
                has_citations=len(paragraph_citations) > 0,
                citation_count=len(paragraph_citations),
                has_mathematical_content=has_math,
                indentation_level=indentation,
                formatting_markers=formatting_markers
            )
            
            paragraphs.append(metadata)
        
        return paragraphs
    
    def _calculate_paragraph_coherence(self, sentences: List[Span]) -> float:
        """
        Calculate semantic coherence score for a paragraph
        
        Args:
            sentences: List of sentences in the paragraph
            
        Returns:
            Coherence score between 0.0 and 1.0
        """
        if len(sentences) <= 1:
            return 1.0  # Single sentence is perfectly coherent
        
        # Calculate average pairwise similarity between sentences
        similarities = []
        for i in range(len(sentences)):
            for j in range(i + 1, len(sentences)):
                sim = self._calculate_sentence_similarity(sentences[i], sentences[j])
                similarities.append(sim)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def ensure_no_split_paragraphs(self, text: str, chunk_boundaries: List[int]) -> List[int]:
        """
        Adjust chunk boundaries to ensure no paragraphs are split
        
        Args:
            text: Original text
            chunk_boundaries: Proposed chunk boundary positions
            
        Returns:
            Adjusted chunk boundaries that respect paragraph integrity
        """
        # Detect paragraph boundaries
        paragraphs = self.detect_paragraph_boundaries(text)
        paragraph_starts = [p.boundary.start_pos for p in paragraphs]
        paragraph_ends = [p.boundary.end_pos for p in paragraphs]
        
        adjusted_boundaries = []
        
        for boundary in chunk_boundaries:
            # Check if boundary falls within a paragraph
            adjusted_boundary = boundary
            
            for p_start, p_end in zip(paragraph_starts, paragraph_ends):
                if p_start < boundary < p_end:
                    # Boundary splits a paragraph, move to paragraph end
                    adjusted_boundary = p_end
                    self.logger.debug(f"Adjusted chunk boundary from {boundary} to {adjusted_boundary} to preserve paragraph")
                    break
            
            adjusted_boundaries.append(adjusted_boundary)
        
        return adjusted_boundaries
    
    def get_paragraph_at_position(self, text: str, position: int) -> Optional[ParagraphMetadata]:
        """
        Get the paragraph that contains a specific text position
        
        Args:
            text: Original text
            position: Character position in text
            
        Returns:
            ParagraphMetadata if found, None otherwise
        """
        paragraphs = self.detect_paragraph_boundaries(text)
        
        for paragraph in paragraphs:
            if paragraph.boundary.start_pos <= position <= paragraph.boundary.end_pos:
                return paragraph
        
        return None


# Utility functions for testing and validation
def test_paragraph_detection():
    """Test function to validate paragraph detection on sample academic text"""
    sample_text = """
    Introduction
    
    This paper presents a novel approach to machine learning. The method builds upon 
    previous work in neural networks and deep learning architectures.
    
    According to Smith et al. (2020), traditional approaches have limitations. However,
    our method addresses these issues through innovative preprocessing techniques.
    
        Definition 1. A neural network is a computational model that mimics the 
        structure of biological neural networks.
    
    The following list outlines our contributions:
    1. Novel architecture design
    2. Improved training algorithms  
    3. Comprehensive evaluation framework
    
    2. Methodology
    
    Our approach consists of three main components. First, we preprocess the input data
    using specialized techniques. Second, we apply our novel neural network architecture.
    """
    
    detector = ParagraphDetector()
    paragraphs = detector.detect_paragraph_boundaries(sample_text)
    
    print(f"Detected {len(paragraphs)} paragraphs:")
    for i, paragraph in enumerate(paragraphs):
        print(f"\\nParagraph {i+1}:")
        print(f"  Type: {paragraph.boundary.paragraph_type.value}")
        print(f"  Length: {len(paragraph.text_content)} characters")
        print(f"  Sentences: {paragraph.sentence_count}")
        print(f"  Coherence: {paragraph.semantic_coherence_score:.2f}")
        print(f"  Signals: {paragraph.boundary.signals}")
        print(f"  Text preview: {paragraph.text_content[:100]}...")


if __name__ == "__main__":
    test_paragraph_detection()