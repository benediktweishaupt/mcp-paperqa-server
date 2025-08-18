# Academic MCP Server - Testing Framework

This comprehensive testing framework ensures the quality, performance, and reliability of the Academic MCP Server's PDF processing capabilities.

## 📋 Table of Contents

- [Overview](#overview)
- [Test Categories](#test-categories)
- [Quick Start](#quick-start)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Data](#test-data)
- [Continuous Integration](#continuous-integration)
- [Performance Benchmarks](#performance-benchmarks)
- [Quality Assurance](#quality-assurance)

## 🎯 Overview

The testing framework provides comprehensive coverage for:

- **PDF Processing Engine**: Text extraction, structure detection, metadata parsing
- **NLP Pipeline**: Academic text analysis, citation detection, discourse markers
- **Layout Analysis**: Multi-column detection, reading order processing
- **Integration**: End-to-end document processing workflows
- **Performance**: Speed, memory usage, and scalability benchmarks
- **Quality**: Regression testing and quality maintenance

## 📂 Test Categories

### Unit Tests (`unit`)
- **Basic Functionality** (`test_basic_functionality.py`): Core imports and initialization
- **Text Extraction** (`test_text_extraction.py`): PDF text extraction components
- **Structure Detection** (`test_structure_detection.py`): Document structure analysis
- **Metadata Extraction** (`test_metadata_extraction.py`): Metadata parsing and validation
- **Multi-column Layout** (`test_multicolumn_layout.py`): Layout detection and processing
- **NLP Pipeline** (`text_chunking/test_nlp_pipeline.py`): Academic text processing

### Integration Tests (`integration`)
- **End-to-End Processing** (`integration/test_end_to_end_processing.py`): Complete workflows

### Regression Tests (`regression`)
- **Quality Maintenance** (`test_regression.py`): Prevent quality degradation over time

### Performance Tests (`performance`)
- **Benchmarks** (`performance/test_benchmarks.py`): Speed, memory, and scalability tests

## 🚀 Quick Start

### Prerequisites

```bash
# Install Python 3.9.18 (required)
pyenv install 3.9.18
pyenv local 3.9.18

# Install dependencies
cd python/
pip install -r requirements.txt

# Install spaCy model
python -m spacy download en_core_web_sm

# Install testing dependencies
pip install pytest pytest-asyncio pytest-cov psutil
```

### Running All Tests

```bash
# Run comprehensive test suite
python tests/run_all_tests.py

# Run only required tests (faster)
python tests/run_all_tests.py --required

# Run specific categories
python tests/run_all_tests.py --categories unit integration
```

### Running Individual Test Files

```bash
# Run with pytest
pytest tests/test_basic_functionality.py -v
pytest tests/test_text_extraction.py -v
pytest tests/integration/test_end_to_end_processing.py -v

# Run with performance markers
pytest tests/performance/test_benchmarks.py -m performance -v
```

## 🏗️ Test Structure

```
tests/
├── README.md                          # This documentation
├── run_all_tests.py                   # Comprehensive test runner
│
├── Unit Tests
├── test_basic_functionality.py        # Core functionality tests  
├── test_text_extraction.py            # Text extraction components
├── test_structure_detection.py        # Structure analysis tests
├── test_metadata_extraction.py        # Metadata processing tests
├── test_multicolumn_layout.py         # Layout analysis tests
├── test_regression.py                 # Regression prevention
│
├── integration/                       # Integration tests
│   └── test_end_to_end_processing.py  # Complete workflow tests
│
├── performance/                       # Performance benchmarks
│   └── test_benchmarks.py            # Speed and memory benchmarks
│
├── test_samples/                      # Sample documents and data
│   ├── README.md                      # Sample documentation
│   ├── sample_catalog.json           # Test document catalog
│   └── [sample PDFs and ground truth]
│
└── test_results/                      # Test execution results
    ├── latest_summary.json           # Latest test summary
    └── test_results_[timestamp].json # Detailed results
```

## 🧪 Running Tests

### Command Line Options

```bash
# Basic usage
python tests/run_all_tests.py

# Filter by category
python tests/run_all_tests.py --categories unit
python tests/run_all_tests.py --categories integration regression
python tests/run_all_tests.py --categories performance

# Quick testing (excludes slow tests)
python tests/run_all_tests.py --quick

# Required tests only
python tests/run_all_tests.py --required
```

### Individual Test Execution

```bash
# Using pytest directly
cd tests/
pytest test_basic_functionality.py -v
pytest test_text_extraction.py::TestPyMuPDFExtractor -v
pytest integration/ -v
pytest performance/ -m performance -v

# With coverage reporting
pytest --cov=pdf_processing --cov-report=html

# With detailed output
pytest -v --tb=long

# Parallel execution (if pytest-xdist installed)
pytest -n auto
```

### Test Markers

Tests use pytest markers for organization:

```python
@pytest.mark.performance  # Performance benchmarks
@pytest.mark.integration  # Integration tests
@pytest.mark.slow         # Slow-running tests
@pytest.mark.skip         # Skip in certain conditions
```

## 📊 Test Data

### Sample Documents

The `test_samples/` directory contains:

- **Academic PDFs**: IEEE, ACM, Springer format samples
- **Ground Truth**: Expected extraction results
- **Synthetic Documents**: Generated test cases for specific scenarios
- **Catalog**: `sample_catalog.json` with metadata for each test document

### Adding Test Samples

1. Ensure sample is open-access or legally usable
2. Add PDF to `test_samples/`
3. Create corresponding ground truth JSON
4. Update `sample_catalog.json` with metadata
5. Add test cases referencing the new sample

### Sample Categories

- **Computer Science**: IEEE and ACM format papers
- **Natural Sciences**: Springer and Nature format papers  
- **Humanities**: Philosophy and social science papers with extensive footnotes
- **Synthetic**: Generated documents for edge cases

## 📈 Performance Benchmarks

### Benchmark Categories

1. **Processing Speed**: Document processing time by size
2. **Memory Usage**: Memory consumption and leak detection
3. **Throughput**: Words/pages processed per second
4. **Scalability**: Performance with concurrent processing
5. **NLP Performance**: Text analysis pipeline speed

### Performance Targets

| Metric | Target | Measurement |
|--------|---------|-------------|
| Small docs | < 2 seconds | Processing time |
| Medium docs | < 5 seconds | Processing time |  
| Large docs | < 15 seconds | Processing time |
| Memory usage | < 200MB peak | Per document |
| Throughput | > 100 words/sec | Text processing |
| Concurrency | > 1.5x speedup | 4-thread vs 1-thread |

### Running Benchmarks

```bash
# All performance tests
python tests/run_all_tests.py --categories performance

# Specific benchmarks
pytest tests/performance/test_benchmarks.py::TestProcessingSpeedBenchmarks -v
pytest tests/performance/test_benchmarks.py::TestMemoryBenchmarks -v

# With performance markers
pytest -m performance -v
```

## 🔍 Quality Assurance

### Regression Testing

The regression test suite prevents quality degradation by:

1. **Baseline Creation**: First run creates baseline metrics
2. **Comparison**: Subsequent runs compare against baselines
3. **Tolerance Thresholds**: Acceptable degradation limits
4. **Reporting**: Detailed regression analysis

```bash
# Run regression tests
python tests/run_all_tests.py --categories regression

# View regression baselines
ls tests/baselines/
```

### Quality Metrics

- **Text Accuracy**: ≥ 95% character/word accuracy
- **Structure Accuracy**: ≥ 90% section detection accuracy  
- **Metadata Completeness**: ≥ 85% field extraction
- **Processing Consistency**: < 5% variance between runs

### Test Coverage

```bash
# Generate coverage report
pytest --cov=pdf_processing --cov=text_chunking --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html  # On macOS
# or browse to htmlcov/index.html
```

## 🔄 Continuous Integration

### GitHub Actions Integration

```yaml
# Example CI configuration
name: Academic MCP Server Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9]
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r python/requirements.txt
        python -m spacy download en_core_web_sm
        pip install pytest pytest-cov
    
    - name: Run test suite
      run: |
        cd python/
        python tests/run_all_tests.py --required
    
    - name: Upload test results
      uses: actions/upload-artifact@v2
      if: always()
      with:
        name: test-results
        path: python/tests/test_results/
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Set up pre-commit hooks
pre-commit install

# Run manual check
pre-commit run --all-files
```

## 🐛 Debugging Test Failures

### Common Issues

1. **Missing Dependencies**: Install all requirements including spaCy models
2. **Python Version**: Ensure Python 3.9.18 is being used
3. **Path Issues**: Run tests from correct directory
4. **Mock Failures**: Check mock setup in failing tests

### Debug Commands

```bash
# Verbose output with full tracebacks
pytest tests/test_failing.py -v --tb=long

# Drop into debugger on failure
pytest tests/test_failing.py --pdb

# Show stdout/print statements
pytest tests/test_failing.py -s

# Run specific test method
pytest tests/test_file.py::TestClass::test_method -v
```

### Log Analysis

```bash
# View latest test results
cat tests/test_results/latest_summary.json | python -m json.tool

# Check detailed results
cat tests/test_results/latest_detailed_results.json | python -m json.tool
```

## 📝 Contributing

### Adding New Tests

1. Follow existing test patterns and naming conventions
2. Include comprehensive docstrings and comments
3. Use appropriate test categories and markers
4. Mock external dependencies properly
5. Update this documentation for new test categories

### Test Development Guidelines

- **Arrange-Act-Assert**: Use clear test structure
- **Single Responsibility**: One concept per test method
- **Descriptive Names**: Clear test method and variable names
- **Mock External Dependencies**: Don't rely on external services
- **Performance Awareness**: Mark slow tests appropriately

### Code Coverage Requirements

- Minimum 80% code coverage for new functionality
- 100% coverage for critical paths (metadata extraction, citation processing)
- Include both positive and negative test cases
- Test error handling and edge cases

## 🔗 Related Documentation

- [Project README](../../README.md): Main project documentation
- [PDF Processing](../pdf_processing/README.md): PDF processing engine details  
- [Text Chunking](../text_chunking/README.md): NLP pipeline documentation
- [Development Guide](../../DEVELOPMENT.md): Development setup and guidelines

---

**Need Help?** Check the test output, review the logs in `test_results/`, or run individual tests with verbose output for detailed debugging information.