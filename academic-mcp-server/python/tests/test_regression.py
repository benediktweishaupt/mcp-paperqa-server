"""
Regression tests to prevent quality degradation in academic PDF processing
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import hashlib
from typing import Dict, List, Any, Optional
import pickle

# Import modules for testing
try:
    from pdf_processing import PDFProcessor, ProcessorConfig
    from pdf_processing.models import Document, Metadata, Section, Paragraph
    from text_chunking.nlp_pipeline import AcademicNLPPipeline
    REGRESSION_MODULES_AVAILABLE = True
except ImportError:
    REGRESSION_MODULES_AVAILABLE = False


class RegressionTestBase:
    """Base class for regression testing with baseline management"""
    
    def __init__(self):
        self.baseline_dir = Path(__file__).parent / "baselines"
        self.baseline_dir.mkdir(exist_ok=True)
        self.tolerance = {
            'text_accuracy': 0.95,
            'structure_accuracy': 0.90,
            'metadata_completeness': 0.85,
            'processing_time_factor': 2.0  # Allow 2x slower than baseline
        }
    
    def save_baseline(self, test_name: str, results: Dict[str, Any]):
        """Save baseline results for future comparisons"""
        baseline_file = self.baseline_dir / f"{test_name}_baseline.json"
        
        # Add timestamp and version info
        results['timestamp'] = "2025-08-11"  # Current implementation date
        results['version'] = "1.0.0"
        
        with open(baseline_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
    
    def load_baseline(self, test_name: str) -> Optional[Dict[str, Any]]:
        """Load baseline results for comparison"""
        baseline_file = self.baseline_dir / f"{test_name}_baseline.json"
        
        if not baseline_file.exists():
            return None
        
        with open(baseline_file, 'r') as f:
            return json.load(f)
    
    def compare_with_baseline(self, test_name: str, current_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compare current results with baseline"""
        baseline = self.load_baseline(test_name)
        
        if baseline is None:
            # No baseline exists, save current as baseline
            self.save_baseline(test_name, current_results)
            return {
                'status': 'baseline_created',
                'message': 'No baseline found, current results saved as baseline'
            }
        
        comparison = {
            'status': 'pass',
            'regressions': [],
            'improvements': [],
            'details': {}
        }
        
        # Compare key metrics
        for metric in ['text_accuracy', 'structure_accuracy', 'metadata_completeness']:
            if metric in both_results := {metric: (baseline.get(metric), current_results.get(metric))}:
                baseline_val, current_val = both_results[metric]
                
                if baseline_val is not None and current_val is not None:
                    threshold = baseline_val * self.tolerance[metric]
                    
                    if current_val < threshold:
                        comparison['regressions'].append({
                            'metric': metric,
                            'baseline': baseline_val,
                            'current': current_val,
                            'threshold': threshold,
                            'degradation': (baseline_val - current_val) / baseline_val
                        })
                        comparison['status'] = 'regression_detected'
                    elif current_val > baseline_val * 1.05:  # 5% improvement threshold
                        comparison['improvements'].append({
                            'metric': metric,
                            'baseline': baseline_val,
                            'current': current_val,
                            'improvement': (current_val - baseline_val) / baseline_val
                        })
                
                comparison['details'][metric] = {
                    'baseline': baseline_val,
                    'current': current_val,
                    'change': current_val - baseline_val if all([baseline_val, current_val]) else None
                }
        
        # Compare processing time
        if 'processing_time' in baseline and 'processing_time' in current_results:
            baseline_time = baseline['processing_time']
            current_time = current_results['processing_time']
            
            if current_time > baseline_time * self.tolerance['processing_time_factor']:
                comparison['regressions'].append({
                    'metric': 'processing_time',
                    'baseline': baseline_time,
                    'current': current_time,
                    'slowdown_factor': current_time / baseline_time
                })
                comparison['status'] = 'regression_detected'
        
        return comparison


