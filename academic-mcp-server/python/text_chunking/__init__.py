"""
Intelligent Text Chunking System for Academic Documents

This module provides semantic chunking that preserves complete argumentative units
and maintains logical flow in academic texts.
"""

from .nlp_pipeline import AcademicNLPPipeline
from .chunker import SemanticChunker, TextSegment
from .coherence_scorer import CoherenceScorer

__all__ = [
    'AcademicNLPPipeline',
    'SemanticChunker', 
    'TextSegment',
    'CoherenceScorer'
]