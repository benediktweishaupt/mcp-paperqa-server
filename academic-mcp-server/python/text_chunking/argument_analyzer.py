"""
Advanced Argument Analysis System for Academic Text Chunking

This module implements comprehensive argument detection, dependency parsing,
and graph representation for preserving argumentative structures in academic texts.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import json

try:
    import spacy
    from spacy.tokens import Doc, Token, Span
    from spacy.matcher import Matcher, DependencyMatcher
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    # Mock classes for when spaCy is not available
    class Doc:
        def __init__(self):
            self.sents = []
    class Token:
        pass
    class Span:
        pass
    class Matcher:
        def __init__(self, vocab):
            pass
    class DependencyMatcher:
        def __init__(self, vocab):
            pass

try:
    from .nlp_pipeline import AcademicNLPPipeline
except ImportError:
    try:
        from nlp_pipeline import AcademicNLPPipeline
    except ImportError:
        class AcademicNLPPipeline:
            def __init__(self):
                pass


class ArgumentComponent(Enum):
    """Types of argument components based on Toulmin's model"""
    CLAIM = "claim"
    EVIDENCE = "evidence"
    WARRANT = "warrant"
    BACKING = "backing"
    REBUTTAL = "rebuttal"
    QUALIFIER = "qualifier"
    CONCLUSION = "conclusion"
    PREMISE = "premise"
    COUNTER_CLAIM = "counter_claim"


class LogicalRelation(Enum):
    """Types of logical relationships between argument components"""
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    ELABORATES = "elaborates"
    EXEMPLIFIES = "exemplifies"
    CAUSES = "causes"
    FOLLOWS_FROM = "follows_from"
    CONDITIONAL = "conditional"
    CONCESSION = "concession"
    SEQUENCE = "sequence"


@dataclass
class ArgumentUnit:
    """Represents a single argument unit with its components and relationships"""
    unit_id: str
    text: str
    start_pos: int
    end_pos: int
    component_type: ArgumentComponent
    confidence: float
    
    # Logical structure
    dependencies: List[Tuple[str, LogicalRelation]] = field(default_factory=list)  # (unit_id, relation)
    supports: List[str] = field(default_factory=list)  # IDs of units this supports
    supported_by: List[str] = field(default_factory=list)  # IDs of units supporting this
    
    # Linguistic features
    discourse_markers: List[str] = field(default_factory=list)
    modal_verbs: List[str] = field(default_factory=list)
    hedging_expressions: List[str] = field(default_factory=list)
    epistemic_markers: List[str] = field(default_factory=list)
    
    # Context
    sentence_indices: List[int] = field(default_factory=list)
    paragraph_id: Optional[str] = None
    nesting_level: int = 0  # 0 = main argument, 1+ = nested sub-arguments


@dataclass
class ArgumentGraph:
    """Graph representation of argumentative structure in text"""
    graph_id: str
    text_source: str
    argument_units: Dict[str, ArgumentUnit] = field(default_factory=dict)
    
    # Graph structure
    edges: List[Tuple[str, str, LogicalRelation]] = field(default_factory=list)  # (from_id, to_id, relation)
    root_claims: List[str] = field(default_factory=list)  # Main claim IDs
    sub_arguments: Dict[str, List[str]] = field(default_factory=dict)  # nested argument chains
    
    # Analysis metadata
    complexity_score: float = 0.0
    coherence_score: float = 0.0
    completeness_score: float = 0.0


