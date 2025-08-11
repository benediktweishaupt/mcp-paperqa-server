"""
Configuration for intelligent text chunking system
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class ChunkingStrategy(Enum):
    """Available chunking strategies"""
    PARAGRAPH_BASED = "paragraph"
    SEMANTIC = "semantic" 
    SLIDING_WINDOW = "sliding_window"
    ARGUMENTATIVE = "argumentative"
    HYBRID = "hybrid"


class AcademicDiscipline(Enum):
    """Academic disciplines with different chunking requirements"""
    GENERAL = "general"
    HUMANITIES = "humanities"
    SOCIAL_SCIENCES = "social_sciences"
    PHILOSOPHY = "philosophy"
    LITERATURE = "literature"
    HISTORY = "history"
    LINGUISTICS = "linguistics"


@dataclass
class NLPPipelineConfig:
    """Configuration for academic NLP pipeline"""
    
    # Model selection
    model_name: str = "en_core_web_sm"
    enable_transformer: bool = False
    
    # Citation detection
    detect_citations: bool = True
    citation_patterns: List[str] = field(default_factory=lambda: [
        "author_year",  # (Author, Year)
        "numbered",     # [1]
        "footnote",     # ¹
        "doi"          # DOI references
    ])
    
    # Academic structure detection
    detect_structures: bool = True
    structure_types: List[str] = field(default_factory=lambda: [
        "theorem", "definition", "proof", "example", "remark", "corollary"
    ])
    
    # Argument detection
    detect_arguments: bool = True
    discourse_markers: bool = True
    
    # Entity recognition
    academic_entities: bool = True
    author_recognition: bool = True
    institution_recognition: bool = True
    concept_recognition: bool = True
    
    # Performance settings
    batch_size: int = 100
    max_length: int = 1000000  # Maximum text length to process
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            'model_name': self.model_name,
            'enable_transformer': self.enable_transformer,
            'detect_citations': self.detect_citations,
            'citation_patterns': self.citation_patterns,
            'detect_structures': self.detect_structures,
            'structure_types': self.structure_types,
            'detect_arguments': self.detect_arguments,
            'discourse_markers': self.discourse_markers,
            'academic_entities': self.academic_entities,
            'author_recognition': self.author_recognition,
            'institution_recognition': self.institution_recognition,
            'concept_recognition': self.concept_recognition,
            'batch_size': self.batch_size,
            'max_length': self.max_length,
        }


@dataclass 
class ChunkingConfig:
    """Configuration for text chunking"""
    
    # Strategy
    strategy: ChunkingStrategy = ChunkingStrategy.HYBRID
    discipline: AcademicDiscipline = AcademicDiscipline.GENERAL
    
    # Chunk size settings
    min_chunk_size: int = 100  # Minimum tokens per chunk
    max_chunk_size: int = 1000  # Maximum tokens per chunk
    target_chunk_size: int = 500  # Target tokens per chunk
    
    # Sliding window settings
    window_overlap: float = 0.2  # 20% overlap between chunks
    window_stride: Optional[int] = None  # Auto-calculated if None
    
    # Paragraph preservation
    preserve_paragraphs: bool = True
    min_paragraph_tokens: int = 50
    
    # Argument preservation
    preserve_arguments: bool = True
    argument_completion_threshold: float = 0.8  # Minimum completeness score
    
    # Semantic coherence
    coherence_threshold: float = 0.7  # Minimum coherence score
    use_sentence_embeddings: bool = True
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # Citation handling
    preserve_citations: bool = True
    citation_context_window: int = 2  # Sentences before/after citation
    
    # Cross-reference handling
    resolve_cross_references: bool = True
    cross_ref_context_window: int = 1
    
    # Quality control
    validate_chunks: bool = True
    min_coherence_score: float = 0.5
    max_complexity_score: float = 10.0
    
    # Performance
    parallel_processing: bool = False
    max_workers: int = 4
    
    def get_discipline_settings(self) -> Dict[str, Any]:
        """Get discipline-specific settings"""
        discipline_configs = {
            AcademicDiscipline.PHILOSOPHY: {
                'min_chunk_size': 150,
                'target_chunk_size': 600,
                'preserve_arguments': True,
                'argument_completion_threshold': 0.9,
                'coherence_threshold': 0.8
            },
            AcademicDiscipline.LITERATURE: {
                'min_chunk_size': 200,
                'target_chunk_size': 800, 
                'preserve_paragraphs': True,
                'window_overlap': 0.15
            },
            AcademicDiscipline.SOCIAL_SCIENCES: {
                'min_chunk_size': 100,
                'target_chunk_size': 500,
                'preserve_citations': True,
                'citation_context_window': 3
            },
            AcademicDiscipline.LINGUISTICS: {
                'min_chunk_size': 80,
                'target_chunk_size': 400,
                'preserve_arguments': True,
                'use_sentence_embeddings': True
            }
        }
        
        return discipline_configs.get(self.discipline, {})
    
    def apply_discipline_settings(self):
        """Apply discipline-specific settings to current config"""
        settings = self.get_discipline_settings()
        for key, value in settings.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            'strategy': self.strategy.value,
            'discipline': self.discipline.value,
            'min_chunk_size': self.min_chunk_size,
            'max_chunk_size': self.max_chunk_size,
            'target_chunk_size': self.target_chunk_size,
            'window_overlap': self.window_overlap,
            'window_stride': self.window_stride,
            'preserve_paragraphs': self.preserve_paragraphs,
            'min_paragraph_tokens': self.min_paragraph_tokens,
            'preserve_arguments': self.preserve_arguments,
            'argument_completion_threshold': self.argument_completion_threshold,
            'coherence_threshold': self.coherence_threshold,
            'use_sentence_embeddings': self.use_sentence_embeddings,
            'embedding_model': self.embedding_model,
            'preserve_citations': self.preserve_citations,
            'citation_context_window': self.citation_context_window,
            'resolve_cross_references': self.resolve_cross_references,
            'cross_ref_context_window': self.cross_ref_context_window,
            'validate_chunks': self.validate_chunks,
            'min_coherence_score': self.min_coherence_score,
            'max_complexity_score': self.max_complexity_score,
            'parallel_processing': self.parallel_processing,
            'max_workers': self.max_workers,
        }


@dataclass
class TextSegmentConfig:
    """Configuration for TextSegment objects"""
    
    # Metadata tracking
    track_positions: bool = True
    track_relationships: bool = True
    track_embeddings: bool = True
    
    # Relationship types
    relationship_types: List[str] = field(default_factory=lambda: [
        "parent", "child", "sibling", "citation", "cross_reference", "semantic_neighbor"
    ])
    
    # Confidence scoring
    calculate_confidence: bool = True
    confidence_factors: List[str] = field(default_factory=lambda: [
        "coherence", "completeness", "boundary_quality", "citation_integrity"
    ])
    
    # Storage optimization
    compress_text: bool = False
    store_original_formatting: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            'track_positions': self.track_positions,
            'track_relationships': self.track_relationships,
            'track_embeddings': self.track_embeddings,
            'relationship_types': self.relationship_types,
            'calculate_confidence': self.calculate_confidence,
            'confidence_factors': self.confidence_factors,
            'compress_text': self.compress_text,
            'store_original_formatting': self.store_original_formatting,
        }


def get_default_config(discipline: AcademicDiscipline = AcademicDiscipline.GENERAL) -> Dict[str, Any]:
    """Get default configuration for specified academic discipline"""
    
    nlp_config = NLPPipelineConfig()
    chunking_config = ChunkingConfig(discipline=discipline)
    chunking_config.apply_discipline_settings()
    segment_config = TextSegmentConfig()
    
    return {
        'nlp': nlp_config.to_dict(),
        'chunking': chunking_config.to_dict(),
        'segments': segment_config.to_dict()
    }


def get_philosophy_config() -> Dict[str, Any]:
    """Get configuration optimized for philosophy texts"""
    return get_default_config(AcademicDiscipline.PHILOSOPHY)


def get_literature_config() -> Dict[str, Any]:
    """Get configuration optimized for literature texts"""
    return get_default_config(AcademicDiscipline.LITERATURE)


def get_social_sciences_config() -> Dict[str, Any]:
    """Get configuration optimized for social sciences texts"""
    return get_default_config(AcademicDiscipline.SOCIAL_SCIENCES)


# Academic-specific patterns and rules
CITATION_PATTERNS = {
    'apa': r'\([^)]*\d{4}[^)]*\)',
    'mla': r'[A-Z][a-z]+ \d+',
    'chicago': r'\([^)]*\d{4}[^)]*\)',
    'ieee': r'\[\d+\]',
    'numbered': r'\[\d+\]',
    'author_year': r'\([^)]*\d{4}[^)]*\)',
    'footnote': r'[¹²³⁴⁵⁶⁷⁸⁹]',
}

DISCOURSE_MARKERS = {
    'claim': [
        'argue', 'claim', 'assert', 'propose', 'suggest', 'contend', 
        'maintain', 'hold', 'posit', 'advance'
    ],
    'evidence': [
        'evidence', 'data', 'shows', 'demonstrates', 'indicates', 'reveals',
        'proves', 'confirms', 'supports', 'establishes'
    ],
    'conclusion': [
        'therefore', 'thus', 'hence', 'consequently', 'in conclusion',
        'it follows', 'as a result', 'accordingly'
    ],
    'contrast': [
        'however', 'but', 'nevertheless', 'on the contrary', 'conversely',
        'in contrast', 'on the other hand', 'yet', 'still'
    ],
    'support': [
        'furthermore', 'moreover', 'additionally', 'in addition',
        'similarly', 'likewise', 'also', 'besides'
    ],
    'elaboration': [
        'in other words', 'that is', 'specifically', 'namely',
        'for example', 'for instance', 'such as'
    ]
}

ACADEMIC_STRUCTURES = [
    'theorem', 'lemma', 'corollary', 'proposition',
    'definition', 'axiom', 'postulate',
    'proof', 'example', 'remark', 'note',
    'hypothesis', 'conjecture', 'claim'
]

# Cross-reference patterns
CROSS_REFERENCE_PATTERNS = [
    r'see\s+(chapter|section|page|figure|table)\s+\d+',
    r'as\s+(discussed|mentioned|noted|shown)\s+(above|below|earlier|later)',
    r'(cf\.|compare)\s+[A-Z][a-z]+',
    r'(supra|infra)\s+(note\s+)?\d+',
    r'(ibid\.|id\.)',
    r'(op\.\s*cit\.|loc\.\s*cit\.)'
]