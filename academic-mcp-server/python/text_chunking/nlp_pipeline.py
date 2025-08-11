"""
Academic NLP Pipeline using spaCy with custom components for academic text processing
"""

try:
    import spacy
    from spacy.language import Language
    from spacy.tokens import Doc, Token, Span
    from spacy.matcher import Matcher, PhraseMatcher
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    
import re
from typing import List, Dict, Optional, Tuple, Set
import re
import logging
from pathlib import Path


class AcademicNLPPipeline:
    """
    spaCy-based NLP pipeline optimized for academic text processing
    
    Features:
    - Citation detection and extraction
    - Academic entity recognition (authors, institutions, concepts)
    - Formal structure recognition (theorems, definitions, proofs)
    - Specialized tokenization for academic conventions
    """
    
    def __init__(self, model_name: str = "en_core_web_sm", enable_transformer: bool = False):
        """
        Initialize the academic NLP pipeline
        
        Args:
            model_name: spaCy model to use ('en_core_web_sm' or 'en_core_web_trf')
            enable_transformer: Whether to use transformer model for better accuracy
        """
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name
        self.enable_transformer = enable_transformer
        
        # Initialize spaCy pipeline
        self.nlp = self._load_spacy_model()
        
        # Add custom components
        self._add_custom_components()
        
        # Initialize matchers
        self.citation_matcher = Matcher(self.nlp.vocab)
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab)
        
        # Load academic patterns
        self._load_academic_patterns()
        
        self.logger.info(f"Academic NLP pipeline initialized with model: {model_name}")
    
    def _load_spacy_model(self) -> Language:
        """Load and configure spaCy model"""
        try:
            if self.enable_transformer:
                # Try to load transformer model first
                try:
                    nlp = spacy.load("en_core_web_trf")
                    self.model_name = "en_core_web_trf"
                    self.logger.info("Loaded transformer model en_core_web_trf")
                except OSError:
                    self.logger.warning("Transformer model not available, falling back to standard model")
                    nlp = spacy.load(self.model_name)
            else:
                nlp = spacy.load(self.model_name)
                
        except OSError as e:
            self.logger.error(f"Failed to load spaCy model {self.model_name}: {e}")
            # Fallback to basic English model
            try:
                nlp = spacy.load("en_core_web_sm")
                self.model_name = "en_core_web_sm"
                self.logger.warning("Falling back to en_core_web_sm")
            except OSError:
                raise RuntimeError("No spaCy English model found. Install with: python -m spacy download en_core_web_sm")
        
        return nlp
    
    def _add_custom_components(self):
        """Add custom pipeline components for academic text processing"""
        
        # Register components with spaCy
        if not Language.has_factory("citation_detector"):
            Language.factory("citation_detector")(self._create_citation_detector_factory)
        if not Language.has_factory("academic_structure"):
            Language.factory("academic_structure")(self._create_academic_structure_factory)
        if not Language.has_factory("argument_detector"):
            Language.factory("argument_detector")(self._create_argument_detector_factory)
        
        # Add components to pipeline
        if "citation_detector" not in self.nlp.pipe_names:
            self.nlp.add_pipe("citation_detector", after="ner")
        
        if "academic_structure" not in self.nlp.pipe_names:
            self.nlp.add_pipe("academic_structure", after="citation_detector")
        
        if "argument_detector" not in self.nlp.pipe_names:
            self.nlp.add_pipe("argument_detector", last=True)
    
    def _create_citation_detector_factory(self, nlp, name):
        """Factory for citation detector component"""
        return self._create_citation_detector()
    
    def _create_academic_structure_factory(self, nlp, name):
        """Factory for academic structure detector component"""
        return self._create_academic_structure_detector()
    
    def _create_argument_detector_factory(self, nlp, name):
        """Factory for argument detector component"""  
        return self._create_argument_detector()
    
    def _create_citation_detector(self):
        """Create citation detection component"""
        def citation_detector(doc: Doc) -> Doc:
            """Detect and annotate citations in academic text"""
            matches = self.citation_matcher(doc)
            
            # Convert matches to spans
            spans = []
            for match_id, start, end in matches:
                span = Span(doc, start, end, label="CITATION")
                spans.append(span)
            
            # Set custom extension for citations
            if not Token.has_extension("is_citation"):
                Token.set_extension("is_citation", default=False)
            if not Span.has_extension("citation_type"):
                Span.set_extension("citation_type", default=None)
            
            # Mark citation tokens and set citation types
            for span in spans:
                for token in span:
                    token._.is_citation = True
                span._.citation_type = self._classify_citation(span.text)
            
            # Add spans to doc entities (avoiding conflicts)
            filtered_ents = self._filter_overlapping_entities(list(doc.ents) + spans)
            doc.ents = filtered_ents
            
            return doc
        
        return citation_detector
    
    def _create_academic_structure_detector(self):
        """Create academic structure detection component"""
        def academic_structure(doc: Doc) -> Doc:
            """Detect academic structures like theorems, definitions, proofs"""
            
            if not Span.has_extension("structure_type"):
                Span.set_extension("structure_type", default=None)
            
            # Detect formal structures
            structure_patterns = [
                (r'(?i)\b(theorem|lemma|corollary|proposition)\s*\d*\.?\s*', 'THEOREM'),
                (r'(?i)\b(definition|def\.)\s*\d*\.?\s*', 'DEFINITION'),
                (r'(?i)\b(proof|pf\.)\s*\.?\s*', 'PROOF'),
                (r'(?i)\b(example|ex\.)\s*\d*\.?\s*', 'EXAMPLE'),
                (r'(?i)\b(remark|note)\s*\d*\.?\s*', 'REMARK'),
            ]
            
            spans = []
            for pattern, label in structure_patterns:
                for match in re.finditer(pattern, doc.text):
                    start_char, end_char = match.span()
                    span = doc.char_span(start_char, end_char, label=label)
                    if span:
                        span._.structure_type = label.lower()
                        spans.append(span)
            
            # Add to entities
            filtered_ents = self._filter_overlapping_entities(list(doc.ents) + spans)
            doc.ents = filtered_ents
            
            return doc
        
        return academic_structure
    
    def _create_argument_detector(self):
        """Create argument boundary detection component"""
        def argument_detector(doc: Doc) -> Doc:
            """Detect argument boundaries and discourse markers"""
            
            if not Token.has_extension("is_discourse_marker"):
                Token.set_extension("is_discourse_marker", default=False)
            if not Span.has_extension("argument_role"):
                Span.set_extension("argument_role", default=None)
            
            # Discourse markers for argument detection
            discourse_markers = {
                'claim': ['argue', 'claim', 'assert', 'propose', 'suggest', 'contend'],
                'evidence': ['evidence', 'data', 'shows', 'demonstrates', 'indicates', 'reveals'],
                'conclusion': ['therefore', 'thus', 'hence', 'consequently', 'in conclusion'],
                'contrast': ['however', 'but', 'nevertheless', 'on the contrary', 'conversely'],
                'support': ['furthermore', 'moreover', 'additionally', 'in addition']
            }
            
            # Mark discourse markers
            for sent in doc.sents:
                for token in sent:
                    for role, markers in discourse_markers.items():
                        if token.lemma_.lower() in markers:
                            token._.is_discourse_marker = True
                            # Mark sentence with argument role
                            sent_span = sent.as_doc().spans.get("sentence", sent)
                            if hasattr(sent_span, "_"):
                                sent_span._.argument_role = role
            
            return doc
        
        return argument_detector
    
    def _load_academic_patterns(self):
        """Load patterns for citation and academic term detection"""
        
        # Citation patterns (Author, Year) format
        citation_patterns = [
            # (Author, Year) format
            [{"TEXT": "("}, {"IS_ALPHA": True}, {"TEXT": ","}, {"IS_DIGIT": True}, {"TEXT": ")"}],
            # Author (Year) format  
            [{"IS_ALPHA": True}, {"TEXT": "("}, {"IS_DIGIT": True}, {"TEXT": ")"}],
            # [Number] format
            [{"TEXT": "["}, {"IS_DIGIT": True}, {"TEXT": "]"}],
            # et al. patterns
            [{"LOWER": "et"}, {"LOWER": "al"}, {"TEXT": "."}],
            # DOI patterns
            [{"LOWER": "doi"}, {"TEXT": ":"}, {"IS_ASCII": True}],
        ]
        
        for i, pattern in enumerate(citation_patterns):
            self.citation_matcher.add(f"CITATION_{i}", [pattern])
        
        # Academic phrase patterns
        academic_phrases = [
            "et al.", "i.e.", "e.g.", "cf.", "ibid.", "op. cit.",
            "et cetera", "inter alia", "supra", "infra"
        ]
        
        phrase_docs = [self.nlp.make_doc(phrase) for phrase in academic_phrases]
        self.phrase_matcher.add("ACADEMIC_PHRASE", phrase_docs)
    
    def _classify_citation(self, citation_text: str) -> str:
        """Classify citation type based on format"""
        citation_text = citation_text.strip()
        
        if re.match(r'\[\d+\]', citation_text):
            return "numbered"
        elif re.match(r'\([^)]*\d{4}[^)]*\)', citation_text):
            return "author_year"
        elif 'doi:' in citation_text.lower():
            return "doi"
        elif 'et al.' in citation_text.lower():
            return "multi_author"
        else:
            return "unknown"
    
    def _filter_overlapping_entities(self, entities: List[Span]) -> List[Span]:
        """Remove overlapping entities, keeping the longest ones"""
        if not entities:
            return entities
        
        # Sort by start position, then by length (longest first)
        sorted_entities = sorted(entities, key=lambda e: (e.start, -(e.end - e.start)))
        
        filtered = []
        for entity in sorted_entities:
            # Check if this entity overlaps with any already accepted entity
            overlaps = False
            for accepted in filtered:
                if (entity.start < accepted.end and entity.end > accepted.start):
                    overlaps = True
                    break
            
            if not overlaps:
                filtered.append(entity)
        
        return filtered
    
    def process_text(self, text: str) -> Doc:
        """
        Process text through the academic NLP pipeline
        
        Args:
            text: Input academic text
            
        Returns:
            spaCy Doc object with academic annotations
        """
        doc = self.nlp(text)
        return doc
    
    def extract_citations(self, doc: Doc) -> List[Dict]:
        """
        Extract citation information from processed document
        
        Args:
            doc: Processed spaCy Doc
            
        Returns:
            List of citation dictionaries
        """
        citations = []
        
        for ent in doc.ents:
            if ent.label_ == "CITATION":
                citation = {
                    'text': ent.text,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'type': ent._.citation_type if hasattr(ent._, 'citation_type') else 'unknown'
                }
                citations.append(citation)
        
        return citations
    
    def extract_academic_structures(self, doc: Doc) -> List[Dict]:
        """
        Extract academic structures (theorems, definitions, etc.)
        
        Args:
            doc: Processed spaCy Doc
            
        Returns:
            List of academic structure dictionaries
        """
        structures = []
        
        for ent in doc.ents:
            if ent.label_ in ['THEOREM', 'DEFINITION', 'PROOF', 'EXAMPLE', 'REMARK']:
                structure = {
                    'text': ent.text,
                    'type': ent.label_.lower(),
                    'start': ent.start_char,
                    'end': ent.end_char
                }
                structures.append(structure)
        
        return structures
    
    def get_discourse_markers(self, doc: Doc) -> List[Dict]:
        """
        Extract discourse markers that signal argument structure
        
        Args:
            doc: Processed spaCy Doc
            
        Returns:
            List of discourse marker dictionaries
        """
        markers = []
        
        for token in doc:
            if hasattr(token._, 'is_discourse_marker') and token._.is_discourse_marker:
                marker = {
                    'text': token.text,
                    'lemma': token.lemma_,
                    'position': token.i,
                    'sentence': token.sent.text
                }
                markers.append(marker)
        
        return markers
    
    def analyze_sentence_complexity(self, doc: Doc) -> List[Dict]:
        """
        Analyze syntactic complexity of sentences
        
        Args:
            doc: Processed spaCy Doc
            
        Returns:
            List of sentence complexity metrics
        """
        sentence_metrics = []
        
        for sent in doc.sents:
            # Calculate complexity metrics
            num_tokens = len(sent)
            num_clauses = len([token for token in sent if token.dep_ in ['ccomp', 'xcomp', 'advcl', 'acl', 'relcl']])
            avg_word_length = sum(len(token.text) for token in sent if token.is_alpha) / max(1, len([t for t in sent if t.is_alpha]))
            
            metrics = {
                'text': sent.text,
                'start': sent.start_char,
                'end': sent.end_char,
                'num_tokens': num_tokens,
                'num_clauses': num_clauses,
                'avg_word_length': avg_word_length,
                'complexity_score': (num_tokens * 0.3) + (num_clauses * 0.5) + (avg_word_length * 0.2)
            }
            sentence_metrics.append(metrics)
        
        return sentence_metrics
    
    def get_pipeline_info(self) -> Dict:
        """Get information about the loaded pipeline"""
        return {
            'model_name': self.model_name,
            'pipe_names': self.nlp.pipe_names,
            'components': len(self.nlp.pipeline),
            'vocab_size': len(self.nlp.vocab),
            'has_transformer': 'transformer' in str(type(self.nlp)).lower()
        }


