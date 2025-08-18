"""
Performance benchmarks for academic PDF processing pipeline
"""

import pytest
import time
import psutil
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, List, Any, Optional
import statistics
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading

# Import modules for testing
try:
    from pdf_processing import PDFProcessor, ProcessorConfig, ExtractionMethod
    from pdf_processing.models import Document, Metadata, Section, Paragraph
    from text_chunking.nlp_pipeline import AcademicNLPPipeline
    BENCHMARK_MODULES_AVAILABLE = True
except ImportError:
    BENCHMARK_MODULES_AVAILABLE = False


class PerformanceBenchmark:
    """Base class for performance benchmarking"""
    
    def __init__(self):
        self.results_dir = Path(__file__).parent / "benchmark_results"
        self.results_dir.mkdir(exist_ok=True)
        self.process = psutil.Process(os.getpid())
    
    def measure_memory_usage(self) -> Dict[str, float]:
        """Measure current memory usage"""
        memory_info = self.process.memory_info()
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
            'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
            'percent': self.process.memory_percent()
        }
    
    def measure_cpu_usage(self) -> float:
        """Measure CPU usage percentage"""
        return self.process.cpu_percent(interval=0.1)
    
    def create_mock_document(self, size_category: str = "medium") -> str:
        """Create mock document content of different sizes"""
        base_content = """
        Advanced Machine Learning Techniques for Academic Research
        
        John Smith¹, Jane Doe², Robert Johnson¹
        ¹MIT Computer Science, Cambridge, MA
        ²Stanford AI Lab, Stanford, CA
        
        Abstract
        This paper presents novel machine learning techniques specifically designed 
        for academic research applications. We introduce new architectures that 
        demonstrate significant improvements over existing methods.
        
        Keywords: machine learning, neural networks, academic research
        
        1. Introduction
        Machine learning has revolutionized many fields of research. In this work,
        we focus on developing techniques that are particularly suited for academic
        research workflows.
        
        1.1 Background
        Previous work in this area has established foundational principles.
        
        2. Methodology
        Our approach consists of three main components.
        
        2.1 Data Preprocessing
        We developed specialized preprocessing techniques.
        
        2.2 Model Architecture
        The proposed architecture builds upon existing frameworks.
        
        3. Experiments
        We conducted extensive experiments on benchmark datasets.
        
        4. Results
        Our method achieves state-of-the-art performance.
        
        5. Conclusion
        This work demonstrates the effectiveness of our approach.
        """
        
        if size_category == "small":
            return base_content
        elif size_category == "medium":
            return base_content * 5
        elif size_category == "large":
            return base_content * 20
        elif size_category == "xlarge":
            return base_content * 100
        else:
            return base_content
    
    def save_benchmark_results(self, benchmark_name: str, results: Dict[str, Any]):
        """Save benchmark results to file"""
        results_file = self.results_dir / f"{benchmark_name}_results.json"
        
        # Add timestamp and system info
        results['timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S")
        results['system_info'] = {
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
        }
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
    
    def setup_mock_extractor(self, mock_fitz, content: str):
        """Setup mock PDF extractor"""
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = content
        mock_page.number = 0
        mock_doc.page_count = 1
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.__getitem__ = Mock(return_value=mock_page)
        mock_doc.metadata = {'title': 'Benchmark Document', 'author': 'Benchmark Author'}
        mock_fitz.open.return_value = mock_doc


class TestProcessingSpeedBenchmarks(PerformanceBenchmark):
    """Benchmarks for processing speed across different document sizes"""
    
    @pytest.mark.performance
    def test_single_document_processing_speed(self):
        """Benchmark single document processing speed by size"""
        if not BENCHMARK_MODULES_AVAILABLE:
            pytest.skip("Benchmark modules not available")
        
        size_categories = ["small", "medium", "large"]
        results = {'processing_times': {}, 'throughput': {}, 'memory_usage': {}}
        
        with patch('pdf_processing.extractors.pymupdf_extractor.fitz') as mock_fitz:
            processor = PDFProcessor()
            
            for size_category in size_categories:
                content = self.create_mock_document(size_category)
                self.setup_mock_extractor(mock_fitz, content)
                
                # Measure processing time and memory
                processing_times = []
                memory_before = self.measure_memory_usage()
                
                # Run multiple iterations for statistical significance
                for _ in range(5):
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                        temp_file.write(f'Benchmark {size_category}'.encode())
                        temp_file.flush()
                        
                        try:
                            start_time = time.time()
                            document = processor.process_document(temp_file.name)
                            end_time = time.time()
                            
                            processing_times.append(end_time - start_time)
                            
                        finally:
                            os.unlink(temp_file.name)
                
                memory_after = self.measure_memory_usage()
                
                # Calculate statistics
                avg_time = statistics.mean(processing_times)
                std_dev = statistics.stdev(processing_times) if len(processing_times) > 1 else 0
                
                # Estimate content size (words)
                content_words = len(content.split())
                throughput_words_per_sec = content_words / avg_time
                
                results['processing_times'][size_category] = {
                    'average_seconds': avg_time,
                    'std_dev_seconds': std_dev,
                    'min_seconds': min(processing_times),
                    'max_seconds': max(processing_times),
                    'content_words': content_words
                }
                
                results['throughput'][size_category] = {
                    'words_per_second': throughput_words_per_sec,
                    'pages_per_minute': 60 / avg_time  # Assuming 1 page per document
                }
                
                results['memory_usage'][size_category] = {
                    'memory_delta_mb': memory_after['rss_mb'] - memory_before['rss_mb'],
                    'peak_memory_mb': memory_after['rss_mb']
                }
        
        # Save benchmark results
        self.save_benchmark_results('single_document_processing_speed', results)
        
        # Performance assertions
        assert results['processing_times']['small']['average_seconds'] < 2.0, "Small documents should process in <2 seconds"
        assert results['processing_times']['medium']['average_seconds'] < 5.0, "Medium documents should process in <5 seconds"
        assert results['processing_times']['large']['average_seconds'] < 15.0, "Large documents should process in <15 seconds"
        
        # Throughput assertions
        assert results['throughput']['small']['words_per_second'] > 100, "Should process >100 words/second"
        
        print(f"\\n📊 Processing Speed Benchmark Results:")
        for size in size_categories:
            avg_time = results['processing_times'][size]['average_seconds']
            throughput = results['throughput'][size]['words_per_second']
            print(f"  {size.capitalize()}: {avg_time:.2f}s avg, {throughput:.0f} words/sec")
    
    @pytest.mark.performance 
    def test_batch_processing_performance(self):
        """Benchmark batch processing performance"""
        if not BENCHMARK_MODULES_AVAILABLE:
            pytest.skip("Benchmark modules not available")
        
        batch_sizes = [1, 5, 10, 20]
        results = {'batch_performance': {}}
        
        with patch('pdf_processing.extractors.pymupdf_extractor.fitz') as mock_fitz:
            content = self.create_mock_document("medium")
            self.setup_mock_extractor(mock_fitz, content)
            
            for batch_size in batch_sizes:
                processor = PDFProcessor()
                
                # Create batch of temporary files
                temp_files = []
                for i in range(batch_size):
                    temp_file = tempfile.NamedTemporaryFile(suffix=f'_batch_{i}.pdf', delete=False)
                    temp_file.write(f'Batch document {i}'.encode())
                    temp_file.flush()
                    temp_files.append(temp_file.name)
                
                try:
                    # Measure batch processing time
                    memory_before = self.measure_memory_usage()
                    start_time = time.time()
                    
                    documents = []
                    for file_path in temp_files:
                        document = processor.process_document(file_path)
                        documents.append(document)
                    
                    end_time = time.time()
                    memory_after = self.measure_memory_usage()
                    
                    total_time = end_time - start_time
                    avg_time_per_doc = total_time / batch_size
                    
                    results['batch_performance'][batch_size] = {
                        'total_time_seconds': total_time,
                        'avg_time_per_document_seconds': avg_time_per_doc,
                        'documents_per_minute': (batch_size / total_time) * 60,
                        'memory_delta_mb': memory_after['rss_mb'] - memory_before['rss_mb'],
                        'memory_per_document_mb': (memory_after['rss_mb'] - memory_before['rss_mb']) / batch_size
                    }
                    
                finally:
                    # Cleanup
                    for file_path in temp_files:
                        if os.path.exists(file_path):
                            os.unlink(file_path)
        
        self.save_benchmark_results('batch_processing_performance', results)
        
        # Performance assertions
        single_doc_time = results['batch_performance'][1]['avg_time_per_document_seconds']
        batch_20_time = results['batch_performance'][20]['avg_time_per_document_seconds']
        
        # Batch processing should not be significantly slower per document
        assert batch_20_time < single_doc_time * 1.5, "Batch processing efficiency should not degrade significantly"
        
        print(f"\\n📈 Batch Processing Performance:")
        for batch_size in batch_sizes:
            perf = results['batch_performance'][batch_size]
            print(f"  Batch size {batch_size}: {perf['avg_time_per_document_seconds']:.2f}s/doc, {perf['documents_per_minute']:.1f} docs/min")


class TestMemoryBenchmarks(PerformanceBenchmark):
    """Benchmarks for memory usage and memory efficiency"""
    
    @pytest.mark.performance
    def test_memory_usage_scaling(self):
        """Test how memory usage scales with document size"""
        if not BENCHMARK_MODULES_AVAILABLE:
            pytest.skip("Benchmark modules not available")
        
        size_categories = ["small", "medium", "large", "xlarge"]
        results = {'memory_scaling': {}, 'memory_efficiency': {}}
        
        with patch('pdf_processing.extractors.pymupdf_extractor.fitz') as mock_fitz:
            
            for size_category in size_categories:
                content = self.create_mock_document(size_category)
                self.setup_mock_extractor(mock_fitz, content)
                
                processor = PDFProcessor()
                
                # Measure memory before processing
                memory_before = self.measure_memory_usage()
                
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    temp_file.write(f'Memory test {size_category}'.encode())
                    temp_file.flush()
                    
                    try:
                        # Process document and measure memory
                        document = processor.process_document(temp_file.name)
                        memory_during = self.measure_memory_usage()
                        
                        # Force garbage collection and measure again
                        import gc
                        gc.collect()
                        memory_after_gc = self.measure_memory_usage()
                        
                        content_size_kb = len(content) / 1024
                        
                        results['memory_scaling'][size_category] = {
                            'content_size_kb': content_size_kb,
                            'memory_before_mb': memory_before['rss_mb'],
                            'memory_during_mb': memory_during['rss_mb'],
                            'memory_after_gc_mb': memory_after_gc['rss_mb'],
                            'peak_delta_mb': memory_during['rss_mb'] - memory_before['rss_mb'],
                            'persistent_delta_mb': memory_after_gc['rss_mb'] - memory_before['rss_mb']
                        }
                        
                        # Calculate memory efficiency (KB content per MB memory)
                        if results['memory_scaling'][size_category]['peak_delta_mb'] > 0:
                            efficiency = content_size_kb / results['memory_scaling'][size_category]['peak_delta_mb'] / 1024
                            results['memory_efficiency'][size_category] = efficiency
                        
                    finally:
                        os.unlink(temp_file.name)
        
        self.save_benchmark_results('memory_usage_scaling', results)
        
        # Memory efficiency assertions
        for size_category in size_categories:
            peak_delta = results['memory_scaling'][size_category]['peak_delta_mb']
            assert peak_delta < 200, f"Peak memory usage for {size_category} documents should be <200MB"
            
            persistent_delta = results['memory_scaling'][size_category]['persistent_delta_mb']
            assert persistent_delta < 50, f"Persistent memory usage for {size_category} documents should be <50MB"
        
        print(f"\\n🧠 Memory Usage Scaling:")
        for size in size_categories:
            scaling = results['memory_scaling'][size]
            efficiency = results['memory_efficiency'].get(size, 0)
            print(f"  {size.capitalize()}: {scaling['peak_delta_mb']:.1f}MB peak, {scaling['persistent_delta_mb']:.1f}MB persistent, {efficiency:.2f} efficiency")
    
    @pytest.mark.performance
    def test_memory_leak_detection(self):
        """Test for memory leaks during repeated processing"""
        if not BENCHMARK_MODULES_AVAILABLE:
            pytest.skip("Benchmark modules not available")
        
        with patch('pdf_processing.extractors.pymupdf_extractor.fitz') as mock_fitz:
            content = self.create_mock_document("medium")
            self.setup_mock_extractor(mock_fitz, content)
            
            processor = PDFProcessor()
            memory_measurements = []
            
            # Process multiple documents and track memory
            for iteration in range(20):
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    temp_file.write(f'Leak test {iteration}'.encode())
                    temp_file.flush()
                    
                    try:
                        document = processor.process_document(temp_file.name)
                        
                        # Force garbage collection and measure
                        import gc
                        gc.collect()
                        memory_info = self.measure_memory_usage()
                        memory_measurements.append({
                            'iteration': iteration,
                            'memory_mb': memory_info['rss_mb'],
                            'memory_percent': memory_info['percent']
                        })
                        
                    finally:
                        os.unlink(temp_file.name)
                
                # Brief pause to allow system cleanup
                time.sleep(0.1)
            
            # Analyze memory trend
            initial_memory = memory_measurements[0]['memory_mb']
            final_memory = memory_measurements[-1]['memory_mb']
            memory_growth = final_memory - initial_memory
            
            # Calculate linear trend
            iterations = [m['iteration'] for m in memory_measurements]
            memories = [m['memory_mb'] for m in memory_measurements]
            
            # Simple linear regression for trend
            n = len(iterations)
            sum_x = sum(iterations)
            sum_y = sum(memories)
            sum_xy = sum(x * y for x, y in zip(iterations, memories))
            sum_x2 = sum(x * x for x in iterations)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            results = {
                'memory_leak_analysis': {
                    'initial_memory_mb': initial_memory,
                    'final_memory_mb': final_memory,
                    'total_growth_mb': memory_growth,
                    'growth_per_iteration_mb': slope,
                    'iterations_tested': n,
                    'memory_measurements': memory_measurements[-5:]  # Keep last 5 measurements
                }
            }
            
            self.save_benchmark_results('memory_leak_detection', results)
            
            # Memory leak assertions
            assert memory_growth < 100, f"Total memory growth should be <100MB, got {memory_growth:.1f}MB"
            assert slope < 1.0, f"Memory growth per iteration should be <1MB, got {slope:.3f}MB/iteration"
            
            print(f"\\n💧 Memory Leak Analysis:")
            print(f"  Total growth: {memory_growth:.1f}MB over {n} iterations")
            print(f"  Growth rate: {slope:.3f}MB per iteration")
            print(f"  Result: {'✅ No significant leak detected' if slope < 0.5 else '⚠️ Potential memory leak'}")


class TestNLPPerformanceBenchmarks(PerformanceBenchmark):
    """Benchmarks for NLP pipeline performance"""
    
    @pytest.mark.performance
    def test_nlp_processing_speed(self):
        """Benchmark NLP processing speed"""
        if not BENCHMARK_MODULES_AVAILABLE:
            pytest.skip("Benchmark modules not available")
        
        # Test different text sizes
        text_sizes = {
            'short': "This is a short academic text with one citation (Smith, 2023).",
            'medium': """
            According to Smith et al. (2020), machine learning has revolutionized many fields.
            However, Johnson (2021) argues that traditional approaches still have merit.
            
            Definition 1. A neural network is a computational model.
            
            Therefore, we conclude that both approaches have value.
            Furthermore, future research should explore hybrid methods.
            """ * 10,
            'long': """
            This is a comprehensive academic text for testing NLP processing performance.
            According to numerous researchers (Smith et al., 2020; Johnson, 2021; Brown & Davis, 2022),
            the field of natural language processing has seen remarkable advances.
            
            Definition 1. Natural language processing is the ability of computers to understand human language.
            
            Theorem 1. Every context-free language can be recognized by a pushdown automaton.
            
            Proof. The proof follows by construction of the automaton.
            
            In conclusion, therefore, we can see that the integration of multiple approaches
            leads to better outcomes. Furthermore, the evidence suggests that hybrid methods
            will dominate future research directions.
            """ * 100
        }
        
        pipeline = AcademicNLPPipeline(enable_transformer=False)
        results = {'nlp_performance': {}}
        
        for size_name, text in text_sizes.items():
            processing_times = []
            memory_before = self.measure_memory_usage()
            
            # Multiple runs for statistical significance
            for _ in range(5):
                start_time = time.time()
                doc = pipeline.process_text(text)
                
                # Extract all features
                citations = pipeline.extract_citations(doc)
                structures = pipeline.extract_academic_structures(doc)
                discourse_markers = pipeline.get_discourse_markers(doc)
                complexity = pipeline.analyze_sentence_complexity(doc)
                
                end_time = time.time()
                processing_times.append(end_time - start_time)
            
            memory_after = self.measure_memory_usage()
            
            # Calculate statistics
            avg_time = statistics.mean(processing_times)
            text_words = len(text.split())
            text_chars = len(text)
            
            results['nlp_performance'][size_name] = {
                'text_words': text_words,
                'text_characters': text_chars,
                'avg_processing_time_seconds': avg_time,
                'words_per_second': text_words / avg_time,
                'characters_per_second': text_chars / avg_time,
                'memory_delta_mb': memory_after['rss_mb'] - memory_before['rss_mb'],
                'features_extracted': {
                    'citations': len(citations),
                    'structures': len(structures),
                    'discourse_markers': len(discourse_markers),
                    'sentences_analyzed': len(complexity)
                }
            }
        
        self.save_benchmark_results('nlp_processing_speed', results)
        
        # Performance assertions
        assert results['nlp_performance']['short']['avg_processing_time_seconds'] < 1.0, "Short text should process in <1 second"
        assert results['nlp_performance']['medium']['avg_processing_time_seconds'] < 5.0, "Medium text should process in <5 seconds"
        assert results['nlp_performance']['long']['avg_processing_time_seconds'] < 30.0, "Long text should process in <30 seconds"
        
        # Throughput assertions
        assert results['nlp_performance']['short']['words_per_second'] > 50, "Should process >50 words/second"
        
        print(f"\\n🔤 NLP Processing Performance:")
        for size in text_sizes.keys():
            perf = results['nlp_performance'][size]
            print(f"  {size.capitalize()}: {perf['avg_processing_time_seconds']:.2f}s, {perf['words_per_second']:.0f} words/sec")


class TestConcurrencyBenchmarks(PerformanceBenchmark):
    """Benchmarks for concurrent processing performance"""
    
    @pytest.mark.performance
    def test_thread_concurrent_processing(self):
        """Test performance with thread-based concurrency"""
        if not BENCHMARK_MODULES_AVAILABLE:
            pytest.skip("Benchmark modules not available")
        
        thread_counts = [1, 2, 4, 8]
        results = {'thread_concurrency': {}}
        
        def process_single_document(document_id):
            """Process a single document in a thread"""
            with patch('pdf_processing.extractors.pymupdf_extractor.fitz') as mock_fitz:
                content = self.create_mock_document("medium")
                self.setup_mock_extractor(mock_fitz, content)
                
                processor = PDFProcessor()
                
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    temp_file.write(f'Thread test {document_id}'.encode())
                    temp_file.flush()
                    
                    try:
                        start_time = time.time()
                        document = processor.process_document(temp_file.name)
                        end_time = time.time()
                        return end_time - start_time
                    finally:
                        os.unlink(temp_file.name)
        
        for thread_count in thread_counts:
            memory_before = self.measure_memory_usage()
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                # Submit 20 documents for processing
                futures = [executor.submit(process_single_document, i) for i in range(20)]
                processing_times = [future.result() for future in futures]
            
            total_time = time.time() - start_time
            memory_after = self.measure_memory_usage()
            
            results['thread_concurrency'][thread_count] = {
                'total_wall_time_seconds': total_time,
                'documents_processed': len(processing_times),
                'avg_processing_time_seconds': statistics.mean(processing_times),
                'documents_per_minute': (len(processing_times) / total_time) * 60,
                'speedup_factor': results['thread_concurrency'][1]['total_wall_time_seconds'] / total_time if thread_count > 1 and 1 in results['thread_concurrency'] else 1.0,
                'memory_delta_mb': memory_after['rss_mb'] - memory_before['rss_mb']
            }
        
        self.save_benchmark_results('thread_concurrent_processing', results)
        
        # Concurrency efficiency assertions
        single_thread_time = results['thread_concurrency'][1]['total_wall_time_seconds']
        four_thread_time = results['thread_concurrency'][4]['total_wall_time_seconds']
        
        speedup = single_thread_time / four_thread_time
        assert speedup > 1.5, f"4-thread processing should show >1.5x speedup, got {speedup:.2f}x"
        
        print(f"\\n⚡ Thread Concurrency Performance:")
        for thread_count in thread_counts:
            perf = results['thread_concurrency'][thread_count]
            print(f"  {thread_count} threads: {perf['total_wall_time_seconds']:.1f}s total, {perf['speedup_factor']:.2f}x speedup")
    
    @pytest.mark.performance
    def test_memory_efficiency_under_load(self):
        """Test memory efficiency under concurrent load"""
        if not BENCHMARK_MODULES_AVAILABLE:
            pytest.skip("Benchmark modules not available")
        
        with patch('pdf_processing.extractors.pymupdf_extractor.fitz') as mock_fitz:
            content = self.create_mock_document("large")
            self.setup_mock_extractor(mock_fitz, content)
            
            memory_samples = []
            
            def monitor_memory():
                """Monitor memory usage during processing"""
                while True:
                    try:
                        memory_info = self.measure_memory_usage()
                        memory_samples.append({
                            'timestamp': time.time(),
                            'memory_mb': memory_info['rss_mb'],
                            'memory_percent': memory_info['percent']
                        })
                        time.sleep(0.1)  # Sample every 100ms
                    except:
                        break
            
            # Start memory monitoring thread
            monitor_thread = threading.Thread(target=monitor_memory, daemon=True)
            monitor_thread.start()
            
            # Process documents concurrently
            def process_document(doc_id):
                processor = PDFProcessor()
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    temp_file.write(f'Load test {doc_id}'.encode())
                    temp_file.flush()
                    try:
                        document = processor.process_document(temp_file.name)
                        return True
                    except:
                        return False
                    finally:
                        os.unlink(temp_file.name)
            
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(process_document, i) for i in range(10)]
                results_list = [future.result() for future in futures]
            
            total_time = time.time() - start_time
            
            # Stop monitoring and analyze
            monitor_thread = None  # Signal to stop monitoring
            
            if memory_samples:
                peak_memory = max(sample['memory_mb'] for sample in memory_samples)
                initial_memory = memory_samples[0]['memory_mb'] 
                memory_growth = peak_memory - initial_memory
                
                results = {
                    'load_testing': {
                        'documents_processed': sum(results_list),
                        'processing_time_seconds': total_time,
                        'initial_memory_mb': initial_memory,
                        'peak_memory_mb': peak_memory,
                        'memory_growth_mb': memory_growth,
                        'successful_processing': all(results_list),
                        'memory_samples_count': len(memory_samples)
                    }
                }
                
                self.save_benchmark_results('memory_efficiency_under_load', results)
                
                # Load testing assertions
                assert results['load_testing']['successful_processing'], "All documents should process successfully"
                assert memory_growth < 500, f"Memory growth under load should be <500MB, got {memory_growth:.1f}MB"
                
                print(f"\\n🔥 Memory Efficiency Under Load:")
                print(f"  Peak memory: {peak_memory:.1f}MB (growth: {memory_growth:.1f}MB)")
                print(f"  Processing time: {total_time:.1f}s for {sum(results_list)} documents")


