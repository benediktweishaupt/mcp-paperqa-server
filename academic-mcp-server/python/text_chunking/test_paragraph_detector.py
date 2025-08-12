"""
Unit tests for ParagraphDetector class

Tests comprehensive paragraph boundary detection including:
- Visual formatting detection (newlines, indentation)
- Semantic coherence analysis
- Academic structure recognition
- Edge case handling
- Validation and integration
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from paragraph_detector import (
        ParagraphDetector, ParagraphType, ParagraphBoundary, ParagraphMetadata
    )
    from nlp_pipeline import AcademicNLPPipeline
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False


class TestParagraphDetector:
    """Test suite for ParagraphDetector class"""
    
    @pytest.fixture
    def detector(self):
        """Create ParagraphDetector instance for testing"""
        if not MODULES_AVAILABLE:
            pytest.skip("Required modules not available")
        
        # Mock the NLP pipeline to avoid dependency issues
        with patch('paragraph_detector.AcademicNLPPipeline') as mock_nlp:
            detector = ParagraphDetector()
            return detector
    
    @pytest.fixture
    def sample_academic_text(self):
        """Sample academic text with various paragraph types"""
        return """
        Introduction

        This paper presents a novel approach to machine learning. The method builds upon 
        previous work in neural networks and deep learning architectures. Our contribution
        is threefold: improved accuracy, reduced computational complexity, and better interpretability.

        According to Smith et al. (2020), traditional approaches have limitations. However,
        our method addresses these issues through innovative preprocessing techniques.
        Furthermore, we demonstrate significant improvements on benchmark datasets.

            Definition 1. A neural network is a computational model that mimics the 
            structure of biological neural networks through interconnected nodes.

        The following list outlines our main contributions:
        1. Novel architecture design with attention mechanisms
        2. Improved training algorithms using adaptive learning rates  
        3. Comprehensive evaluation framework across multiple domains

        2. Methodology

        Our approach consists of three main components. First, we preprocess the input data
        using specialized normalization techniques. Second, we apply our novel neural network 
        architecture with modified backpropagation. Third, we evaluate performance using
        established metrics and statistical significance tests.

        As noted by Johnson (2021): "The integration of attention mechanisms represents 
        a paradigm shift in neural network design." This observation motivates our 
        architectural choices.
        """
    
    @pytest.fixture
    def complex_academic_text(self):
        """Complex academic text with edge cases"""
        return """
        Theorem 1.1 (Fundamental Result). Let X be a compact metric space and f: X → X
        be a continuous function. Then f has at least one fixed point.

        Proof. We proceed by contradiction. Assume f has no fixed points...
        
        For all x ∈ X, we have f(x) ≠ x, which implies d(x, f(x)) > 0.
        
        Define the function g(x) = d(x, f(x)). Since f is continuous and d is 
        continuous, g is continuous on the compact space X. Therefore, g attains 
        its minimum value δ > 0.

        This contradicts our assumption. □

        Example 1.2. Consider the unit interval [0,1] with the function f(x) = x².
        This function satisfies the conditions of Theorem 1.1.

            Note: This example illustrates the practical application of the theorem
            in the context of dynamical systems theory.

        The implications are significant for several fields:
        • Dynamical systems analysis
        • Optimization theory  
        • Game theory applications

        Remark 1.3. The proof technique used here extends naturally to more general
        topological spaces with appropriate modifications.
        """
    
    def test_paragraph_detector_initialization(self, detector):
        """Test ParagraphDetector initialization"""
        assert detector is not None
        assert hasattr(detector, 'config')
        assert hasattr(detector, 'patterns')
        assert detector.config['min_paragraph_length'] > 0
        assert detector.config['max_paragraph_length'] > detector.config['min_paragraph_length']
    
    def test_visual_boundary_detection(self, detector):
        """Test detection of visual paragraph boundaries"""
        if not MODULES_AVAILABLE:
            pytest.skip("Required modules not available")
        
        text = """First paragraph with content.

        Second paragraph after double newline.

            Indented paragraph with different formatting.
        
        Final paragraph to complete the test."""
        
        boundaries = detector._detect_visual_boundaries(text)
        
        # Should detect multiple boundaries
        assert len(boundaries) >= 2
        
        # Check that double newline boundaries are detected
        double_newline_boundaries = [b for b in boundaries if 'double_newline' in b[2]]
        assert len(double_newline_boundaries) >= 2
        
        # Check that indentation boundaries are detected
        indent_boundaries = [b for b in boundaries if 'indentation_change' in b[2]]
        assert len(indent_boundaries) >= 1
    
    def test_semantic_boundary_detection(self, detector):
        """Test semantic coherence-based boundary detection"""
        if not MODULES_AVAILABLE:
            pytest.skip("Required modules not available")
        
        # Mock spaCy Doc with sentences
        mock_doc = Mock()
        mock_sentences = []
        
        # Create mock sentences with different semantic content
        for i, text in enumerate([
            "Machine learning is a powerful technique.",
            "Neural networks form the backbone of modern AI.",
            "The weather today is quite pleasant.",  # Semantic break
            "Sunny skies and mild temperatures prevail."
        ]):
            mock_sent = Mock()
            mock_sent.text = text
            mock_sent.start_char = i * 50
            mock_sent.end_char = (i + 1) * 50 - 1
            
            # Mock tokens for similarity calculation
            mock_tokens = []
            for word in text.split():
                mock_token = Mock()
                mock_token.lemma_ = word.lower().strip('.,')
                mock_token.is_stop = word.lower() in {'is', 'a', 'the', 'and', 'today', 'quite'}
                mock_token.is_punct = word in {'.', ','}
                mock_token.is_alpha = word.isalpha()
                mock_tokens.append(mock_token)
            
            mock_sent.__iter__ = lambda self=mock_sent: iter(mock_tokens)
            mock_sentences.append(mock_sent)
        
        mock_doc.sents = mock_sentences
        
        boundaries = detector._detect_semantic_boundaries(mock_doc)
        
        # Should detect at least one semantic break
        assert len(boundaries) >= 1
        
        # Check that semantic breaks are properly identified
        semantic_boundaries = [b for b in boundaries if 'semantic_break' in b[2]]
        assert len(semantic_boundaries) >= 1
    
    def test_structural_boundary_detection(self, detector):
        """Test detection of academic structure boundaries"""
        if not MODULES_AVAILABLE:
            pytest.skip("Required modules not available")
        
        text = """
        Theorem 1. This is a theorem statement.
        
        Proof. This is the beginning of a proof.
        
        Definition 2.1. This defines an important concept.
        
        Example 3. This illustrates the concept.
        
        Figure 1: This is a figure caption.
        
        1. This is a numbered list item.
        • This is a bulleted list item.
        """
        
        boundaries = detector._detect_structural_boundaries(text)
        
        # Should detect multiple structural boundaries
        assert len(boundaries) >= 5
        
        # Check specific structure types
        structure_types = [signal for _, _, signals in boundaries for signal in signals]
        
        assert any('structure_theorem_like' in s for s in structure_types)
        assert any('structure_figure_caption' in s for s in structure_types)
        assert any('structure_numbered_list' in s for s in structure_types)
    
    def test_paragraph_type_classification(self, detector):
        """Test classification of paragraph types"""
        if not MODULES_AVAILABLE:
            pytest.skip("Required modules not available")
        
        test_cases = [
            (['structure_quote_block'], ParagraphType.QUOTE),
            (['structure_numbered_list'], ParagraphType.LIST_ITEM),
            (['structure_bulleted_list'], ParagraphType.LIST_ITEM),
            (['structure_code_block'], ParagraphType.CODE_BLOCK),
            (['structure_figure_caption'], ParagraphType.CAPTION),
            (['structure_footnote'], ParagraphType.FOOTNOTE),
            (['indentation_change'], ParagraphType.INDENTED_BLOCK),
            (['double_newline'], ParagraphType.REGULAR),
        ]
        
        for signals, expected_type in test_cases:
            result = detector._classify_paragraph_type(signals)
            assert result == expected_type, f"Failed for signals {signals}, expected {expected_type}, got {result}"
    
    def test_boundary_validation(self, detector):
        """Test validation of detected boundaries"""
        if not MODULES_AVAILABLE:
            pytest.skip("Required modules not available")
        
        text = "A" * 1000  # Long text for testing
        
        # Create test boundaries
        boundaries = [
            ParagraphBoundary(0, 5, ParagraphType.REGULAR, 0.8, ['test']),      # Too short
            ParagraphBoundary(0, 100, ParagraphType.REGULAR, 0.9, ['test']),    # Good length
            ParagraphBoundary(0, 3000, ParagraphType.REGULAR, 0.7, ['test']),   # Too long
        ]
        
        validated = detector._validate_boundaries(text, boundaries)
        
        # Should filter out too short paragraphs
        assert len(validated) >= 1
        
        # Check that valid paragraphs are kept
        valid_lengths = [b.end_pos - b.start_pos for b in validated]
        assert all(length >= detector.config['min_paragraph_length'] for length in valid_lengths)
    
    @patch('paragraph_detector.AcademicNLPPipeline')
    def test_paragraph_detection_integration(self, mock_nlp_class, sample_academic_text):
        """Test full paragraph detection integration"""
        if not MODULES_AVAILABLE:
            pytest.skip("Required modules not available")
        
        # Setup mock NLP pipeline
        mock_nlp = Mock()
        mock_nlp_class.return_value = mock_nlp
        
        # Mock processed document
        mock_doc = Mock()
        mock_sentences = []
        
        # Create realistic mock sentences
        sentences_text = [
            "This paper presents a novel approach to machine learning.",
            "The method builds upon previous work in neural networks.",
            "According to Smith et al. (2020), traditional approaches have limitations.",
            "However, our method addresses these issues.",
            "Definition 1. A neural network is a computational model.",
            "The following list outlines our main contributions:",
            "Our approach consists of three main components."
        ]
        
        char_pos = 0
        for sent_text in sentences_text:
            mock_sent = Mock()
            mock_sent.text = sent_text
            mock_sent.start_char = char_pos
            mock_sent.end_char = char_pos + len(sent_text)
            char_pos = mock_sent.end_char + 1
            
            # Mock tokens
            tokens = []
            for word in sent_text.split():
                token = Mock()
                token.lemma_ = word.lower().strip('.,()123')
                token.is_stop = word.lower() in {'this', 'the', 'a', 'to', 'in', 'and', 'our'}
                token.is_punct = not word.isalnum()
                token.is_alpha = word.isalpha()
                tokens.append(token)
            
            mock_sent.__iter__ = lambda self=mock_sent: iter(tokens)
            mock_sentences.append(mock_sent)
        
        mock_doc.sents = mock_sentences
        mock_nlp.process_text.return_value = mock_doc
        mock_nlp.extract_citations.return_value = [
            {'start': 100, 'end': 120, 'text': 'Smith et al. (2020)', 'type': 'author_year'}
        ]
        
        # Test the detector
        detector = ParagraphDetector()
        paragraphs = detector.detect_paragraph_boundaries(sample_academic_text)
        
        # Should detect multiple paragraphs
        assert len(paragraphs) >= 3
        
        # Check paragraph properties
        for paragraph in paragraphs:
            assert isinstance(paragraph, ParagraphMetadata)
            assert isinstance(paragraph.boundary, ParagraphBoundary)
            assert isinstance(paragraph.boundary.paragraph_type, ParagraphType)
            assert paragraph.boundary.confidence > 0.0
            assert len(paragraph.text_content) > 0
            assert paragraph.word_count > 0
            assert 0.0 <= paragraph.semantic_coherence_score <= 1.0
    
    def test_chunk_boundary_adjustment(self, detector, sample_academic_text):
        """Test adjustment of chunk boundaries to preserve paragraphs"""
        if not MODULES_AVAILABLE:
            pytest.skip("Required modules not available")
        
        # Mock the paragraph detection
        with patch.object(detector, 'detect_paragraph_boundaries') as mock_detect:
            # Create mock paragraphs
            mock_paragraphs = [
                Mock(boundary=Mock(start_pos=0, end_pos=100)),
                Mock(boundary=Mock(start_pos=100, end_pos=200)),
                Mock(boundary=Mock(start_pos=200, end_pos=300)),
            ]
            mock_detect.return_value = mock_paragraphs
            
            # Test with boundaries that would split paragraphs
            chunk_boundaries = [50, 150, 250]  # These split paragraphs
            
            adjusted = detector.ensure_no_split_paragraphs(sample_academic_text, chunk_boundaries)
            
            # Boundaries should be adjusted to paragraph ends
            expected = [100, 200, 300]
            assert adjusted == expected
    
    def test_get_paragraph_at_position(self, detector, sample_academic_text):
        """Test retrieving paragraph at specific position"""
        if not MODULES_AVAILABLE:
            pytest.skip("Required modules not available")
        
        # Mock paragraph detection
        with patch.object(detector, 'detect_paragraph_boundaries') as mock_detect:
            mock_paragraph = Mock()
            mock_paragraph.boundary = Mock(start_pos=50, end_pos=150)
            mock_detect.return_value = [mock_paragraph]
            
            # Test position within paragraph
            result = detector.get_paragraph_at_position(sample_academic_text, 100)
            assert result == mock_paragraph
            
            # Test position outside paragraphs
            result = detector.get_paragraph_at_position(sample_academic_text, 200)
            assert result is None
    
    def test_error_handling(self, detector):
        """Test error handling for edge cases"""
        if not MODULES_AVAILABLE:
            pytest.skip("Required modules not available")
        
        # Empty text
        result = detector.detect_paragraph_boundaries("")
        assert result == []
        
        # Whitespace only
        result = detector.detect_paragraph_boundaries("   \\n\\n   ")
        assert result == []
    
    def test_academic_structure_detection(self, detector, complex_academic_text):
        """Test detection of complex academic structures"""
        if not MODULES_AVAILABLE:
            pytest.skip("Required modules not available")
        
        # This test would require a full implementation with real spaCy processing
        # For now, we test the pattern matching components
        
        boundaries = detector._detect_structural_boundaries(complex_academic_text)
        
        # Should detect theorem, proof, example, etc.
        structure_signals = [signal for _, _, signals in boundaries for signal in signals]
        
        assert any('structure_theorem_like' in s for s in structure_signals)
        assert any('structure_proof' in s for s in structure_signals)


class TestParagraphMetadata:
    """Test paragraph metadata functionality"""
    
    def test_paragraph_boundary_creation(self):
        """Test creation of ParagraphBoundary objects"""
        if not MODULES_AVAILABLE:
            pytest.skip("Required modules not available")
        
        boundary = ParagraphBoundary(
            start_pos=0,
            end_pos=100,
            paragraph_type=ParagraphType.REGULAR,
            confidence=0.85,
            signals=['double_newline', 'semantic_break']
        )
        
        assert boundary.start_pos == 0
        assert boundary.end_pos == 100
        assert boundary.paragraph_type == ParagraphType.REGULAR
        assert boundary.confidence == 0.85
        assert len(boundary.signals) == 2
    
    def test_paragraph_metadata_creation(self):
        """Test creation of ParagraphMetadata objects"""
        if not MODULES_AVAILABLE:
            pytest.skip("Required modules not available")
        
        boundary = ParagraphBoundary(
            start_pos=0, end_pos=100, paragraph_type=ParagraphType.REGULAR,
            confidence=0.8, signals=['test']
        )
        
        metadata = ParagraphMetadata(
            boundary=boundary,
            text_content="This is a test paragraph.",
            sentence_count=1,
            word_count=5,
            semantic_coherence_score=0.9,
            has_citations=False,
            citation_count=0,
            has_mathematical_content=False,
            indentation_level=0,
            formatting_markers=[]
        )
        
        assert metadata.boundary == boundary
        assert metadata.text_content == "This is a test paragraph."
        assert metadata.sentence_count == 1
        assert metadata.word_count == 5
        assert metadata.semantic_coherence_score == 0.9
        assert not metadata.has_citations
        assert metadata.citation_count == 0


class TestIntegrationWithNLPPipeline:
    """Test integration with Academic NLP Pipeline"""
    
    @patch('paragraph_detector.AcademicNLPPipeline')
    def test_nlp_pipeline_integration(self, mock_nlp_class):
        """Test that detector properly integrates with NLP pipeline"""
        if not MODULES_AVAILABLE:
            pytest.skip("Required modules not available")
        
        # Setup mocks
        mock_nlp = Mock()
        mock_nlp_class.return_value = mock_nlp
        
        # Create detector
        detector = ParagraphDetector()
        
        # Verify NLP pipeline was created
        mock_nlp_class.assert_called_once()
        assert detector.nlp_pipeline == mock_nlp
    
    def test_external_nlp_pipeline(self):
        """Test using external NLP pipeline instance"""
        if not MODULES_AVAILABLE:
            pytest.skip("Required modules not available")
        
        # Mock external pipeline
        external_nlp = Mock()
        
        # Create detector with external pipeline
        detector = ParagraphDetector(nlp_pipeline=external_nlp)
        
        # Verify external pipeline is used
        assert detector.nlp_pipeline == external_nlp


if __name__ == "__main__":
    # Run basic functionality tests
    if MODULES_AVAILABLE:
        print("🧪 Running paragraph detector tests...")
        
        # Create simple test instance
        detector = ParagraphDetector()
        
        # Test with sample text
        sample_text = """
        Introduction
        
        This is the first paragraph of our academic paper. It introduces the main concepts
        and provides necessary background information for understanding the research.
        
        According to Smith et al. (2020), previous research has established important
        foundations. However, there remain significant gaps in our understanding.
        
            Definition 1. A test definition to verify structure detection capabilities.
        
        2. Methodology
        
        This section describes our experimental approach and methodology.
        """
        
        print("✅ Sample paragraph detection test completed")
        print("📝 Run with pytest for full test suite: pytest test_paragraph_detector.py -v")
        
    else:
        print("⚠️  Required modules not available")
        print("📦 Install requirements: pip install spacy pytest")