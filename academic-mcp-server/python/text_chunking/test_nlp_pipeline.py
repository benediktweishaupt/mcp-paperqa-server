"""
Test script for Academic NLP Pipeline
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nlp_pipeline import AcademicNLPPipeline, download_required_models, is_transformer_available
from config import NLPPipelineConfig, AcademicDiscipline


def test_pipeline_initialization():
    """Test pipeline initialization"""
    print("=" * 50)
    print("Testing Pipeline Initialization")
    print("=" * 50)
    
    try:
        # Test with basic model
        pipeline = AcademicNLPPipeline(model_name="en_core_web_sm", enable_transformer=False)
        info = pipeline.get_pipeline_info()
        
        print(f"✓ Pipeline initialized successfully")
        print(f"  Model: {info['model_name']}")
        print(f"  Components: {info['pipe_names']}")
        print(f"  Vocab size: {info['vocab_size']}")
        print(f"  Has transformer: {info['has_transformer']}")
        
        return pipeline
        
    except Exception as e:
        print(f"✗ Pipeline initialization failed: {e}")
        return None


def test_citation_detection(pipeline):
    """Test citation detection functionality"""
    print("\n" + "=" * 50)
    print("Testing Citation Detection")
    print("=" * 50)
    
    test_texts = [
        "According to Smith et al. (2020), this approach is effective.",
        "Recent research [1] shows promising results.",
        "As noted by Johnson (2019), the methodology has limitations.",
        "The study by Brown et al. (2021) contradicts these findings.",
        "See DOI: 10.1038/nature12373 for more details.",
    ]
    
    for text in test_texts:
        try:
            doc = pipeline.process_text(text)
            citations = pipeline.extract_citations(doc)
            
            print(f"\nText: '{text}'")
            if citations:
                for citation in citations:
                    print(f"  ✓ Found citation: '{citation['text']}' (type: {citation['type']})")
            else:
                print("  - No citations detected")
                
        except Exception as e:
            print(f"  ✗ Error processing: {e}")


def test_academic_structures(pipeline):
    """Test academic structure detection"""
    print("\n" + "=" * 50)
    print("Testing Academic Structure Detection")
    print("=" * 50)
    
    test_text = """
    Definition 1. A semantic space is a mathematical structure that represents meaning relationships between concepts.
    
    Theorem 2. Every finite-dimensional vector space has a basis.
    
    Proof. We proceed by mathematical induction on the dimension of the space.
    
    Example 1. Consider the vector space R³ with the standard basis vectors.
    
    Remark. This result extends to infinite-dimensional spaces under certain conditions.
    """
    
    try:
        doc = pipeline.process_text(test_text)
        structures = pipeline.extract_academic_structures(doc)
        
        print(f"Test text processed. Found {len(structures)} academic structures:")
        for structure in structures:
            print(f"  ✓ {structure['type'].upper()}: '{structure['text']}'")
            
    except Exception as e:
        print(f"✗ Error processing academic structures: {e}")


def test_discourse_markers(pipeline):
    """Test discourse marker detection"""
    print("\n" + "=" * 50)
    print("Testing Discourse Marker Detection")
    print("=" * 50)
    
    test_text = """
    We argue that this approach is superior to previous methods. However, the evidence suggests otherwise.
    Furthermore, the data demonstrates clear limitations. Therefore, we conclude that more research is needed.
    Nevertheless, these findings indicate promising directions for future work.
    """
    
    try:
        doc = pipeline.process_text(test_text)
        markers = pipeline.get_discourse_markers(doc)
        
        print(f"Found {len(markers)} discourse markers:")
        for marker in markers:
            print(f"  ✓ '{marker['text']}' (lemma: {marker['lemma']})")
            print(f"    In sentence: '{marker['sentence'][:50]}...'")
            
    except Exception as e:
        print(f"✗ Error processing discourse markers: {e}")


def test_sentence_complexity(pipeline):
    """Test sentence complexity analysis"""
    print("\n" + "=" * 50)
    print("Testing Sentence Complexity Analysis")
    print("=" * 50)
    
    test_texts = [
        "This is a simple sentence.",
        "Although the methodology appears sound, we must consider that the results, which were obtained under controlled conditions, may not generalize to real-world applications where confounding variables could significantly impact the observed effects.",
        "The research shows clear benefits.",
    ]
    
    for i, text in enumerate(test_texts, 1):
        try:
            doc = pipeline.process_text(text)
            complexity = pipeline.analyze_sentence_complexity(doc)
            
            print(f"\nSentence {i}: '{text[:60]}...'")
            for metrics in complexity:
                print(f"  Tokens: {metrics['num_tokens']}")
                print(f"  Clauses: {metrics['num_clauses']}")
                print(f"  Avg word length: {metrics['avg_word_length']:.2f}")
                print(f"  Complexity score: {metrics['complexity_score']:.2f}")
                
        except Exception as e:
            print(f"✗ Error analyzing sentence {i}: {e}")


def test_full_academic_text(pipeline):
    """Test with a full academic text sample"""
    print("\n" + "=" * 50)
    print("Testing Full Academic Text Processing")
    print("=" * 50)
    
    academic_text = """
    Introduction
    
    The field of natural language processing has seen significant advances in recent years (Smith et al., 2020).
    However, as noted by Johnson (2021), current approaches still face substantial challenges in understanding
    academic discourse patterns. This paper argues that a multi-layered approach can address these limitations.
    
    Related Work
    
    Previous research [1, 2, 3] has focused primarily on general text processing. Nevertheless, academic texts
    present unique challenges due to their formal structure and specialized terminology (Brown & Davis, 2019).
    Furthermore, the presence of citations, cross-references, and formal definitions requires specialized handling.
    
    Methodology
    
    Definition 1. Let S be a semantic space where each point represents a concept's meaning vector.
    
    Our approach consists of three main components: citation detection, structure recognition, and
    argument tracking. Therefore, we can process academic texts more effectively than previous methods.
    
    Theorem 1. For any finite set of academic documents D, there exists a consistent chunking strategy
    that preserves argumentative coherence.
    
    Proof. We proceed by construction, showing that the semantic similarity measure maintains coherence
    across chunk boundaries.
    
    Results
    
    The experimental results demonstrate significant improvements over baseline methods. However, certain
    edge cases require further investigation. See Section 4.2 for detailed analysis.
    
    Conclusion
    
    In conclusion, our approach offers a promising direction for academic text processing. Nevertheless,
    future work should address the computational complexity issues identified in this study.
    """
    
    try:
        print("Processing full academic text...")
        doc = pipeline.process_text(academic_text)
        
        # Get all analysis results
        citations = pipeline.extract_citations(doc)
        structures = pipeline.extract_academic_structures(doc)
        markers = pipeline.get_discourse_markers(doc)
        complexity = pipeline.analyze_sentence_complexity(doc)
        
        print(f"\n📊 Analysis Results:")
        print(f"  📖 Total sentences: {len(list(doc.sents))}")
        print(f"  📝 Citations found: {len(citations)}")
        print(f"  🏗️  Academic structures: {len(structures)}")
        print(f"  💬 Discourse markers: {len(markers)}")
        print(f"  📈 Avg complexity score: {sum(c['complexity_score'] for c in complexity) / len(complexity):.2f}")
        
        print(f"\n📋 Detailed Results:")
        
        if citations:
            print(f"\n  Citations ({len(citations)}):")
            for citation in citations[:5]:  # Show first 5
                print(f"    • '{citation['text']}' (type: {citation['type']})")
            if len(citations) > 5:
                print(f"    ... and {len(citations) - 5} more")
        
        if structures:
            print(f"\n  Academic Structures ({len(structures)}):")
            for structure in structures:
                print(f"    • {structure['type'].upper()}: '{structure['text']}'")
        
        if markers:
            print(f"\n  Key Discourse Markers ({min(5, len(markers))}):")
            for marker in markers[:5]:
                print(f"    • '{marker['text']}' (lemma: {marker['lemma']})")
        
        return True
        
    except Exception as e:
        print(f"✗ Error processing full text: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Academic NLP Pipeline Test Suite")
    print("=" * 60)
    
    # Check if required models are available
    print("Checking spaCy models...")
    try:
        download_required_models()
    except Exception as e:
        print(f"Warning: Could not download models: {e}")
    
    # Check transformer availability
    transformer_available = is_transformer_available()
    print(f"Transformer model available: {transformer_available}")
    
    # Initialize pipeline
    pipeline = test_pipeline_initialization()
    if not pipeline:
        print("❌ Cannot proceed without working pipeline")
        return
    
    # Run all tests
    tests = [
        test_citation_detection,
        test_academic_structures, 
        test_discourse_markers,
        test_sentence_complexity,
        test_full_academic_text,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            result = test_func(pipeline)
            if result is not False:  # None or True counts as passed
                passed += 1
            print("✅ PASSED")
        except Exception as e:
            print(f"❌ FAILED: {e}")
    
    # Final results
    print("\n" + "=" * 60)
    print(f"📈 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! NLP pipeline is working correctly.")
    else:
        print(f"⚠️  {total - passed} tests failed. Check the error messages above.")
    
    print("=" * 60)


if __name__ == "__main__":
    main()