# Utility functions for installation and model management
def download_required_models():
    """Download required spaCy models"""
    import subprocess
    import sys
    
    models = ["en_core_web_sm"]
    
    for model in models:
        try:
            spacy.load(model)
            print(f"✓ {model} already installed")
        except OSError:
            print(f"Downloading {model}...")
            subprocess.run([sys.executable, "-m", "spacy", "download", model], check=True)
            print(f"✓ {model} installed successfully")


def is_transformer_available() -> bool:
    """Check if transformer model is available"""
    try:
        spacy.load("en_core_web_trf")
        return True
    except OSError:
        return False


if __name__ == "__main__":
    # Test the pipeline
    pipeline = AcademicNLPPipeline(enable_transformer=False)
    
    test_text = """
    According to Smith et al. (2020), the theory of relativity has significant implications.
    However, Johnson (2021) argues that this interpretation is incomplete.
    
    Definition 1. A semantic space is a mathematical structure that represents meaning.
    
    Theorem 1. Every finite dimensional vector space has a basis.
    
    Proof. We proceed by induction on the dimension of the space.
    """
    
    doc = pipeline.process_text(test_text)
    
    print("Pipeline Info:", pipeline.get_pipeline_info())
    print("\nCitations:", pipeline.extract_citations(doc))
    print("\nAcademic Structures:", pipeline.extract_academic_structures(doc))
    print("\nDiscourse Markers:", pipeline.get_discourse_markers(doc))