if __name__ == "__main__":
    if BENCHMARK_MODULES_AVAILABLE:
        print("🏁 Running performance benchmarks...")
        
        try:
            # Processing speed benchmarks
            speed_test = TestProcessingSpeedBenchmarks()
            speed_test.test_single_document_processing_speed()
            print("✅ Processing speed benchmarks completed")
        except Exception as e:
            print(f"❌ Processing speed benchmarks failed: {e}")
        
        try:
            # Memory benchmarks
            memory_test = TestMemoryBenchmarks()
            memory_test.test_memory_usage_scaling()
            print("✅ Memory benchmarks completed")
        except Exception as e:
            print(f"❌ Memory benchmarks failed: {e}")
        
        try:
            # NLP performance benchmarks
            nlp_test = TestNLPPerformanceBenchmarks()
            nlp_test.test_nlp_processing_speed()
            print("✅ NLP performance benchmarks completed")
        except Exception as e:
            print(f"❌ NLP performance benchmarks failed: {e}")
        
        try:
            # Concurrency benchmarks
            concurrency_test = TestConcurrencyBenchmarks()
            print("✅ Concurrency benchmarks setup completed")
        except Exception as e:
            print(f"❌ Concurrency benchmarks failed: {e}")
        
        print("\\n🏆 Performance benchmarking complete!")
        print("📊 Results saved to benchmark_results/ directory")
        print("🎯 Performance targets:")
        print("  - Single document: <5s for medium docs")
        print("  - Memory usage: <200MB peak per document")
        print("  - Throughput: >100 words/second")
        print("  - Concurrency: >1.5x speedup with 4 threads")
        
    else:
        print("⚠️  Benchmark modules not available")
        print("📦 Install all requirements for performance benchmarking")