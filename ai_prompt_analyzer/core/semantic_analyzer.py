"""Semantic analysis engine for AI prompts using NLP models."""

import asyncio
import re
from typing import Dict, List, Tuple, Set
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from loguru import logger

from ..models import AnalysisResult
from .config import settings


class SemanticAnalyzer:
    """Analyzes semantic content and patterns in AI prompts."""
    
    def __init__(self):
        """Initialize the semantic analyzer."""
        self.embedding_model = None
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 3),
            min_df=2
        )
        
        # Prompt engineering techniques patterns
        self.technique_patterns = {
            'few_shot_learning': [
                r'example.*:',
                r'for example',
                r'here are some examples',
                r'sample.*input.*output',
                r'demonstration'
            ],
            'chain_of_thought': [
                r'step by step',
                r'think step by step',
                r'reasoning process',
                r'explain your thinking',
                r'break down'
            ],
            'role_playing': [
                r'you are a',
                r'act as',
                r'pretend to be',
                r'roleplay',
                r'imagine you are'
            ],
            'constraint_specification': [
                r'must not',
                r'should not',
                r'requirements?:',
                r'constraints?:',
                r'limitations?:'
            ],
            'output_formatting': [
                r'format.*output',
                r'response format',
                r'structure.*response',
                r'json format',
                r'markdown format'
            ],
            'context_provision': [
                r'given.*context',
                r'background information',
                r'context:',
                r'situation:',
                r'scenario:'
            ],
            'iterative_refinement': [
                r'refine',
                r'improve',
                r'revise',
                r'iterate',
                r'enhance'
            ],
            'metacognitive_prompting': [
                r'think about',
                r'consider',
                r'reflect on',
                r'analyze your',
                r'evaluate'
            ],
            'persona_adoption': [
                r'speak as',
                r'write in the style of',
                r'tone of',
                r'voice of',
                r'personality'
            ],
            'zero_shot_prompting': [
                r'without examples',
                r'directly',
                r'immediately',
                r'straight to'
            ]
        }
        
        # Domain categories
        self.domain_keywords = {
            'coding': [
                'code', 'programming', 'software', 'debug', 'algorithm',
                'function', 'variable', 'class', 'method', 'api'
            ],
            'writing': [
                'write', 'article', 'essay', 'content', 'blog',
                'story', 'narrative', 'draft', 'edit', 'grammar'
            ],
            'analysis': [
                'analyze', 'analysis', 'evaluate', 'assess', 'examine',
                'review', 'study', 'research', 'investigate'
            ],
            'creative': [
                'creative', 'imagine', 'brainstorm', 'innovate', 'design',
                'artistic', 'original', 'unique', 'inventive'
            ],
            'education': [
                'teach', 'learn', 'explain', 'tutorial', 'lesson',
                'education', 'academic', 'study', 'course'
            ],
            'business': [
                'business', 'strategy', 'marketing', 'sales', 'management',
                'finance', 'economics', 'profit', 'revenue'
            ],
            'technical': [
                'technical', 'engineering', 'system', 'architecture',
                'infrastructure', 'implementation', 'configuration'
            ],
            'conversational': [
                'chat', 'conversation', 'dialogue', 'talk', 'discuss',
                'communicate', 'respond', 'interact'
            ]
        }
    
    async def initialize_models(self):
        """Initialize ML models asynchronously."""
        if self.embedding_model is None:
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.embedding_model = await loop.run_in_executor(
                None, SentenceTransformer, settings.embedding_model
            )
            logger.info("Embedding model loaded successfully")
    
    async def analyze_semantic_content(self, content: str) -> Dict[str, any]:
        """Analyze semantic content of a prompt.
        
        Args:
            content: Prompt content to analyze
            
        Returns:
            Dictionary with semantic analysis results
        """
        await self.initialize_models()
        
        # Generate embeddings
        embeddings = await self._generate_embeddings([content])
        
        # Detect techniques
        techniques = self._detect_techniques(content)
        
        # Categorize content
        categories = self._categorize_content(content)
        
        # Extract patterns
        patterns = self._extract_patterns(content)
        
        # Analyze complexity
        complexity = self._analyze_complexity(content)
        
        # Detect intent
        intent = self._analyze_intent(content)
        
        return {
            'embeddings': embeddings[0].tolist() if embeddings else [],
            'techniques': techniques,
            'categories': categories,
            'patterns': patterns,
            'complexity_score': complexity,
            'intent': intent,
            'semantic_similarity': await self._calculate_similarity_features(content)
        }
    
    async def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Embeddings array
        """
        if not self.embedding_model:
            await self.initialize_models()
        
        try:
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, self.embedding_model.encode, texts
            )
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return np.array([])
    
    def _detect_techniques(self, content: str) -> List[str]:
        """Detect prompt engineering techniques.
        
        Args:
            content: Content to analyze
            
        Returns:
            List of detected techniques
        """
        detected = []
        content_lower = content.lower()
        
        for technique, patterns in self.technique_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    detected.append(technique)
                    break
        
        return detected
    
    def _categorize_content(self, content: str) -> List[str]:
        """Categorize content by domain.
        
        Args:
            content: Content to categorize
            
        Returns:
            List of categories
        """
        categories = []
        content_lower = content.lower()
        
        for category, keywords in self.domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score >= 2:  # Threshold for category assignment
                categories.append(category)
        
        return categories
    
    def _extract_patterns(self, content: str) -> List[str]:
        """Extract common patterns from content.
        
        Args:
            content: Content to analyze
            
        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Common prompt patterns
        pattern_regexes = {
            'question_answer': r'\?.*\n.*answer',
            'input_output': r'input:.*output:',
            'template_structure': r'\{.*\}',
            'conditional_logic': r'if.*then',
            'enumeration': r'1\.|2\.|•|-)/',
            'emphasis': r'\*\*.*\*\*|__.*__|ALL CAPS',
            'role_definition': r'(role|character|persona):\s*\w+',
            'instruction_sequence': r'(first|second|third|next|then|finally)',
            'quality_indicators': r'(best|high[- ]quality|excellent|perfect)',
            'safety_constraints': r'(safe|ethical|appropriate|respectful)'
        }
        
        for pattern_name, regex in pattern_regexes.items():
            if re.search(regex, content, re.IGNORECASE):
                patterns.append(pattern_name)
        
        return patterns
    
    def _analyze_complexity(self, content: str) -> float:
        """Analyze complexity of prompt content.
        
        Args:
            content: Content to analyze
            
        Returns:
            Complexity score (0-10)
        """
        # Factors that increase complexity
        word_count = len(content.split())
        sentence_count = len(re.split(r'[.!?]+', content))
        
        # Average words per sentence
        avg_words_per_sentence = word_count / max(sentence_count, 1)
        
        # Count of complex elements
        complex_elements = 0
        
        # Multi-step instructions
        if re.search(r'(step|phase|stage|first|second|third)', content.lower()):
            complex_elements += 1
        
        # Conditional logic
        if re.search(r'(if|when|unless|provided|given)', content.lower()):
            complex_elements += 1
        
        # Multiple requirements
        if re.search(r'(and|also|additionally|furthermore)', content.lower()):
            complex_elements += 1
        
        # Technical terms
        technical_patterns = [
            r'algorithm', r'implementation', r'optimization',
            r'configuration', r'parameters', r'metadata'
        ]
        for pattern in technical_patterns:
            if re.search(pattern, content.lower()):
                complex_elements += 0.5
        
        # Calculate complexity score
        length_score = min(word_count / 100, 3)  # Cap at 3
        structure_score = min(avg_words_per_sentence / 15, 2)  # Cap at 2
        element_score = min(complex_elements, 5)  # Cap at 5
        
        complexity = length_score + structure_score + element_score
        return min(complexity, 10.0)  # Cap at 10
    
    def _analyze_intent(self, content: str) -> str:
        """Analyze the intent of the prompt.
        
        Args:
            content: Content to analyze
            
        Returns:
            Detected intent category
        """
        content_lower = content.lower()
        
        intent_patterns = {
            'instruction': [
                'please', 'can you', 'help me', 'assist', 'guide'
            ],
            'query': [
                'what', 'how', 'why', 'when', 'where', 'which', '?'
            ],
            'generation': [
                'create', 'generate', 'write', 'produce', 'make'
            ],
            'analysis': [
                'analyze', 'examine', 'evaluate', 'assess', 'review'
            ],
            'transformation': [
                'convert', 'transform', 'translate', 'rewrite', 'modify'
            ],
            'explanation': [
                'explain', 'describe', 'clarify', 'elaborate', 'detail'
            ],
            'comparison': [
                'compare', 'contrast', 'difference', 'similar', 'versus'
            ],
            'synthesis': [
                'combine', 'merge', 'integrate', 'synthesize', 'unify'
            ]
        }
        
        intent_scores = {}
        for intent, patterns in intent_patterns.items():
            score = sum(1 for pattern in patterns if pattern in content_lower)
            intent_scores[intent] = score
        
        # Return the intent with highest score
        if intent_scores:
            return max(intent_scores, key=intent_scores.get)
        
        return 'general'
    
    async def _calculate_similarity_features(self, content: str) -> Dict[str, float]:
        """Calculate similarity features for the content.
        
        Args:
            content: Content to analyze
            
        Returns:
            Dictionary of similarity features
        """
        # This would typically compare against a database of known prompts
        # For now, return basic features
        return {
            'uniqueness_score': self._calculate_uniqueness(content),
            'common_phrase_density': self._calculate_common_phrase_density(content),
            'template_similarity': self._calculate_template_similarity(content)
        }
    
    def _calculate_uniqueness(self, content: str) -> float:
        """Calculate uniqueness score for content.
        
        Args:
            content: Content to analyze
            
        Returns:
            Uniqueness score (0-1)
        """
        # Simple uniqueness based on rare words and phrases
        words = content.lower().split()
        
        # Count rare words (longer than 6 chars, not common)
        common_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
            'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day',
            'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new',
            'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did',
            'they', 'them', 'this', 'that', 'with', 'have', 'from',
            'will', 'what', 'when', 'were', 'been', 'said', 'each',
            'make', 'like', 'into', 'time', 'very', 'after', 'words'
        }
        
        rare_words = sum(1 for word in words 
                        if len(word) > 6 and word not in common_words)
        
        uniqueness = min(rare_words / max(len(words), 1), 1.0)
        return uniqueness
    
    def _calculate_common_phrase_density(self, content: str) -> float:
        """Calculate density of common phrases.
        
        Args:
            content: Content to analyze
            
        Returns:
            Common phrase density (0-1)
        """
        common_phrases = [
            'you are', 'please help', 'can you', 'i need',
            'step by step', 'make sure', 'keep in mind',
            'it is important', 'please note', 'remember to'
        ]
        
        content_lower = content.lower()
        phrase_count = sum(1 for phrase in common_phrases 
                          if phrase in content_lower)
        
        # Normalize by content length
        density = phrase_count / max(len(content.split()) / 10, 1)
        return min(density, 1.0)
    
    def _calculate_template_similarity(self, content: str) -> float:
        """Calculate similarity to common templates.
        
        Args:
            content: Content to analyze
            
        Returns:
            Template similarity score (0-1)
        """
        template_indicators = [
            r'\{.*\}',  # Template variables
            r'<.*>',    # XML-like tags
            r'\[.*\]',  # Bracket notation
            r'{{.*}}',  # Double bracket notation
            r'%%.*%%'   # Percentage notation
        ]
        
        template_score = 0
        for pattern in template_indicators:
            if re.search(pattern, content):
                template_score += 0.2
        
        return min(template_score, 1.0)
    
    async def cluster_prompts(self, prompts: List[str], n_clusters: int = 5) -> Dict[int, List[int]]:
        """Cluster prompts by semantic similarity.
        
        Args:
            prompts: List of prompt texts
            n_clusters: Number of clusters
            
        Returns:
            Dictionary mapping cluster IDs to prompt indices
        """
        if len(prompts) < n_clusters:
            # If fewer prompts than clusters, assign each to its own cluster
            return {i: [i] for i in range(len(prompts))}
        
        try:
            # Generate embeddings
            embeddings = await self._generate_embeddings(prompts)
            
            if embeddings.size == 0:
                return {0: list(range(len(prompts)))}
            
            # Perform clustering
            loop = asyncio.get_event_loop()
            kmeans = await loop.run_in_executor(
                None, lambda: KMeans(n_clusters=n_clusters, random_state=42).fit(embeddings)
            )
            
            # Group by clusters
            clusters = {}
            for i, label in enumerate(kmeans.labels_):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(i)
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error clustering prompts: {e}")
            return {0: list(range(len(prompts)))}