class TestTextExtractionRegression(RegressionTestBase):
    """Regression tests for text extraction quality"""
    
    @pytest.fixture
    def sample_documents(self):
        """Sample documents with known ground truth"""
        return {
            'ieee_paper': {
                'content': '''
                IEEE TRANSACTIONS ON PATTERN ANALYSIS AND MACHINE INTELLIGENCE
                
                A Novel Approach to Deep Learning for Computer Vision
                
                John Smith¹, Jane Doe², Robert Johnson¹
                ¹MIT CSAIL, ²Stanford AI Lab
                
                Abstract—This paper presents a novel deep learning approach
                for computer vision tasks. We achieve state-of-the-art results
                on benchmark datasets.
                
                Index Terms—Deep learning, computer vision, neural networks
                
                I. INTRODUCTION
                Computer vision has been revolutionized by deep learning...
                ''',
                'expected_structure': {
                    'title': 'A Novel Approach to Deep Learning for Computer Vision',
                    'authors': ['John Smith', 'Jane Doe', 'Robert Johnson'],
                    'sections': ['Introduction'],
                    'has_abstract': True,
                    'has_keywords': True
                }
            },
            'acm_paper': {
                'content': '''
                ACM Computing Surveys
                
                Machine Learning in Software Engineering: A Comprehensive Survey
                
                Alice Brown, Bob Wilson, Carol Davis, David Evans
                University of Technology, Software Engineering Department
                
                ABSTRACT
                This survey provides a comprehensive overview of machine learning
                applications in software engineering. We analyze 200+ papers
                published in the last decade.
                
                CCS Concepts: • Software and its engineering → Software verification;
                • Computing methodologies → Machine learning;
                
                1 INTRODUCTION
                The intersection of machine learning and software engineering...
                
                1.1 Research Questions
                This survey addresses the following research questions...
                ''',
                'expected_structure': {
                    'title': 'Machine Learning in Software Engineering: A Comprehensive Survey',
                    'authors': ['Alice Brown', 'Bob Wilson', 'Carol Davis', 'David Evans'],
                    'sections': ['Introduction'],
                    'subsections': ['Research Questions'],
                    'has_abstract': True,
                    'has_keywords': True
                }
            }
        }
    
    def test_text_extraction_quality_ieee(self, sample_documents):
        """Test text extraction quality for IEEE format papers"""
        if not REGRESSION_MODULES_AVAILABLE:
            pytest.skip("Regression modules not available")
        
        ieee_doc = sample_documents['ieee_paper']
        
        with patch('pdf_processing.extractors.pymupdf_extractor.fitz') as mock_fitz:
            self._setup_extraction_mock(mock_fitz, ieee_doc['content'])
            
            processor = PDFProcessor()
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(b'Mock IEEE PDF')
                temp_file.flush()
                
                try:
                    import time
                    start_time = time.time()
                    document = processor.process_document(temp_file.name)
                    processing_time = time.time() - start_time
                    
                    # Calculate quality metrics
                    results = self._calculate_extraction_quality(document, ieee_doc['expected_structure'])
                    results['processing_time'] = processing_time
                    results['document_type'] = 'ieee'
                    
                    # Compare with baseline
                    comparison = self.compare_with_baseline('ieee_text_extraction', results)
                    
                    # Assert no significant regressions
                    if comparison['status'] == 'regression_detected':
                        regression_details = "\\n".join([
                            f"- {r['metric']}: {r['current']:.3f} < {r['threshold']:.3f} (baseline: {r['baseline']:.3f})"
                            for r in comparison['regressions']
                        ])
                        pytest.fail(f"Text extraction quality regression detected:\\n{regression_details}")
                    
                    # Verify minimum quality thresholds
                    assert results['text_accuracy'] >= 0.90, "Text accuracy below minimum threshold"
                    assert results['structure_accuracy'] >= 0.85, "Structure accuracy below minimum threshold"
                    
                finally:
                    os.unlink(temp_file.name)
    
    def test_text_extraction_quality_acm(self, sample_documents):
        """Test text extraction quality for ACM format papers"""
        if not REGRESSION_MODULES_AVAILABLE:
            pytest.skip("Regression modules not available")
        
        acm_doc = sample_documents['acm_paper']
        
        with patch('pdf_processing.extractors.pymupdf_extractor.fitz') as mock_fitz:
            self._setup_extraction_mock(mock_fitz, acm_doc['content'])
            
            processor = PDFProcessor()
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(b'Mock ACM PDF')
                temp_file.flush()
                
                try:
                    import time
                    start_time = time.time()
                    document = processor.process_document(temp_file.name)
                    processing_time = time.time() - start_time
                    
                    # Calculate quality metrics
                    results = self._calculate_extraction_quality(document, acm_doc['expected_structure'])
                    results['processing_time'] = processing_time
                    results['document_type'] = 'acm'
                    
                    # Compare with baseline
                    comparison = self.compare_with_baseline('acm_text_extraction', results)
                    
                    # Assert no significant regressions
                    if comparison['status'] == 'regression_detected':
                        regression_details = "\\n".join([
                            f"- {r['metric']}: {r['current']:.3f} < {r['threshold']:.3f} (baseline: {r['baseline']:.3f})"
                            for r in comparison['regressions']
                        ])
                        pytest.fail(f"Text extraction quality regression detected:\\n{regression_details}")
                    
                    # Test hierarchical structure detection
                    assert len(document.sections) >= 1, "Should detect at least one main section"
                    intro_section = next((s for s in document.sections if 'Introduction' in s.title), None)
                    assert intro_section is not None, "Should detect Introduction section"
                    
                finally:
                    os.unlink(temp_file.name)
    
    def _setup_extraction_mock(self, mock_fitz, content):
        """Setup mock for text extraction"""
        mock_doc = Mock()
        mock_page = Mock()
        
        mock_page.get_text.return_value = content
        mock_page.number = 0
        
        mock_doc.page_count = 1
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.__getitem__ = Mock(return_value=mock_page)
        mock_doc.metadata = {'title': 'Mock Title', 'author': 'Mock Author'}
        
        mock_fitz.open.return_value = mock_doc
    
    def _calculate_extraction_quality(self, document: Document, expected: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate extraction quality metrics"""
        results = {}
        
        # Text accuracy (based on title extraction)
        title_accuracy = 0.0
        if document.metadata and document.metadata.title and expected.get('title'):
            # Simple similarity based on shared words
            extracted_words = set(document.metadata.title.lower().split())
            expected_words = set(expected['title'].lower().split())
            if expected_words:
                title_accuracy = len(extracted_words.intersection(expected_words)) / len(expected_words)
        
        results['text_accuracy'] = title_accuracy
        
        # Structure accuracy
        structure_score = 0.0
        total_checks = 0
        
        # Check sections
        if expected.get('sections'):
            expected_sections = expected['sections']
            found_sections = [s.title for s in document.sections]
            
            for expected_section in expected_sections:
                total_checks += 1
                if any(expected_section.lower() in found.lower() for found in found_sections):
                    structure_score += 1
        
        # Check subsections
        if expected.get('subsections'):
            expected_subsections = expected['subsections']
            found_subsections = []
            for section in document.sections:
                found_subsections.extend([sub.title for sub in section.subsections])
            
            for expected_subsection in expected_subsections:
                total_checks += 1
                if any(expected_subsection.lower() in found.lower() for found in found_subsections):
                    structure_score += 1
        
        # Check abstract presence
        if expected.get('has_abstract'):
            total_checks += 1
            if (document.metadata and document.metadata.abstract) or \
               any('abstract' in s.title.lower() for s in document.sections):
                structure_score += 1
        
        # Check keywords presence
        if expected.get('has_keywords'):
            total_checks += 1
            if (document.metadata and document.metadata.keywords) or \
               any('keyword' in s.title.lower() or 'index term' in s.title.lower() for s in document.sections):
                structure_score += 1
        
        results['structure_accuracy'] = structure_score / max(total_checks, 1)
        
        # Metadata completeness
        metadata_score = 0.0
        metadata_checks = 0
        
        if document.metadata:
            # Title
            metadata_checks += 1
            if document.metadata.title:
                metadata_score += 1
            
            # Authors
            metadata_checks += 1
            if document.metadata.authors:
                metadata_score += 1
            
            # Abstract or keywords
            metadata_checks += 1
            if document.metadata.abstract or document.metadata.keywords:
                metadata_score += 1
        
        results['metadata_completeness'] = metadata_score / max(metadata_checks, 1)
        
        return results


class TestNLPPipelineRegression(RegressionTestBase):
    """Regression tests for NLP pipeline quality"""
    
    def test_nlp_processing_consistency(self):
        """Test that NLP processing maintains consistent results"""
        if not REGRESSION_MODULES_AVAILABLE:
            pytest.skip("Regression modules not available")
        
        # Sample academic text for consistent testing
        academic_text = """
        According to Smith et al. (2020), machine learning has revolutionized natural language processing.
        However, Johnson (2021) argues that traditional methods still have merit.
        
        Definition 1. A neural network is a computational model inspired by biological neural networks.
        
        Theorem 1. Every continuous function can be approximated by a neural network.
        
        Proof. We proceed by construction using universal approximation theory.
        
        Therefore, we conclude that neural networks are powerful computational tools.
        Furthermore, their applications continue to expand across various domains.
        """
        
        pipeline = AcademicNLPPipeline(enable_transformer=False)
        
        import time
        start_time = time.time()
        doc = pipeline.process_text(academic_text)
        processing_time = time.time() - start_time
        
        # Extract features
        citations = pipeline.extract_citations(doc)
        structures = pipeline.extract_academic_structures(doc)
        discourse_markers = pipeline.get_discourse_markers(doc)
        complexity_metrics = pipeline.analyze_sentence_complexity(doc)
        
        # Calculate quality metrics
        results = {
            'citations_found': len(citations),
            'structures_found': len(structures),
            'discourse_markers_found': len(discourse_markers),
            'sentences_analyzed': len(complexity_metrics),
            'processing_time': processing_time,
            'avg_complexity_score': sum(m['complexity_score'] for m in complexity_metrics) / max(len(complexity_metrics), 1)
        }
        
        # Expected baselines (based on current implementation)
        expected_citations = 2  # Smith et al. (2020), Johnson (2021)
        expected_structures = 3  # Definition 1, Theorem 1, Proof
        
        results['citation_accuracy'] = min(results['citations_found'] / expected_citations, 1.0) if expected_citations > 0 else 0
        results['structure_accuracy'] = min(results['structures_found'] / expected_structures, 1.0) if expected_structures > 0 else 0
        
        # Compare with baseline
        comparison = self.compare_with_baseline('nlp_pipeline_consistency', results)
        
        # Assert no regressions
        if comparison['status'] == 'regression_detected':
            regression_details = "\\n".join([
                f"- {r['metric']}: {r.get('current', 'N/A')} vs baseline {r.get('baseline', 'N/A')}"
                for r in comparison['regressions']
            ])
            pytest.fail(f"NLP pipeline regression detected:\\n{regression_details}")
        
        # Basic functionality checks
        assert len(complexity_metrics) > 0, "Should analyze sentence complexity"
        assert results['processing_time'] < 30.0, "Processing should complete in reasonable time"
    
    def test_citation_detection_stability(self):
        """Test citation detection stability across different formats"""
        if not REGRESSION_MODULES_AVAILABLE:
            pytest.skip("Regression modules not available")
        
        citation_test_cases = [
            "Smith et al. (2020) demonstrated significant improvements.",
            "According to Johnson (2021), the method is effective.", 
            "The results are consistent [1, 2, 3].",
            "See Jones and Brown (2019) for details.",
            "DOI: 10.1109/ACCESS.2023.1234567"
        ]
        
        pipeline = AcademicNLPPipeline(enable_transformer=False)
        
        total_citations = 0
        processing_times = []
        
        for test_case in citation_test_cases:
            import time
            start_time = time.time()
            doc = pipeline.process_text(test_case)
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
            
            citations = pipeline.extract_citations(doc)
            total_citations += len(citations)
        
        results = {
            'total_citations_detected': total_citations,
            'avg_processing_time': sum(processing_times) / len(processing_times),
            'detection_rate': total_citations / len(citation_test_cases)
        }
        
        # Compare with baseline
        comparison = self.compare_with_baseline('citation_detection_stability', results)
        
        # Assert stability
        if comparison['status'] == 'regression_detected':
            pytest.fail(f"Citation detection regression: {comparison['regressions']}")
        
        # Minimum functionality check
        assert total_citations >= 3, "Should detect at least 3 citations from test cases"


class TestMemoryAndResourceRegression(RegressionTestBase):
    """Regression tests for memory usage and resource consumption"""
    
    def test_memory_usage_stability(self):
        """Test that memory usage remains stable"""
        if not REGRESSION_MODULES_AVAILABLE:
            pytest.skip("Regression modules not available")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Measure baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create processor and process multiple documents
        processor = PDFProcessor()
        
        with patch('pdf_processing.extractors.pymupdf_extractor.fitz') as mock_fitz:
            # Setup mock
            mock_doc = Mock()
            mock_page = Mock()
            mock_page.get_text.return_value = "Sample text content for memory testing. " * 1000
            mock_page.number = 0
            mock_doc.page_count = 1
            mock_doc.__len__ = Mock(return_value=1) 
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            mock_doc.metadata = {'title': 'Memory Test'}
            mock_fitz.open.return_value = mock_doc
            
            # Process multiple documents
            documents = []
            memory_measurements = []
            
            for i in range(10):
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    temp_file.write(f'Mock PDF {i}'.encode())
                    temp_file.flush()
                    
                    try:
                        document = processor.process_document(temp_file.name)
                        documents.append(document)
                        
                        # Measure memory after each document
                        current_memory = process.memory_info().rss / 1024 / 1024  # MB
                        memory_measurements.append(current_memory)
                        
                    finally:
                        os.unlink(temp_file.name)
        
        # Calculate memory metrics
        peak_memory = max(memory_measurements)
        final_memory = memory_measurements[-1]
        memory_growth = final_memory - baseline_memory
        avg_per_document = memory_growth / 10
        
        results = {
            'baseline_memory_mb': baseline_memory,
            'peak_memory_mb': peak_memory,
            'final_memory_mb': final_memory,
            'memory_growth_mb': memory_growth,
            'avg_memory_per_document_mb': avg_per_document,
            'documents_processed': 10
        }
        
        # Compare with baseline
        comparison = self.compare_with_baseline('memory_usage_stability', results)
        
        # Check for memory regressions
        if comparison['status'] == 'regression_detected':
            memory_regressions = [r for r in comparison['regressions'] if 'memory' in r['metric']]
            if memory_regressions:
                pytest.fail(f"Memory usage regression detected: {memory_regressions}")
        
        # Hard limits to prevent runaway memory usage
        assert memory_growth < 500, f"Memory growth too high: {memory_growth} MB"
        assert avg_per_document < 50, f"Average memory per document too high: {avg_per_document} MB"
    
    def test_processing_time_regression(self):
        """Test processing time regression for standardized workload"""
        if not REGRESSION_MODULES_AVAILABLE:
            pytest.skip("Regression modules not available")
        
        # Standardized test content
        standard_content = """
        This is a standardized test document for performance regression testing.
        """ + "Standard paragraph content for testing processing speed. " * 100
        
        with patch('pdf_processing.extractors.pymupdf_extractor.fitz') as mock_fitz:
            # Setup mock
            mock_doc = Mock()
            mock_page = Mock()
            mock_page.get_text.return_value = standard_content
            mock_page.number = 0
            mock_doc.page_count = 1
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            mock_doc.metadata = {'title': 'Performance Test'}
            mock_fitz.open.return_value = mock_doc
            
            processor = PDFProcessor()
            
            # Run multiple iterations to get stable timing
            processing_times = []
            
            for i in range(5):
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    temp_file.write(f'Performance test {i}'.encode())
                    temp_file.flush()
                    
                    try:
                        import time
                        start_time = time.time()
                        document = processor.process_document(temp_file.name)
                        end_time = time.time()
                        
                        processing_times.append(end_time - start_time)
                        
                    finally:
                        os.unlink(temp_file.name)
        
        results = {
            'avg_processing_time': sum(processing_times) / len(processing_times),
            'min_processing_time': min(processing_times),
            'max_processing_time': max(processing_times),
            'std_dev': (sum((t - sum(processing_times)/len(processing_times))**2 for t in processing_times) / len(processing_times))**0.5,
            'iterations': len(processing_times)
        }
        
        # Compare with baseline
        comparison = self.compare_with_baseline('processing_time_regression', results)
        
        # Check for performance regressions
        if comparison['status'] == 'regression_detected':
            time_regressions = [r for r in comparison['regressions'] if 'time' in r['metric']]
            if time_regressions:
                pytest.fail(f"Processing time regression detected: {time_regressions}")
        
        # Absolute performance requirements
        assert results['avg_processing_time'] < 10.0, "Average processing time too slow"
        assert results['max_processing_time'] < 20.0, "Maximum processing time too slow"


if __name__ == "__main__":
    if REGRESSION_MODULES_AVAILABLE:
        print("🔄 Running regression tests...")
        
        try:
            # Text extraction regression tests
            test_text = TestTextExtractionRegression()
            print("✅ Text extraction regression tests setup complete")
        except Exception as e:
            print(f"❌ Text extraction regression tests failed: {e}")
        
        try:
            # NLP pipeline regression tests
            test_nlp = TestNLPPipelineRegression()
            test_nlp.test_nlp_processing_consistency()
            print("✅ NLP pipeline regression tests passed")
        except Exception as e:
            print(f"❌ NLP pipeline regression tests failed: {e}")
        
        try:
            # Memory and resource regression tests
            test_memory = TestMemoryAndResourceRegression()
            print("✅ Memory and resource regression tests setup complete")
        except Exception as e:
            print(f"❌ Memory regression tests failed: {e}")
        
        print("\n🎉 Regression testing framework complete!")
        print("📊 Baseline files will be created on first run for future comparisons")
        print("📈 Tests will detect quality degradation and performance regressions")
        
    else:
        print("⚠️  Regression test modules not available")
        print("📦 Install all requirements for full regression testing")