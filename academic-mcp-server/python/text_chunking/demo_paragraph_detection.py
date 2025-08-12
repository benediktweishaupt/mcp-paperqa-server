#!/usr/bin/env python3
"""
Demonstration of paragraph detection logic for Task 3.2

This demo shows the core paragraph detection functionality without requiring
full spaCy installation, highlighting the key features implemented.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Tuple, Optional


class ParagraphType(Enum):
    """Types of paragraphs in academic texts"""
    REGULAR = "regular"
    QUOTE = "quote"
    LIST_ITEM = "list_item"
    CODE_BLOCK = "code_block"
    CAPTION = "caption"
    FOOTNOTE = "footnote"
    INDENTED_BLOCK = "indented_block"
    THEOREM_LIKE = "theorem_like"


@dataclass
class DetectedParagraph:
    """Simplified paragraph detection result"""
    start_pos: int
    end_pos: int
    paragraph_type: ParagraphType
    confidence: float
    signals: List[str]
    text_content: str
    word_count: int
    has_citations: bool


class SimpleParagraphDetector:
    """
    Simplified paragraph detector for demonstration
    
    Shows the core logic implemented in Task 3.2 without external dependencies
    """
    
    def __init__(self):
        self.config = {
            'min_paragraph_length': 20,
            'max_paragraph_length': 2000,
            'double_newline_weight': 0.8,
            'indentation_weight': 0.6,
            'structure_weight': 0.9,
        }
        
        # Compile academic structure patterns
        self.patterns = {
            'theorem_like': re.compile(r'^\\s*(?:Theorem|Lemma|Corollary|Proposition|Definition|Example)\\s*\\d*[.:)]', 
                                     re.MULTILINE | re.IGNORECASE),
            'proof': re.compile(r'^\\s*(?:Proof|Demonstration)[.:)]?\\s*', re.MULTILINE | re.IGNORECASE),
            'numbered_list': re.compile(r'^\\s*(?:\\d+[.):]|[a-zA-Z][.):])', re.MULTILINE),
            'bulleted_list': re.compile(r'^\\s*[•\\-\\*]\\s+', re.MULTILINE),
            'quote_block': re.compile(r'^\\s{4,}.*$', re.MULTILINE),
            'figure_caption': re.compile(r'^\\s*(?:Figure|Fig|Table|Algorithm)\\s*\\d+[.:)]', 
                                       re.MULTILINE | re.IGNORECASE),
            'citations': re.compile(r'\\b(?:[A-Z][a-z]+\\s+et\\s+al\\.\\s*\\(\\d{4}\\)|[A-Z][a-z]+\\s*\\(\\d{4}\\)|\\[\\d+\\])', 
                                  re.IGNORECASE),
        }
    
    def detect_paragraphs(self, text: str) -> List[DetectedParagraph]:
        """
        Detect paragraph boundaries using multiple signals
        
        Args:
            text: Input academic text
            
        Returns:
            List of detected paragraphs with metadata
        """
        if not text.strip():
            return []
        
        print(f"🔍 Analyzing text of {len(text)} characters...")
        
        # Step 1: Detect visual boundaries (double newlines, indentation)
        visual_boundaries = self._detect_visual_boundaries(text)
        print(f"📄 Found {len(visual_boundaries)} visual boundaries")
        
        # Step 2: Detect structural boundaries (theorems, definitions, etc.)
        structural_boundaries = self._detect_structural_boundaries(text)
        print(f"🏗️  Found {len(structural_boundaries)} structural boundaries")
        
        # Step 3: Combine and validate boundaries
        combined_boundaries = self._combine_boundaries(text, visual_boundaries, structural_boundaries)
        print(f"🔗 Combined into {len(combined_boundaries)} paragraph boundaries")
        
        # Step 4: Generate paragraph metadata
        paragraphs = self._create_paragraphs(text, combined_boundaries)
        print(f"📝 Created {len(paragraphs)} validated paragraphs")
        
        return paragraphs
    
    def _detect_visual_boundaries(self, text: str) -> List[Tuple[int, float, List[str]]]:
        """Detect boundaries based on visual formatting"""
        boundaries = []
        
        # Double newline detection (strongest signal)
        for match in re.finditer(r'\\n\\s*\\n', text):
            boundaries.append((match.end(), self.config['double_newline_weight'], ['double_newline']))
        
        # Significant indentation changes
        lines = text.split('\\n')
        current_pos = 0
        
        for i in range(1, len(lines)):
            current_pos += len(lines[i-1]) + 1  # +1 for newline
            
            if not lines[i].strip():  # Skip empty lines
                continue
                
            prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip()) if lines[i-1].strip() else 0
            curr_indent = len(lines[i]) - len(lines[i].lstrip())
            
            if abs(curr_indent - prev_indent) >= 4:  # Significant change
                boundaries.append((current_pos, self.config['indentation_weight'], ['indentation_change']))
        
        return boundaries
    
    def _detect_structural_boundaries(self, text: str) -> List[Tuple[int, float, List[str]]]:
        """Detect boundaries based on academic structures"""
        boundaries = []
        
        for structure_name, pattern in self.patterns.items():
            if structure_name == 'citations':  # Citations don't create boundaries
                continue
                
            for match in pattern.finditer(text):
                confidence = self.config['structure_weight']
                signals = [f'structure_{structure_name}']
                boundaries.append((match.start(), confidence, signals))
        
        return boundaries
    
    def _combine_boundaries(self, text: str, visual: List, structural: List) -> List[Tuple[int, int, ParagraphType, float, List[str]]]:
        """Combine and validate all detected boundaries"""
        all_boundaries = visual + structural
        
        if not all_boundaries:
            # No boundaries found, treat entire text as one paragraph
            return [(0, len(text), ParagraphType.REGULAR, 0.5, ['default'])]
        
        # Sort boundaries by position
        all_boundaries.sort(key=lambda x: x[0])
        
        # Create paragraph segments
        segments = []
        start_pos = 0
        
        for boundary_pos, confidence, signals in all_boundaries:
            if boundary_pos > start_pos:
                # Determine paragraph type from signals
                paragraph_type = self._classify_paragraph_type(signals)
                
                segments.append((start_pos, boundary_pos, paragraph_type, confidence, signals))
                start_pos = boundary_pos
        
        # Add final segment
        if start_pos < len(text):
            segments.append((start_pos, len(text), ParagraphType.REGULAR, 0.5, ['final']))
        
        return segments
    
    def _classify_paragraph_type(self, signals: List[str]) -> ParagraphType:
        """Classify paragraph type based on detection signals"""
        signal_str = ' '.join(signals)
        
        if 'structure_theorem_like' in signal_str:
            return ParagraphType.THEOREM_LIKE
        elif 'structure_quote_block' in signal_str:
            return ParagraphType.QUOTE
        elif 'structure_numbered_list' in signal_str or 'structure_bulleted_list' in signal_str:
            return ParagraphType.LIST_ITEM
        elif 'structure_figure_caption' in signal_str:
            return ParagraphType.CAPTION
        elif 'indentation_change' in signal_str:
            return ParagraphType.INDENTED_BLOCK
        else:
            return ParagraphType.REGULAR
    
    def _create_paragraphs(self, text: str, boundaries: List) -> List[DetectedParagraph]:
        """Create paragraph objects with metadata"""
        paragraphs = []
        
        for start_pos, end_pos, paragraph_type, confidence, signals in boundaries:
            paragraph_text = text[start_pos:end_pos].strip()
            
            # Skip too short paragraphs
            if len(paragraph_text) < self.config['min_paragraph_length']:
                continue
            
            # Detect citations in this paragraph
            citations = self.patterns['citations'].findall(paragraph_text)
            
            paragraph = DetectedParagraph(
                start_pos=start_pos,
                end_pos=end_pos,
                paragraph_type=paragraph_type,
                confidence=confidence,
                signals=signals,
                text_content=paragraph_text,
                word_count=len(paragraph_text.split()),
                has_citations=len(citations) > 0
            )
            
            paragraphs.append(paragraph)
        
        return paragraphs
    
    def ensure_no_split_paragraphs(self, text: str, chunk_boundaries: List[int]) -> List[int]:
        """
        Adjust chunk boundaries to ensure no paragraphs are split
        
        This is the key functionality that preserves paragraph integrity
        """
        print(f"\\n🔧 Adjusting {len(chunk_boundaries)} chunk boundaries to preserve paragraphs...")
        
        # Detect paragraph boundaries
        paragraphs = self.detect_paragraphs(text)
        paragraph_ends = [p.end_pos for p in paragraphs]
        
        adjusted_boundaries = []
        adjustments_made = 0
        
        for boundary in chunk_boundaries:
            # Find the nearest paragraph end at or after this boundary
            adjusted_boundary = boundary
            
            for p in paragraphs:
                if p.start_pos < boundary < p.end_pos:
                    # Boundary splits a paragraph, move to paragraph end
                    adjusted_boundary = p.end_pos
                    adjustments_made += 1
                    print(f"  📌 Adjusted boundary {boundary} → {adjusted_boundary} (preserved {p.paragraph_type.value} paragraph)")
                    break
            
            adjusted_boundaries.append(adjusted_boundary)
        
        print(f"✅ Made {adjustments_made} adjustments to preserve paragraph integrity")
        return adjusted_boundaries


def demonstrate_paragraph_detection():
    """Demonstrate the paragraph detection capabilities"""
    
    print("🎯 Task 3.2: Paragraph-Level Preservation Logic Demo")
    print("=" * 60)
    
    # Sample academic text with various paragraph types
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

    Figure 1: Architecture diagram showing the flow of information through our 
    proposed neural network design with attention mechanisms.
    """
    
    # Create detector and analyze text
    detector = SimpleParagraphDetector()
    paragraphs = detector.detect_paragraphs(sample_text)
    
    print(f"\\n📊 Detected {len(paragraphs)} paragraphs:")
    print("-" * 60)
    
    for i, paragraph in enumerate(paragraphs):
        print(f"\\n📄 Paragraph {i+1}:")
        print(f"   Type: {paragraph.paragraph_type.value}")
        print(f"   Position: {paragraph.start_pos}-{paragraph.end_pos}")
        print(f"   Length: {len(paragraph.text_content)} chars, {paragraph.word_count} words")
        print(f"   Confidence: {paragraph.confidence:.2f}")
        print(f"   Citations: {'Yes' if paragraph.has_citations else 'No'}")
        print(f"   Signals: {', '.join(paragraph.signals)}")
        print(f"   Preview: {paragraph.text_content[:100].replace(chr(10), ' ')}...")
    
    print(f"\\n🔧 Testing Chunk Boundary Adjustment:")
    print("-" * 60)
    
    # Test chunk boundary adjustment (key feature of Task 3.2)
    proposed_boundaries = [200, 500, 800, 1200]  # Arbitrary chunk boundaries
    print(f"Original chunk boundaries: {proposed_boundaries}")
    
    adjusted_boundaries = detector.ensure_no_split_paragraphs(sample_text, proposed_boundaries)
    print(f"Adjusted chunk boundaries: {adjusted_boundaries}")
    
    print(f"\\n✅ Task 3.2 Implementation Complete!")
    print("🎯 Key Features Demonstrated:")
    print("   • Multi-signal paragraph boundary detection")
    print("   • Academic structure recognition (theorems, definitions, lists)")
    print("   • Citation detection and metadata extraction")
    print("   • Paragraph type classification")
    print("   • Chunk boundary adjustment to preserve paragraph integrity")
    print("   • Integration-ready for spaCy NLP pipeline")


if __name__ == "__main__":
    demonstrate_paragraph_detection()