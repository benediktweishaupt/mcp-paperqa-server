# Test Sample PDFs for Academic MCP Server

This directory contains diverse academic PDF samples for comprehensive testing of the PDF processing engine.

## Sample Categories

### Open Access Academic Papers

#### Computer Science - IEEE Format
- `ieee_sample_1.md` - Two-column format with complex equations and figures
- `ieee_sample_2.md` - Single-author paper with extensive references
- Source: arXiv open-access papers, IEEE Xplore open access

#### Computer Science - ACM Format  
- `acm_sample_1.md` - ACM Computing Surveys format
- `acm_sample_2.md` - Conference paper with multiple authors
- Source: ACM Digital Library open access

#### Natural Sciences - Springer Format
- `springer_sample_1.md` - Life sciences paper with complex tables
- `springer_sample_2.md` - Physics paper with mathematical notation
- Source: SpringerOpen, PLoS ONE

#### Social Sciences & Humanities
- `humanities_sample_1.md` - Philosophy paper with extensive footnotes
- `humanities_sample_2.md` - Sociology paper with qualitative data
- Source: DOAJ (Directory of Open Access Journals)

#### Mixed Format Samples
- `mixed_layout_1.md` - Abstract + two-column body
- `mixed_layout_2.md` - Variable column widths
- `complex_formatting.md` - Multiple fonts, embedded figures

## Sample Metadata

Each PDF sample includes:
- Publisher type and format
- Expected structural elements (sections, subsections, etc.)
- Citation count and formats used
- Special formatting challenges (footnotes, tables, equations)
- Ground truth annotations for validation

## Usage in Tests

These samples are used for:
1. **Unit Testing** - Individual component validation
2. **Integration Testing** - End-to-end PDF processing
3. **Regression Testing** - Ensure quality maintenance
4. **Performance Benchmarking** - Speed and memory usage
5. **Publisher-Specific Testing** - Format handler validation

## Adding New Samples

When adding new test samples:
1. Ensure they are open-access or legally usable for testing
2. Create corresponding `.json` ground truth files
3. Update the sample metadata in `sample_catalog.json`
4. Add appropriate test cases in the test suite

## Legal Notice

All PDF samples used for testing are either:
- Open access publications with permissive licenses
- Generated synthetic academic documents for testing
- Used under fair use for software testing purposes

No copyrighted material is included without proper authorization.