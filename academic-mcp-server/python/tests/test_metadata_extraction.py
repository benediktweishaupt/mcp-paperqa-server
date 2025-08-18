"""
Comprehensive unit tests for metadata extraction components
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any

# Import modules for testing
try:
    from pdf_processing.models import Metadata
    from pdf_processing.extractors.base_extractor import BaseExtractor
    from pdf_processing.config import PublisherProfile, PublisherType
    METADATA_MODULES_AVAILABLE = True
except ImportError:
    METADATA_MODULES_AVAILABLE = False


class TestMetadataModel:
    """Test the Metadata model class"""
    
    def test_metadata_basic_creation(self):
        """Test basic metadata creation and attributes"""
        if not METADATA_MODULES_AVAILABLE:
            pytest.skip("Metadata modules not available")
        
        metadata = Metadata(
            title="Test Paper Title",
            authors=["John Smith", "Jane Doe"],
            abstract="This is a test abstract for the paper."
        )
        
        assert metadata.title == "Test Paper Title"
        assert len(metadata.authors) == 2
        assert metadata.authors[0] == "John Smith"
        assert metadata.abstract == "This is a test abstract for the paper."
    
    def test_metadata_complete_creation(self):
        """Test metadata creation with all fields"""
        if not METADATA_MODULES_AVAILABLE:
            pytest.skip("Metadata modules not available")
        
        metadata = Metadata(
            title="Advanced Machine Learning Techniques",
            authors=["Alice Johnson", "Bob Wilson", "Carol Davis"],
            affiliations=["MIT", "Stanford", "Berkeley"],
            abstract="This paper presents novel machine learning approaches...",
            keywords=["machine learning", "neural networks", "deep learning"],
            doi="10.1109/TEST.2023.123456",
            isbn="978-1-234-56789-0",
            publication_year=2023,
            journal="IEEE Transactions on Neural Networks",
            volume="34",
            issue="2",
            pages="145-162",
            publisher="IEEE",
            conference="International Conference on Machine Learning",
            submission_date="2023-01-15",
            acceptance_date="2023-03-20",
            publication_date="2023-06-01"
        )
        
        # Test all fields
        assert metadata.title == "Advanced Machine Learning Techniques"
        assert len(metadata.authors) == 3
        assert len(metadata.affiliations) == 3
        assert len(metadata.keywords) == 3
        assert metadata.doi == "10.1109/TEST.2023.123456"
        assert metadata.publication_year == 2023
        assert metadata.journal == "IEEE Transactions on Neural Networks"
        assert metadata.publisher == "IEEE"
    
    def test_metadata_validation(self):
        """Test metadata validation methods"""
        if not METADATA_MODULES_AVAILABLE:
            pytest.skip("Metadata modules not available")
        
        # Valid metadata
        valid_metadata = Metadata(
            title="Valid Title",
            authors=["Author Name"],
            doi="10.1109/valid.2023.123"
        )
        
        assert valid_metadata.is_valid()
        assert valid_metadata.validate_doi()
        
        # Invalid DOI
        invalid_doi_metadata = Metadata(
            title="Invalid DOI Test",
            authors=["Author"],
            doi="invalid-doi-format"
        )
        
        assert not invalid_doi_metadata.validate_doi()
        
        # Missing essential fields
        incomplete_metadata = Metadata()
        assert not incomplete_metadata.is_valid()
    
    def test_metadata_export_import(self):
        """Test metadata serialization and deserialization"""
        if not METADATA_MODULES_AVAILABLE:
            pytest.skip("Metadata modules not available")
        
        original_metadata = Metadata(
            title="Export Test Paper",
            authors=["Test Author"],
            publication_year=2023,
            keywords=["test", "export", "import"]
        )
        
        # Export to dictionary
        metadata_dict = original_metadata.to_dict()
        
        assert isinstance(metadata_dict, dict)
        assert metadata_dict['title'] == "Export Test Paper"
        assert metadata_dict['publication_year'] == 2023
        assert len(metadata_dict['keywords']) == 3
        
        # Import from dictionary
        imported_metadata = Metadata.from_dict(metadata_dict)
        
        assert imported_metadata.title == original_metadata.title
        assert imported_metadata.authors == original_metadata.authors
        assert imported_metadata.publication_year == original_metadata.publication_year
        assert imported_metadata.keywords == original_metadata.keywords


class TestMetadataExtraction:
    """Test metadata extraction from different sources"""
    
    def create_mock_pdf_metadata(self):
        """Create mock PDF metadata dictionary"""
        return {
            'title': 'Machine Learning Applications in Natural Language Processing',
            'author': 'John Smith; Jane Doe; Robert Johnson',
            'subject': 'Machine learning, NLP, deep learning',
            'creator': 'LaTeX via pdfTeX',
            'producer': 'pdfTeX-1.40.21',
            'creationDate': "D:20230615120000+00'00'",
            'modDate': "D:20230615120000+00'00'"
        }
    
    def create_mock_first_page_text(self):
        """Create mock first page text for heuristic extraction"""
        return """
        Advanced Machine Learning Techniques for Natural Language Processing
        
        John Smith¹, Jane Doe², Robert Johnson¹
        ¹Massachusetts Institute of Technology, Cambridge, MA, USA
        ²Stanford University, Stanford, CA, USA
        
        Abstract
        This paper presents novel machine learning approaches for natural language 
        processing tasks. We introduce new architectures that achieve state-of-the-art 
        performance on benchmark datasets. Our methods demonstrate significant improvements 
        in both accuracy and computational efficiency.
        
        Keywords: machine learning, natural language processing, deep learning, neural networks
        
        1. Introduction
        Natural language processing has become increasingly important...
        """
    
    def test_pdf_metadata_extraction(self):
        """Test extraction of metadata from PDF info dictionary"""
        if not METADATA_MODULES_AVAILABLE:
            pytest.skip("Metadata modules not available")
        
        # Mock extractor with PDF metadata extraction
        class MockPDFMetadataExtractor(BaseExtractor):
            def extract_metadata(self, file_path, config=None):
                pdf_meta = self.create_mock_pdf_metadata()
                
                # Convert PDF metadata to Metadata object
                return Metadata(
                    title=pdf_meta.get('title', ''),
                    authors=self._parse_authors(pdf_meta.get('author', '')),
                    keywords=self._parse_keywords(pdf_meta.get('subject', '')),
                    creator=pdf_meta.get('creator', ''),
                    creation_date=self._parse_pdf_date(pdf_meta.get('creationDate', ''))
                )
            
            def _parse_authors(self, author_string):
                if not author_string:
                    return []
                return [author.strip() for author in author_string.split(';')]
            
            def _parse_keywords(self, subject_string):
                if not subject_string:
                    return []
                return [kw.strip() for kw in subject_string.split(',')]
            
            def _parse_pdf_date(self, pdf_date):
                # Parse PDF date format D:YYYYMMDDHHmmSSOHH'mm'
                if pdf_date and pdf_date.startswith('D:'):
                    date_part = pdf_date[2:10]  # YYYYMMDD
                    try:
                        return datetime.strptime(date_part, '%Y%m%d').date().isoformat()
                    except ValueError:
                        return None
                return None
            
            def create_mock_pdf_metadata(self):
                return {
                    'title': 'Machine Learning Applications in Natural Language Processing',
                    'author': 'John Smith; Jane Doe; Robert Johnson',
                    'subject': 'Machine learning, NLP, deep learning',
                    'creator': 'LaTeX via pdfTeX',
                    'creationDate': "D:20230615120000+00'00'"
                }
        
        extractor = MockPDFMetadataExtractor()
        metadata = extractor.extract_metadata("/mock/path.pdf")
        
        assert metadata.title == 'Machine Learning Applications in Natural Language Processing'
        assert len(metadata.authors) == 3
        assert metadata.authors[0] == 'John Smith'
        assert len(metadata.keywords) == 3
        assert 'machine learning' in metadata.keywords
    
    def test_heuristic_metadata_extraction(self):
        """Test heuristic metadata extraction from document text"""
        if not METADATA_MODULES_AVAILABLE:
            pytest.skip("Metadata modules not available")
        
        class HeuristicMetadataExtractor:
            def extract_metadata_from_text(self, text):
                """Extract metadata using text analysis heuristics"""
                metadata = Metadata()
                
                # Extract title (usually the first line or largest text)
                lines = text.strip().split('\\n')
                title_candidates = [line.strip() for line in lines[:5] if line.strip()]
                if title_candidates:
                    # Assume first substantial line is title
                    metadata.title = title_candidates[0]
                
                # Extract authors (look for patterns)
                author_pattern = r'([A-Z][a-z]+ [A-Z][a-z]+(?:[¹²³⁴⁵]|\\d*)?(?:,\\s*[A-Z][a-z]+ [A-Z][a-z]+(?:[¹²³⁴⁵]|\\d*)?)*)'
                author_matches = re.findall(author_pattern, text)
                if author_matches:
                    authors_text = author_matches[0]
                    metadata.authors = [author.strip() for author in re.split(r',|;', authors_text) if author.strip()]
                
                # Extract affiliations (lines with university/institution names)
                affiliation_pattern = r'([^\\n]*(?:University|Institute|College|Laboratory)[^\\n]*)'
                affiliation_matches = re.findall(affiliation_pattern, text, re.IGNORECASE)
                if affiliation_matches:
                    metadata.affiliations = [aff.strip() for aff in affiliation_matches[:3]]
                
                # Extract abstract (text after "Abstract" keyword)
                abstract_pattern = r'Abstract\\s*\\n([^\\n]+(?:\\n[^\\n]+)*?)(?=\\n\\s*(?:Keywords|1\\.\\s*Introduction|\\Z))'
                abstract_match = re.search(abstract_pattern, text, re.IGNORECASE | re.DOTALL)
                if abstract_match:
                    metadata.abstract = ' '.join(abstract_match.group(1).split())
                
                # Extract keywords (text after "Keywords:" or "Index Terms:")
                keywords_pattern = r'(?:Keywords|Index Terms):?\\s*([^\\n]+)'
                keywords_match = re.search(keywords_pattern, text, re.IGNORECASE)
                if keywords_match:
                    keywords_text = keywords_match.group(1)
                    metadata.keywords = [kw.strip() for kw in re.split(r',|;', keywords_text) if kw.strip()]
                
                return metadata
        
        extractor = HeuristicMetadataExtractor()
        text = self.create_mock_first_page_text()
        metadata = extractor.extract_metadata_from_text(text)
        
        assert "Advanced Machine Learning Techniques" in metadata.title
        assert len(metadata.authors) >= 2
        assert "John Smith" in metadata.authors
        assert metadata.abstract is not None and len(metadata.abstract) > 50
        assert len(metadata.keywords) >= 3
    
    def test_doi_extraction_and_validation(self):
        """Test DOI extraction and validation"""
        if not METADATA_MODULES_AVAILABLE:
            pytest.skip("Metadata modules not available")
        
        class DOIExtractor:
            def extract_doi_from_text(self, text):
                """Extract DOI from document text"""
                # Common DOI patterns
                doi_patterns = [
                    r'doi:?\\s*(10\\.\\d+/[^\\s]+)',
                    r'DOI:?\\s*(10\\.\\d+/[^\\s]+)',
                    r'https?://(?:dx\\.)?doi\\.org/(10\\.\\d+/[^\\s]+)',
                    r'\\bdoi\\s*=\\s*["\']?(10\\.\\d+/[^\\s"\']+)'
                ]
                
                for pattern in doi_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        return match.group(1)
                
                return None
            
            def validate_doi_format(self, doi):
                """Validate DOI format"""
                if not doi:
                    return False
                
                # Basic DOI format: 10.xxxx/yyyyyyy
                doi_pattern = r'^10\\.\\d{4,}/[\\w\\-\\._:;\\[\\]/]+$'
                return bool(re.match(doi_pattern, doi))
        
        extractor = DOIExtractor()
        
        # Test DOI extraction from different formats
        test_texts = [
            "DOI: 10.1109/TNNLS.2023.123456",
            "doi:10.1145/3384523.3384567", 
            "Available at https://doi.org/10.1007/s12345-023-01234-5",
            "doi = \"10.1038/nature12345\""
        ]
        
        expected_dois = [
            "10.1109/TNNLS.2023.123456",
            "10.1145/3384523.3384567",
            "10.1007/s12345-023-01234-5",
            "10.1038/nature12345"
        ]
        
        for text, expected_doi in zip(test_texts, expected_dois):
            extracted_doi = extractor.extract_doi_from_text(text)
            assert extracted_doi == expected_doi
            assert extractor.validate_doi_format(extracted_doi)
    
    def test_publisher_specific_metadata(self):
        """Test publisher-specific metadata extraction"""
        if not METADATA_MODULES_AVAILABLE:
            pytest.skip("Metadata modules not available")
        
        class PublisherMetadataExtractor:
            def extract_ieee_metadata(self, text):
                """Extract IEEE-specific metadata patterns"""
                metadata = Metadata()
                
                # IEEE transaction pattern
                ieee_pattern = r'IEEE\\s+(?:Transactions|Journal)\\s+on\\s+([^,\\n]+)'
                ieee_match = re.search(ieee_pattern, text, re.IGNORECASE)
                if ieee_match:
                    metadata.journal = f"IEEE Transactions on {ieee_match.group(1).strip()}"
                    metadata.publisher = "IEEE"
                
                # IEEE DOI pattern
                ieee_doi_pattern = r'10\\.1109/[^\\s]+'
                ieee_doi_match = re.search(ieee_doi_pattern, text)
                if ieee_doi_match:
                    metadata.doi = ieee_doi_match.group(0)
                
                return metadata
            
            def extract_acm_metadata(self, text):
                """Extract ACM-specific metadata patterns"""
                metadata = Metadata()
                
                # ACM publication pattern
                acm_pattern = r'ACM\\s+([^,\\n]+)'
                acm_match = re.search(acm_pattern, text, re.IGNORECASE)
                if acm_match:
                    metadata.journal = acm_match.group(0).strip()
                    metadata.publisher = "ACM"
                
                # ACM DOI pattern
                acm_doi_pattern = r'10\\.1145/[^\\s]+'
                acm_doi_match = re.search(acm_doi_pattern, text)
                if acm_doi_match:
                    metadata.doi = acm_doi_match.group(0)
                
                return metadata
            
            def extract_springer_metadata(self, text):
                """Extract Springer-specific metadata patterns"""
                metadata = Metadata()
                
                # Springer DOI pattern
                springer_doi_pattern = r'10\\.1007/[^\\s]+'
                springer_doi_match = re.search(springer_doi_pattern, text)
                if springer_doi_match:
                    metadata.doi = springer_doi_match.group(0)
                    metadata.publisher = "Springer"
                
                return metadata
        
        extractor = PublisherMetadataExtractor()
        
        # Test IEEE extraction
        ieee_text = "IEEE Transactions on Neural Networks and Learning Systems, vol. 34, no. 2, pp. 145-162, 2023. DOI: 10.1109/TNNLS.2023.123456"
        ieee_metadata = extractor.extract_ieee_metadata(ieee_text)
        
        assert "IEEE Transactions on Neural Networks" in ieee_metadata.journal
        assert ieee_metadata.publisher == "IEEE"
        assert ieee_metadata.doi == "10.1109/TNNLS.2023.123456"
        
        # Test ACM extraction
        acm_text = "ACM Computing Surveys, Vol. 55, No. 3, Article 67, Publication date: March 2023. DOI: 10.1145/3384523.3384567"
        acm_metadata = extractor.extract_acm_metadata(acm_text)
        
        assert acm_metadata.publisher == "ACM"
        assert acm_metadata.doi == "10.1145/3384523.3384567"
        
        # Test Springer extraction  
        springer_text = "Journal of Machine Learning Research, Springer Nature, 2023. DOI: 10.1007/s12345-023-01234-5"
        springer_metadata = extractor.extract_springer_metadata(springer_text)
        
        assert springer_metadata.publisher == "Springer"
        assert springer_metadata.doi == "10.1007/s12345-023-01234-5"


class TestMetadataQuality:
    """Test metadata quality assessment and validation"""
    
    def test_metadata_completeness_scoring(self):
        """Test scoring of metadata completeness"""
        if not METADATA_MODULES_AVAILABLE:
            pytest.skip("Metadata modules not available")
        
        class MetadataQualityAssessor:
            def calculate_completeness_score(self, metadata):
                """Calculate completeness score (0-100)"""
                essential_fields = ['title', 'authors']
                important_fields = ['abstract', 'keywords', 'doi', 'publication_year']
                optional_fields = ['journal', 'publisher', 'affiliations']
                
                score = 0
                total_points = 100
                
                # Essential fields (50 points total)
                for field in essential_fields:
                    if getattr(metadata, field, None):
                        score += 25
                
                # Important fields (40 points total)
                for field in important_fields:
                    if getattr(metadata, field, None):
                        score += 10
                
                # Optional fields (10 points total)
                filled_optional = sum(1 for field in optional_fields 
                                    if getattr(metadata, field, None))
                score += min(10, filled_optional * 2)
                
                return min(score, total_points)
        
        assessor = MetadataQualityAssessor()
        
        # Test complete metadata
        complete_metadata = Metadata(
            title="Complete Paper",
            authors=["Author One", "Author Two"],
            abstract="Complete abstract here.",
            keywords=["keyword1", "keyword2"],
            doi="10.1109/test.2023.123",
            publication_year=2023,
            journal="Test Journal",
            publisher="Test Publisher"
        )
        
        complete_score = assessor.calculate_completeness_score(complete_metadata)
        assert complete_score >= 90
        
        # Test minimal metadata
        minimal_metadata = Metadata(
            title="Minimal Paper",
            authors=["Single Author"]
        )
        
        minimal_score = assessor.calculate_completeness_score(minimal_metadata)
        assert minimal_score == 50  # Only essential fields
        
        # Test empty metadata
        empty_metadata = Metadata()
        empty_score = assessor.calculate_completeness_score(empty_metadata)
        assert empty_score == 0
    
    def test_metadata_consistency_validation(self):
        """Test validation of metadata consistency"""
        if not METADATA_MODULES_AVAILABLE:
            pytest.skip("Metadata modules not available")
        
        class MetadataValidator:
            def validate_consistency(self, metadata):
                """Validate metadata for consistency issues"""
                issues = []
                
                # Check title length
                if metadata.title and len(metadata.title) > 200:
                    issues.append("Title too long (>200 characters)")
                
                # Check author format
                if metadata.authors:
                    for author in metadata.authors:
                        if not re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+', author):
                            issues.append(f"Author name format questionable: {author}")
                
                # Check publication year reasonableness
                if metadata.publication_year:
                    current_year = datetime.now().year
                    if metadata.publication_year > current_year + 1:
                        issues.append("Publication year in the future")
                    if metadata.publication_year < 1900:
                        issues.append("Publication year too old")
                
                # Check DOI format if present
                if metadata.doi and not re.match(r'^10\\.\\d+/', metadata.doi):
                    issues.append("Invalid DOI format")
                
                # Check keywords reasonableness
                if metadata.keywords and len(metadata.keywords) > 20:
                    issues.append("Too many keywords (>20)")
                
                return issues
        
        validator = MetadataValidator()
        
        # Test valid metadata
        valid_metadata = Metadata(
            title="A Reasonable Paper Title",
            authors=["John Smith", "Jane Doe"],
            publication_year=2023,
            doi="10.1109/test.2023.123",
            keywords=["ml", "ai", "research"]
        )
        
        valid_issues = validator.validate_consistency(valid_metadata)
        assert len(valid_issues) == 0
        
        # Test problematic metadata
        problematic_metadata = Metadata(
            title="A" * 250,  # Too long
            authors=["john smith"],  # Wrong format
            publication_year=2025,  # Future
            doi="invalid-doi",  # Invalid format
            keywords=["kw" + str(i) for i in range(25)]  # Too many
        )
        
        problem_issues = validator.validate_consistency(problematic_metadata)
        assert len(problem_issues) >= 4
    
    def test_metadata_confidence_scoring(self):
        """Test confidence scoring for extracted metadata"""
        if not METADATA_MODULES_AVAILABLE:
            pytest.skip("Metadata modules not available")
        
        class MetadataConfidenceScorer:
            def calculate_extraction_confidence(self, metadata, extraction_method, text_source=None):
                """Calculate confidence score for extracted metadata"""
                confidence_scores = {}
                
                # Title confidence
                if metadata.title:
                    if extraction_method == 'pdf_metadata':
                        confidence_scores['title'] = 0.95
                    elif extraction_method == 'heuristic':
                        # Check if title looks reasonable
                        if 5 <= len(metadata.title) <= 150:
                            confidence_scores['title'] = 0.85
                        else:
                            confidence_scores['title'] = 0.60
                
                # Authors confidence
                if metadata.authors:
                    if extraction_method == 'pdf_metadata':
                        confidence_scores['authors'] = 0.90
                    elif extraction_method == 'heuristic':
                        # Check author name patterns
                        valid_names = sum(1 for author in metadata.authors 
                                        if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+', author))
                        confidence_scores['authors'] = valid_names / len(metadata.authors) * 0.80
                
                # DOI confidence
                if metadata.doi:
                    if re.match(r'^10\\.\\d+/', metadata.doi):
                        confidence_scores['doi'] = 0.98  # DOIs are very reliable
                    else:
                        confidence_scores['doi'] = 0.30
                
                # Overall confidence
                if confidence_scores:
                    overall_confidence = sum(confidence_scores.values()) / len(confidence_scores)
                    return overall_confidence, confidence_scores
                else:
                    return 0.0, {}
        
        scorer = MetadataConfidenceScorer()
        
        # Test high confidence metadata (from PDF metadata)
        high_conf_metadata = Metadata(
            title="Well Extracted Title",
            authors=["John Smith", "Jane Doe"],
            doi="10.1109/test.2023.123"
        )
        
        overall_conf, field_conf = scorer.calculate_extraction_confidence(
            high_conf_metadata, 'pdf_metadata'
        )
        
        assert overall_conf > 0.90
        assert field_conf['title'] >= 0.95
        assert field_conf['doi'] >= 0.95
        
        # Test medium confidence metadata (heuristic extraction)
        medium_conf_metadata = Metadata(
            title="Reasonably Good Title",
            authors=["Valid Name"],
            doi="questionable-doi"
        )
        
        med_overall_conf, med_field_conf = scorer.calculate_extraction_confidence(
            medium_conf_metadata, 'heuristic'
        )
        
        assert 0.50 <= med_overall_conf <= 0.85
        assert med_field_conf['doi'] < 0.50  # Low confidence for bad DOI


if __name__ == "__main__":
    if METADATA_MODULES_AVAILABLE:
        print("🔄 Running metadata extraction tests...")
        
        # Basic model tests
        try:
            test_model = TestMetadataModel()
            test_model.test_metadata_basic_creation()
            test_model.test_metadata_complete_creation()
            test_model.test_metadata_validation()
            print("✅ Metadata model tests passed")
        except Exception as e:
            print(f"❌ Metadata model tests failed: {e}")
        
        # Extraction tests
        try:
            test_extraction = TestMetadataExtraction()
            test_extraction.test_heuristic_metadata_extraction()
            test_extraction.test_doi_extraction_and_validation()
            print("✅ Metadata extraction tests passed")
        except Exception as e:
            print(f"❌ Metadata extraction tests failed: {e}")
        
        # Quality tests
        try:
            test_quality = TestMetadataQuality()
            test_quality.test_metadata_completeness_scoring()
            test_quality.test_metadata_consistency_validation()
            print("✅ Metadata quality tests passed")
        except Exception as e:
            print(f"❌ Metadata quality tests failed: {e}")
        
        print("\n🎉 Metadata extraction testing complete!")
        print("📝 Note: Full integration requires PDF processing libraries")
        
    else:
        print("⚠️  Metadata modules not available")
        print("📦 Install requirements and ensure module structure is complete")