class ArgumentAnalyzer:
    """
    Advanced argument analyzer using dependency parsing and rhetorical structure theory
    
    Features:
    - Dependency-based logical connection tracking
    - Multi-level argument nesting detection
    - Toulmin model argument component classification
    - Argument graph construction and analysis
    - Academic discourse pattern recognition
    """
    
    def __init__(self, nlp_pipeline: Optional[AcademicNLPPipeline] = None):
        """Initialize the argument analyzer"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize NLP pipeline
        if nlp_pipeline and SPACY_AVAILABLE:
            self.nlp_pipeline = nlp_pipeline
        elif SPACY_AVAILABLE:
            self.nlp_pipeline = AcademicNLPPipeline()
        else:
            self.logger.warning("spaCy not available, using mock implementation")
            self.nlp_pipeline = AcademicNLPPipeline()
        
        # Initialize matchers for complex pattern detection
        if SPACY_AVAILABLE and hasattr(self.nlp_pipeline, 'nlp'):
            self.dependency_matcher = DependencyMatcher(self.nlp_pipeline.nlp.vocab)
            self.phrase_matcher = Matcher(self.nlp_pipeline.nlp.vocab)
            self._load_argument_patterns()
        
        # Argument component classification patterns
        self.component_patterns = self._load_component_patterns()
        
        # Logical relation indicators
        self.relation_indicators = self._load_relation_indicators()
        
        self.logger.info("ArgumentAnalyzer initialized")
    
    def _load_argument_patterns(self):
        """Load spaCy patterns for argument structure detection"""
        if not SPACY_AVAILABLE:
            return
        
        # Dependency patterns for logical connections
        causal_pattern = [
            {
                "RIGHT_ID": "cause",
                "RIGHT_ATTRS": {"LEMMA": {"IN": ["cause", "result", "lead", "produce"]}}
            },
            {
                "LEFT_ID": "cause",
                "REL_OP": ">",
                "RIGHT_ID": "effect",
                "RIGHT_ATTRS": {"DEP": "dobj"}
            }
        ]
        
        conditional_pattern = [
            {
                "RIGHT_ID": "if_token",
                "RIGHT_ATTRS": {"LOWER": "if"}
            },
            {
                "LEFT_ID": "if_token", 
                "REL_OP": ">",
                "RIGHT_ID": "condition",
                "RIGHT_ATTRS": {"DEP": "advcl"}
            }
        ]
        
        try:
            self.dependency_matcher.add("CAUSAL", [causal_pattern])
            self.dependency_matcher.add("CONDITIONAL", [conditional_pattern])
        except Exception as e:
            self.logger.warning(f"Could not load dependency patterns: {e}")
    
    def _load_component_patterns(self) -> Dict[ArgumentComponent, List[str]]:
        """Load patterns for argument component classification"""
        return {
            ArgumentComponent.CLAIM: [
                'argue', 'assert', 'claim', 'maintain', 'contend', 'propose',
                'suggest', 'believe', 'think', 'hold', 'posit', 'submit'
            ],
            ArgumentComponent.EVIDENCE: [
                'evidence', 'data', 'research', 'study', 'findings', 'results',
                'shows', 'demonstrates', 'indicates', 'reveals', 'proves',
                'according to', 'research shows', 'data indicates'
            ],
            ArgumentComponent.WARRANT: [
                'because', 'since', 'as', 'given that', 'assuming',
                'based on', 'considering', 'in light of'
            ],
            ArgumentComponent.REBUTTAL: [
                'however', 'but', 'nevertheless', 'although', 'despite',
                'on the contrary', 'conversely', 'yet', 'still'
            ],
            ArgumentComponent.CONCLUSION: [
                'therefore', 'thus', 'hence', 'consequently', 'accordingly',
                'as a result', 'in conclusion', 'to conclude', 'finally'
            ],
            ArgumentComponent.QUALIFIER: [
                'probably', 'likely', 'possibly', 'perhaps', 'might',
                'could', 'may', 'seemingly', 'apparently', 'arguably'
            ]
        }
    
    def _load_relation_indicators(self) -> Dict[LogicalRelation, List[str]]:
        """Load indicators for logical relations between argument units"""
        return {
            LogicalRelation.SUPPORTS: [
                'furthermore', 'moreover', 'additionally', 'also', 'in addition',
                'similarly', 'likewise', 'correspondingly'
            ],
            LogicalRelation.CONTRADICTS: [
                'however', 'but', 'conversely', 'on the contrary', 'nevertheless',
                'nonetheless', 'in contrast', 'alternatively'
            ],
            LogicalRelation.ELABORATES: [
                'specifically', 'particularly', 'namely', 'that is', 'in other words',
                'more precisely', 'to elaborate', 'for instance'
            ],
            LogicalRelation.EXEMPLIFIES: [
                'for example', 'for instance', 'such as', 'including', 'notably',
                'e.g.', 'i.e.', 'case in point'
            ],
            LogicalRelation.CAUSES: [
                'because', 'since', 'as a result of', 'due to', 'owing to',
                'leads to', 'results in', 'causes', 'produces'
            ],
            LogicalRelation.CONDITIONAL: [
                'if', 'unless', 'provided that', 'assuming', 'supposing',
                'in case', 'on condition that'
            ],
            LogicalRelation.CONCESSION: [
                'although', 'though', 'even though', 'despite', 'in spite of',
                'granted', 'admittedly', 'while'
            ]
        }
    
    def analyze_argumentative_structure(self, text: str, document_id: Optional[str] = None) -> ArgumentGraph:
        """
        Analyze text to extract comprehensive argumentative structure
        
        Args:
            text: Input academic text
            document_id: Optional document identifier
            
        Returns:
            ArgumentGraph with complete argument analysis
        """
        if not text.strip():
            return ArgumentGraph(graph_id=document_id or "empty", text_source=text)
        
        self.logger.info(f"Analyzing argumentative structure in text of {len(text)} characters")
        
        # Process text through NLP pipeline
        doc = self.nlp_pipeline.process_text(text)
        
        # Step 1: Identify argument units and components
        argument_units = self._identify_argument_units(doc, text)
        
        # Step 2: Extract logical connections using dependency parsing
        connections = self._extract_logical_connections(doc, argument_units)
        
        # Step 3: Detect nested arguments and sub-arguments
        nested_structure = self._detect_nested_arguments(argument_units, connections)
        
        # Step 4: Build argument graph
        graph = self._build_argument_graph(text, argument_units, connections, nested_structure, document_id)
        
        # Step 5: Calculate analysis metrics
        graph = self._calculate_argument_metrics(graph)
        
        self.logger.info(f"Identified {len(graph.argument_units)} argument units with {len(graph.edges)} logical connections")
        
        return graph
    
    def _identify_argument_units(self, doc: Doc, text: str) -> Dict[str, ArgumentUnit]:
        """Identify individual argument units and classify their components"""
        units = {}
        unit_counter = 0
        
        # Analyze each sentence as potential argument unit
        for sent_idx, sent in enumerate(doc.sents):
            unit_id = f"unit_{unit_counter:03d}"
            
            # Classify argument component type
            component_type, confidence = self._classify_argument_component(sent)
            
            if component_type and confidence > 0.3:  # Minimum confidence threshold
                # Extract linguistic features
                discourse_markers = self._extract_discourse_markers(sent)
                modal_verbs = self._extract_modal_verbs(sent)
                hedging_expressions = self._extract_hedging_expressions(sent)
                epistemic_markers = self._extract_epistemic_markers(sent)
                
                unit = ArgumentUnit(
                    unit_id=unit_id,
                    text=sent.text.strip(),
                    start_pos=sent.start_char,
                    end_pos=sent.end_char,
                    component_type=component_type,
                    confidence=confidence,
                    discourse_markers=discourse_markers,
                    modal_verbs=modal_verbs,
                    hedging_expressions=hedging_expressions,
                    epistemic_markers=epistemic_markers,
                    sentence_indices=[sent_idx]
                )
                
                units[unit_id] = unit
                unit_counter += 1
        
        return units
    
    def _classify_argument_component(self, sent: Span) -> Tuple[Optional[ArgumentComponent], float]:
        """Classify sentence as argument component type with confidence score"""
        if not SPACY_AVAILABLE:
            return ArgumentComponent.CLAIM, 0.5  # Default for mock implementation
        
        sent_text = sent.text.lower()
        scores = defaultdict(float)
        
        # Pattern-based classification
        for component, patterns in self.component_patterns.items():
            for pattern in patterns:
                if pattern in sent_text:
                    # Weight by pattern length and position
                    weight = len(pattern.split()) / len(sent_text.split())
                    position_weight = 2.0 if sent_text.find(pattern) < len(sent_text) * 0.3 else 1.0
                    scores[component] += weight * position_weight
        
        # Syntactic features
        has_modal = any(token.tag_ in ['MD'] for token in sent)
        has_epistemic = any(token.lemma_ in ['think', 'believe', 'seem', 'appear'] for token in sent)
        has_citation = '(' in sent.text and any(char.isdigit() for char in sent.text)
        
        if has_modal:
            scores[ArgumentComponent.QUALIFIER] += 0.3
        if has_epistemic:
            scores[ArgumentComponent.CLAIM] += 0.2
        if has_citation:
            scores[ArgumentComponent.EVIDENCE] += 0.4
        
        # Return highest scoring component
        if scores:
            best_component = max(scores.items(), key=lambda x: x[1])
            return best_component[0], min(best_component[1], 1.0)
        
        return None, 0.0
    
    def _extract_discourse_markers(self, sent: Span) -> List[str]:
        """Extract discourse markers from sentence"""
        markers = []
        sent_text = sent.text.lower()
        
        all_markers = []
        for relation_markers in self.relation_indicators.values():
            all_markers.extend(relation_markers)
        
        for marker in all_markers:
            if marker in sent_text:
                markers.append(marker)
        
        return markers
    
    def _extract_modal_verbs(self, sent: Span) -> List[str]:
        """Extract modal verbs indicating epistemic stance"""
        if not SPACY_AVAILABLE:
            return []
        
        modals = []
        for token in sent:
            if token.tag_ == 'MD':  # Modal verb tag
                modals.append(token.text.lower())
        
        return modals
    
    def _extract_hedging_expressions(self, sent: Span) -> List[str]:
        """Extract hedging expressions indicating uncertainty"""
        hedges = ['perhaps', 'possibly', 'likely', 'probably', 'seemingly', 
                 'apparently', 'arguably', 'presumably', 'supposedly']
        
        found_hedges = []
        sent_text = sent.text.lower()
        
        for hedge in hedges:
            if hedge in sent_text:
                found_hedges.append(hedge)
        
        return found_hedges
    
    def _extract_epistemic_markers(self, sent: Span) -> List[str]:
        """Extract epistemic markers indicating certainty/uncertainty"""
        epistemic = ['certain', 'sure', 'definite', 'clear', 'obvious', 
                    'uncertain', 'unclear', 'doubtful', 'questionable']
        
        found_markers = []
        sent_text = sent.text.lower()
        
        for marker in epistemic:
            if marker in sent_text:
                found_markers.append(marker)
        
        return found_markers
    
    def _extract_logical_connections(self, doc: Doc, argument_units: Dict[str, ArgumentUnit]) -> List[Tuple[str, str, LogicalRelation]]:
        """Extract logical connections between argument units using dependency parsing"""
        connections = []
        
        if not SPACY_AVAILABLE or not argument_units:
            return connections
        
        # Convert units to sentence mapping for efficient lookup
        sent_to_unit = {}
        for unit_id, unit in argument_units.items():
            for sent_idx in unit.sentence_indices:
                sent_to_unit[sent_idx] = unit_id
        
        sentences = list(doc.sents)
        
        # Analyze adjacent sentences for connections
        for i in range(len(sentences) - 1):
            curr_sent = sentences[i]
            next_sent = sentences[i + 1]
            
            curr_unit_id = sent_to_unit.get(i)
            next_unit_id = sent_to_unit.get(i + 1)
            
            if curr_unit_id and next_unit_id and curr_unit_id != next_unit_id:
                # Detect logical relation based on discourse markers
                relation = self._detect_logical_relation(curr_sent, next_sent)
                if relation:
                    connections.append((curr_unit_id, next_unit_id, relation))
        
        # Use dependency patterns if available
        if hasattr(self, 'dependency_matcher'):
            try:
                matches = self.dependency_matcher(doc)
                for match_id, token_ids in matches:
                    # Process dependency-based connections
                    pattern_name = doc.vocab.strings[match_id]
                    if pattern_name == "CAUSAL":
                        # Find argument units involved in causal relation
                        for token_id in token_ids:
                            # Implementation would map tokens to argument units
                            pass
            except Exception as e:
                self.logger.debug(f"Dependency matching failed: {e}")
        
        return connections
    
    def _detect_logical_relation(self, sent1: Span, sent2: Span) -> Optional[LogicalRelation]:
        """Detect logical relation between two sentences"""
        sent2_text = sent2.text.lower()
        
        # Check for relation indicators at start of second sentence
        for relation, indicators in self.relation_indicators.items():
            for indicator in indicators:
                if sent2_text.startswith(indicator) or f" {indicator} " in sent2_text[:50]:
                    return relation
        
        return None
    
    def _detect_nested_arguments(self, argument_units: Dict[str, ArgumentUnit], 
                                connections: List[Tuple[str, str, LogicalRelation]]) -> Dict[str, List[str]]:
        """Detect nested arguments and sub-argument chains"""
        nested_structure = defaultdict(list)
        
        # Build adjacency list for connection graph
        graph = defaultdict(list)
        for from_id, to_id, relation in connections:
            graph[from_id].append((to_id, relation))
        
        # Identify argument chains using BFS
        visited = set()
        
        for unit_id in argument_units:
            if unit_id not in visited:
                chain = self._extract_argument_chain(unit_id, graph, argument_units, visited)
                if len(chain) > 1:  # Multi-unit argument
                    main_claim = self._identify_main_claim(chain, argument_units)
                    nested_structure[main_claim] = [uid for uid in chain if uid != main_claim]
        
        return nested_structure
    
    def _extract_argument_chain(self, start_id: str, graph: Dict[str, List[Tuple[str, LogicalRelation]]], 
                               argument_units: Dict[str, ArgumentUnit], visited: Set[str]) -> List[str]:
        """Extract connected argument chain using BFS"""
        chain = []
        queue = deque([start_id])
        local_visited = set()
        
        while queue:
            unit_id = queue.popleft()
            if unit_id in local_visited:
                continue
                
            local_visited.add(unit_id)
            visited.add(unit_id)
            chain.append(unit_id)
            
            # Add connected units
            for next_id, relation in graph.get(unit_id, []):
                if next_id not in local_visited:
                    queue.append(next_id)
        
        return chain
    
    def _identify_main_claim(self, chain: List[str], argument_units: Dict[str, ArgumentUnit]) -> str:
        """Identify the main claim in an argument chain"""
        # Prioritize CLAIM components, then highest confidence
        claims = [uid for uid in chain if argument_units[uid].component_type == ArgumentComponent.CLAIM]
        
        if claims:
            return max(claims, key=lambda uid: argument_units[uid].confidence)
        else:
            # Return highest confidence unit
            return max(chain, key=lambda uid: argument_units[uid].confidence)
    
    def _build_argument_graph(self, text: str, argument_units: Dict[str, ArgumentUnit], 
                             connections: List[Tuple[str, str, LogicalRelation]],
                             nested_structure: Dict[str, List[str]], 
                             document_id: Optional[str] = None) -> ArgumentGraph:
        """Build comprehensive argument graph"""
        
        graph_id = document_id or f"graph_{hash(text) % 10000}"
        
        graph = ArgumentGraph(
            graph_id=graph_id,
            text_source=text,
            argument_units=argument_units,
            edges=connections,
            sub_arguments=nested_structure
        )
        
        # Identify root claims (claims not supported by other claims in this text)
        supported_units = set()
        for _, to_id, relation in connections:
            if relation in [LogicalRelation.SUPPORTS, LogicalRelation.ELABORATES]:
                supported_units.add(to_id)
        
        graph.root_claims = [
            unit_id for unit_id, unit in argument_units.items()
            if unit.component_type == ArgumentComponent.CLAIM and unit_id not in supported_units
        ]
        
        # Update argument units with relationship information
        for from_id, to_id, relation in connections:
            if relation == LogicalRelation.SUPPORTS:
                argument_units[from_id].supports.append(to_id)
                argument_units[to_id].supported_by.append(from_id)
            
            argument_units[from_id].dependencies.append((to_id, relation))
        
        # Set nesting levels
        for main_claim, sub_args in nested_structure.items():
            for sub_arg in sub_args:
                if sub_arg in argument_units:
                    argument_units[sub_arg].nesting_level = 1
        
        return graph
    
    def _calculate_argument_metrics(self, graph: ArgumentGraph) -> ArgumentGraph:
        """Calculate complexity, coherence, and completeness scores for argument graph"""
        
        if not graph.argument_units:
            return graph
        
        num_units = len(graph.argument_units)
        num_connections = len(graph.edges)
        
        # Complexity: based on number of units, connections, and nesting
        max_nesting = max((unit.nesting_level for unit in graph.argument_units.values()), default=0)
        graph.complexity_score = min(1.0, (num_units + num_connections + max_nesting * 5) / 50)
        
        # Coherence: based on connection density and logical consistency
        if num_units > 1:
            connection_density = num_connections / (num_units * (num_units - 1) / 2)
            graph.coherence_score = min(1.0, connection_density * 2)
        else:
            graph.coherence_score = 1.0
        
        # Completeness: based on presence of different argument components
        component_types = set(unit.component_type for unit in graph.argument_units.values())
        expected_components = {ArgumentComponent.CLAIM, ArgumentComponent.EVIDENCE}
        present_ratio = len(component_types.intersection(expected_components)) / len(expected_components)
        graph.completeness_score = present_ratio
        
        return graph
    
    def get_argument_boundaries(self, graph: ArgumentGraph) -> List[Tuple[int, int]]:
        """Get argument boundaries for chunk preservation"""
        boundaries = []
        
        # Group units by argument chains
        for main_claim, sub_args in graph.sub_arguments.items():
            all_units = [main_claim] + sub_args
            
            # Find text span covering entire argument
            if all_units:
                units = [graph.argument_units[uid] for uid in all_units if uid in graph.argument_units]
                if units:
                    start_pos = min(unit.start_pos for unit in units)
                    end_pos = max(unit.end_pos for unit in units)
                    boundaries.append((start_pos, end_pos))
        
        # Add individual units not part of larger arguments
        for unit_id, unit in graph.argument_units.items():
            if unit_id not in graph.root_claims and unit.nesting_level == 0:
                boundaries.append((unit.start_pos, unit.end_pos))
        
        return boundaries
    
    def export_graph_to_dict(self, graph: ArgumentGraph) -> Dict[str, Any]:
        """Export argument graph to dictionary for serialization"""
        return {
            'graph_id': graph.graph_id,
            'text_source': graph.text_source,
            'argument_units': {
                unit_id: {
                    'unit_id': unit.unit_id,
                    'text': unit.text,
                    'start_pos': unit.start_pos,
                    'end_pos': unit.end_pos,
                    'component_type': unit.component_type.value,
                    'confidence': unit.confidence,
                    'dependencies': [(dep_id, rel.value) for dep_id, rel in unit.dependencies],
                    'supports': unit.supports,
                    'supported_by': unit.supported_by,
                    'discourse_markers': unit.discourse_markers,
                    'nesting_level': unit.nesting_level
                }
                for unit_id, unit in graph.argument_units.items()
            },
            'edges': [(from_id, to_id, rel.value) for from_id, to_id, rel in graph.edges],
            'root_claims': graph.root_claims,
            'sub_arguments': dict(graph.sub_arguments),
            'metrics': {
                'complexity_score': graph.complexity_score,
                'coherence_score': graph.coherence_score,
                'completeness_score': graph.completeness_score
            }
        }


# Utility functions for testing and validation
def test_argument_analyzer():
    """Test the argument analyzer with sample academic text"""
    sample_text = """
    This paper argues that current machine learning approaches have significant limitations in academic text processing.
    
    According to Smith et al. (2020), traditional NLP methods fail to capture argumentative structure effectively. 
    The evidence shows that 70% of academic arguments are misclassified by existing systems.
    
    However, our proposed method addresses these issues through semantic analysis and dependency parsing.
    Furthermore, the approach preserves argumentative coherence across text chunks.
    
    Therefore, we conclude that semantic chunking represents a substantial advancement in academic text processing.
    """
    
    try:
        analyzer = ArgumentAnalyzer()
        graph = analyzer.analyze_argumentative_structure(sample_text, "test_doc")
        
        print(f"🎯 Argument Analysis Results:")
        print(f"  📊 Units identified: {len(graph.argument_units)}")
        print(f"  🔗 Logical connections: {len(graph.edges)}")
        print(f"  📈 Complexity score: {graph.complexity_score:.2f}")
        print(f"  🎯 Coherence score: {graph.coherence_score:.2f}")
        print(f"  ✅ Completeness score: {graph.completeness_score:.2f}")
        
        print(f"\n📋 Argument Units:")
        for unit_id, unit in graph.argument_units.items():
            print(f"  {unit_id}: {unit.component_type.value} (conf: {unit.confidence:.2f})")
            print(f"    Text: {unit.text[:80]}...")
            if unit.discourse_markers:
                print(f"    Discourse markers: {unit.discourse_markers}")
        
        print(f"\n🔗 Logical Connections:")
        for from_id, to_id, relation in graph.edges:
            print(f"  {from_id} --{relation.value}--> {to_id}")
        
        return graph
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None


if __name__ == "__main__":
    test_argument_analyzer()