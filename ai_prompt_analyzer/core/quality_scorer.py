"""Quality scoring system for AI prompts."""

import re
from typing import Dict, List
import numpy as np
from loguru import logger

from ..models import QualityMetrics, PromptType, AIProvider


class QualityScorer:
    """Scores the quality of AI prompts on multiple dimensions."""
    
    def __init__(self):
        """Initialize the quality scorer."""
        
        # Clarity indicators
        self.clarity_positive = [
            r'specific', r'clear', r'precise', r'explicit',
            r'detailed', r'exact', r'concrete', r'definite'
        ]
        
        self.clarity_negative = [
            r'maybe', r'perhaps', r'unclear', r'vague',
            r'ambiguous', r'confusing', r'general'
        ]
        
        # Effectiveness indicators
        self.effectiveness_positive = [
            r'step by step', r'systematic', r'methodical',
            r'structured', r'organized', r'comprehensive',
            r'examples?', r'demonstrate', r'show'
        ]
        
        self.effectiveness_negative = [
            r'just', r'simply', r'basically', r'roughly',
            r'sort of', r'kind of', r'approximately'
        ]
        
        # Specificity indicators
        self.specificity_indicators = [
            r'must', r'should', r'exactly', r'precisely',
            r'requirements?', r'constraints?', r'format',
            r'length', r'style', r'tone', r'audience'
        ]
        
        # Completeness indicators
        self.completeness_indicators = [
            r'including', r'considering', r'accounting for',
            r'taking into account', r'comprehensive',
            r'complete', r'thorough', r'detailed'
        ]
        
        # Safety indicators
        self.safety_positive = [
            r'ethical', r'appropriate', r'respectful',
            r'safe', r'responsible', r'unbiased',
            r'inclusive', r'fair', r'neutral'
        ]
        
        self.safety_negative = [
            r'harmful', r'dangerous', r'offensive',
            r'inappropriate', r'biased', r'discriminatory',
            r'violent', r'illegal', r'unethical'
        ]
        
        # Best practices check
        self.best_practices = {
            'role_definition': r'(?:you are|act as|assume the role)',
            'context_provision': r'(?:context|background|given)',
            'output_specification': r'(?:format|structure|style|length)',
            'example_provision': r'(?:example|sample|demonstration)',
            'constraint_specification': r'(?:must|should|requirement|constraint)',
            'step_by_step': r'(?:step by step|systematic|process)',
            'quality_emphasis': r'(?:high quality|best|excellent|perfect)',
            'iteration_instruction': r'(?:refine|improve|iterate|enhance)'
        }
    
    def score_prompt(self, content: str, prompt_type: PromptType, 
                    ai_provider: AIProvider, techniques: List[str] = None) -> QualityMetrics:
        """Score a prompt on multiple quality dimensions.
        
        Args:
            content: Prompt content
            prompt_type: Type of prompt
            ai_provider: AI provider
            techniques: Detected techniques
            
        Returns:
            Quality metrics
        """
        techniques = techniques or []
        
        # Calculate individual scores
        clarity = self._score_clarity(content)
        effectiveness = self._score_effectiveness(content, techniques)
        specificity = self._score_specificity(content)
        completeness = self._score_completeness(content)
        safety = self._score_safety(content)
        
        # Apply type-specific adjustments
        clarity = self._adjust_for_type(clarity, prompt_type, 'clarity')
        effectiveness = self._adjust_for_type(effectiveness, prompt_type, 'effectiveness')
        
        # Apply provider-specific adjustments
        effectiveness = self._adjust_for_provider(effectiveness, ai_provider)
        
        # Calculate overall score (weighted average)
        overall = self._calculate_overall_score(
            clarity, effectiveness, specificity, completeness, safety
        )
        
        return QualityMetrics(
            clarity_score=clarity,
            effectiveness_score=effectiveness,
            specificity_score=specificity,
            completeness_score=completeness,
            safety_score=safety,
            overall_score=overall
        )
    
    def _score_clarity(self, content: str) -> float:
        """Score the clarity of a prompt.
        
        Args:
            content: Prompt content
            
        Returns:
            Clarity score (0-10)
        """
        content_lower = content.lower()
        
        # Base score
        score = 5.0
        
        # Positive indicators
        positive_count = sum(1 for pattern in self.clarity_positive
                           if re.search(pattern, content_lower))
        score += positive_count * 0.5
        
        # Negative indicators
        negative_count = sum(1 for pattern in self.clarity_negative
                           if re.search(pattern, content_lower))
        score -= negative_count * 0.5
        
        # Sentence structure analysis
        sentences = re.split(r'[.!?]+', content)
        avg_sentence_length = np.mean([len(s.split()) for s in sentences if s.strip()])
        
        # Optimal sentence length is 15-25 words
        if 15 <= avg_sentence_length <= 25:
            score += 1.0
        elif avg_sentence_length < 10 or avg_sentence_length > 30:
            score -= 1.0
        
        # Grammar and structure indicators
        if re.search(r'[A-Z][a-z]', content):  # Proper capitalization
            score += 0.5
        
        if content.count('.') > 0:  # Has periods
            score += 0.5
        
        # Question marks for queries
        if '?' in content and any(w in content_lower for w in ['what', 'how', 'why']):
            score += 0.5
        
        return min(max(score, 0.0), 10.0)
    
    def _score_effectiveness(self, content: str, techniques: List[str]) -> float:
        """Score the effectiveness of a prompt.
        
        Args:
            content: Prompt content
            techniques: Detected techniques
            
        Returns:
            Effectiveness score (0-10)
        """
        content_lower = content.lower()
        
        # Base score
        score = 5.0
        
        # Technique bonus
        score += len(techniques) * 0.5
        
        # Best practices check
        practices_found = 0
        for practice, pattern in self.best_practices.items():
            if re.search(pattern, content_lower):
                practices_found += 1
        
        score += practices_found * 0.3
        
        # Positive indicators
        positive_count = sum(1 for pattern in self.effectiveness_positive
                           if re.search(pattern, content_lower))
        score += positive_count * 0.4
        
        # Negative indicators
        negative_count = sum(1 for pattern in self.effectiveness_negative
                           if re.search(pattern, content_lower))
        score -= negative_count * 0.3
        
        # Length considerations
        word_count = len(content.split())
        if 20 <= word_count <= 200:  # Optimal range
            score += 1.0
        elif word_count < 10:  # Too short
            score -= 2.0
        elif word_count > 500:  # Too long
            score -= 1.0
        
        # Action words bonus
        action_words = [
            'create', 'generate', 'write', 'analyze', 'explain',
            'describe', 'summarize', 'compare', 'evaluate'
        ]
        action_count = sum(1 for word in action_words if word in content_lower)
        score += min(action_count * 0.3, 1.5)
        
        return min(max(score, 0.0), 10.0)
    
    def _score_specificity(self, content: str) -> float:
        """Score the specificity of a prompt.
        
        Args:
            content: Prompt content
            
        Returns:
            Specificity score (0-10)
        """
        content_lower = content.lower()
        
        # Base score
        score = 5.0
        
        # Specificity indicators
        specific_count = sum(1 for pattern in self.specificity_indicators
                           if re.search(pattern, content_lower))
        score += specific_count * 0.4
        
        # Numbers and quantities
        number_patterns = [
            r'\d+\s+(words?|sentences?|paragraphs?|points?|items?)',
            r'(exactly|precisely|at least|no more than)\s+\d+',
            r'\d+%', r'\d+\.\d+'
        ]
        
        for pattern in number_patterns:
            if re.search(pattern, content_lower):
                score += 0.5
        
        # Format specifications
        format_patterns = [
            r'json', r'csv', r'markdown', r'html', r'xml',
            r'bullet points?', r'numbered list', r'table',
            r'format:', r'structure:'
        ]
        
        format_count = sum(1 for pattern in format_patterns
                          if re.search(pattern, content_lower))
        score += format_count * 0.3
        
        # Constraint words
        constraint_words = ['must', 'should', 'required', 'necessary', 'essential']
        constraint_count = sum(1 for word in constraint_words if word in content_lower)
        score += constraint_count * 0.2
        
        # Vague words penalty
        vague_words = ['something', 'anything', 'whatever', 'somehow', 'general']
        vague_count = sum(1 for word in vague_words if word in content_lower)
        score -= vague_count * 0.5
        
        return min(max(score, 0.0), 10.0)
    
    def _score_completeness(self, content: str) -> float:
        """Score the completeness of a prompt.
        
        Args:
            content: Prompt content
            
        Returns:
            Completeness score (0-10)
        """
        content_lower = content.lower()
        
        # Base score
        score = 5.0
        
        # Completeness indicators
        complete_count = sum(1 for pattern in self.completeness_indicators
                           if re.search(pattern, content_lower))
        score += complete_count * 0.4
        
        # Essential components check
        components = {
            'task_definition': ['task', 'objective', 'goal', 'purpose'],
            'input_specification': ['input', 'given', 'provided', 'data'],
            'output_specification': ['output', 'result', 'response', 'format'],
            'context_provision': ['context', 'background', 'situation'],
            'constraints': ['constraint', 'requirement', 'must', 'should']
        }
        
        components_found = 0
        for component, keywords in components.items():
            if any(keyword in content_lower for keyword in keywords):
                components_found += 1
        
        score += components_found * 0.5
        
        # Coverage indicators
        coverage_words = [
            'all', 'every', 'each', 'comprehensive', 'complete',
            'thorough', 'detailed', 'full', 'entire'
        ]
        coverage_count = sum(1 for word in coverage_words if word in content_lower)
        score += min(coverage_count * 0.3, 1.5)
        
        # Missing information penalty
        incomplete_indicators = [
            'etc', '...', 'and so on', 'among others',
            'or similar', 'things like that'
        ]
        incomplete_count = sum(1 for pattern in incomplete_indicators
                             if pattern in content_lower)
        score -= incomplete_count * 0.5
        
        return min(max(score, 0.0), 10.0)
    
    def _score_safety(self, content: str) -> float:
        """Score the safety of a prompt.
        
        Args:
            content: Prompt content
            
        Returns:
            Safety score (0-10)
        """
        content_lower = content.lower()
        
        # Base score (assume safe unless proven otherwise)
        score = 8.0
        
        # Positive safety indicators
        positive_count = sum(1 for pattern in self.safety_positive
                           if re.search(pattern, content_lower))
        score += min(positive_count * 0.3, 2.0)
        
        # Negative safety indicators (major penalties)
        negative_count = sum(1 for pattern in self.safety_negative
                           if re.search(pattern, content_lower))
        score -= negative_count * 2.0
        
        # Bias indicators
        bias_patterns = [
            r'(men|women|boys|girls|males|females)\s+(?:are|should|must)',
            r'all\s+(?:race|religion|nationality|gender)',
            r'stereotype', r'prejudice', r'discrimination'
        ]
        
        bias_count = sum(1 for pattern in bias_patterns
                        if re.search(pattern, content_lower))
        score -= bias_count * 1.5
        
        # Privacy concerns
        privacy_patterns = [
            r'personal information', r'private data', r'ssn',
            r'social security', r'credit card', r'password'
        ]
        
        privacy_count = sum(1 for pattern in privacy_patterns
                          if re.search(pattern, content_lower))
        score -= privacy_count * 1.0
        
        # Manipulation indicators
        manipulation_patterns = [
            r'trick', r'deceive', r'manipulate', r'fool',
            r'lie', r'fake', r'pretend to be'
        ]
        
        manipulation_count = sum(1 for pattern in manipulation_patterns
                               if re.search(pattern, content_lower))
        score -= manipulation_count * 1.5
        
        return min(max(score, 0.0), 10.0)
    
    def _adjust_for_type(self, score: float, prompt_type: PromptType, 
                        metric: str) -> float:
        """Adjust score based on prompt type.
        
        Args:
            score: Original score
            prompt_type: Type of prompt
            metric: Metric being adjusted
            
        Returns:
            Adjusted score
        """
        adjustments = {
            PromptType.SYSTEM: {
                'clarity': 0.5,  # System prompts should be very clear
                'effectiveness': 0.3
            },
            PromptType.USER: {
                'clarity': 0.0,  # User prompts can be more casual
                'effectiveness': 0.2
            },
            PromptType.INSTRUCTION: {
                'clarity': 0.4,
                'effectiveness': 0.5  # Instructions should be highly effective
            },
            PromptType.FUNCTION: {
                'clarity': 0.6,  # Function prompts must be very clear
                'effectiveness': 0.4
            }
        }
        
        adjustment = adjustments.get(prompt_type, {}).get(metric, 0.0)
        return min(max(score + adjustment, 0.0), 10.0)
    
    def _adjust_for_provider(self, score: float, ai_provider: AIProvider) -> float:
        """Adjust score based on AI provider.
        
        Args:
            score: Original score
            ai_provider: AI provider
            
        Returns:
            Adjusted score
        """
        # Different providers have different strengths
        provider_adjustments = {
            AIProvider.OPENAI: 0.2,     # Strong instruction following
            AIProvider.ANTHROPIC: 0.3,  # Excellent with detailed prompts
            AIProvider.GOOGLE: 0.1,     # Good general performance
            AIProvider.XAI: 0.0,        # Neutral
            AIProvider.CURSOR: 0.2,     # Good for coding
            AIProvider.OTHER: 0.0       # Unknown capabilities
        }
        
        adjustment = provider_adjustments.get(ai_provider, 0.0)
        return min(max(score + adjustment, 0.0), 10.0)
    
    def _calculate_overall_score(self, clarity: float, effectiveness: float,
                               specificity: float, completeness: float,
                               safety: float) -> float:
        """Calculate overall quality score.
        
        Args:
            clarity: Clarity score
            effectiveness: Effectiveness score
            specificity: Specificity score
            completeness: Completeness score
            safety: Safety score
            
        Returns:
            Overall quality score
        """
        # Weighted average with safety being most important
        weights = {
            'safety': 0.3,
            'effectiveness': 0.25,
            'clarity': 0.2,
            'completeness': 0.15,
            'specificity': 0.1
        }
        
        overall = (
            safety * weights['safety'] +
            effectiveness * weights['effectiveness'] +
            clarity * weights['clarity'] +
            completeness * weights['completeness'] +
            specificity * weights['specificity']
        )
        
        return min(max(overall, 0.0), 10.0)