"""Intelligent filtering system with safety compliance."""

import re
from typing import List, Dict, Set
from datetime import datetime
from loguru import logger

from ..models import (
    AnalysisResult, FilterCriteria, FilterLevel, 
    AIProvider, PromptType, QualityMetrics
)


class FilterEngine:
    """Advanced filtering system for AI prompts with safety compliance."""
    
    def __init__(self):
        """Initialize the filter engine."""
        
        # Harmful patterns - content that should be filtered out
        self.harmful_patterns = [
            # Violence and harm
            r'(?:kill|murder|harm|hurt|violence|attack|weapon)',
            r'(?:suicide|self[-\s]harm|cutting|overdose)',
            r'(?:bomb|explosive|terrorist|assassination)',
            
            # Illegal activities
            r'(?:illegal|criminal|fraud|theft|hacking|piracy)',
            r'(?:drug dealing|money laundering|tax evasion)',
            r'(?:plagiarism|cheating|academic dishonesty)',
            
            # Inappropriate content
            r'(?:sexual|pornographic|explicit|nsfw)',
            r'(?:racist|sexist|homophobic|transphobic)',
            r'(?:hate speech|discrimination|prejudice)',
            
            # Privacy violations
            r'(?:personal information|private data|doxx)',
            r'(?:ssn|social security|credit card|password)',
            r'(?:medical records|confidential)',
            
            # Manipulation and deception
            r'(?:manipulate|deceive|trick|scam|con)',
            r'(?:fake news|misinformation|propaganda)',
            r'(?:impersonate|identity theft)'
        ]
        
        # Bias indicators
        self.bias_patterns = [
            r'(?:all|most|every)\s+(?:men|women|boys|girls)\s+(?:are|should)',
            r'(?:race|ethnicity|religion|nationality)\s+(?:determines|causes)',
            r'stereotype.*about',
            r'(?:inferior|superior).*because.*of.*(?:gender|race|religion)',
            r'(?:naturally|inherently).*(?:better|worse).*(?:gender|race)'
        ]
        
        # Quality indicators for different filter levels
        self.quality_thresholds = {
            FilterLevel.STRICT: {
                'min_overall_score': 7.0,
                'min_safety_score': 9.0,
                'min_clarity_score': 7.0,
                'min_word_count': 20,
                'max_word_count': 1000
            },
            FilterLevel.MODERATE: {
                'min_overall_score': 5.0,
                'min_safety_score': 7.0,
                'min_clarity_score': 5.0,
                'min_word_count': 10,
                'max_word_count': 2000
            },
            FilterLevel.PERMISSIVE: {
                'min_overall_score': 3.0,
                'min_safety_score': 5.0,
                'min_clarity_score': 3.0,
                'min_word_count': 5,
                'max_word_count': 5000
            }
        }
        
        # Domain-specific filters
        self.domain_filters = {
            'coding': {
                'required_keywords': ['code', 'programming', 'function', 'algorithm'],
                'excluded_keywords': ['personal', 'private', 'confidential'],
                'min_technical_score': 5.0
            },
            'creative': {
                'required_keywords': ['creative', 'story', 'imagine', 'design'],
                'excluded_keywords': ['harmful', 'inappropriate', 'offensive'],
                'min_creativity_score': 6.0
            },
            'analysis': {
                'required_keywords': ['analyze', 'evaluate', 'assess', 'examine'],
                'excluded_keywords': ['biased', 'prejudiced', 'discriminatory'],
                'min_analytical_score': 6.0
            },
            'education': {
                'required_keywords': ['learn', 'teach', 'explain', 'educational'],
                'excluded_keywords': ['cheat', 'plagiarize', 'academic dishonesty'],
                'min_educational_value': 7.0
            }
        }
    
    def filter_prompts(self, results: List[AnalysisResult], 
                      criteria: FilterCriteria) -> List[AnalysisResult]:
        """Filter prompts based on criteria.
        
        Args:
            results: List of analysis results
            criteria: Filter criteria
            
        Returns:
            Filtered list of results
        """
        filtered = []
        
        for result in results:
            if self._passes_filter(result, criteria):
                filtered.append(result)
            else:
                logger.debug(f"Filtered out prompt {result.id}")
        
        logger.info(f"Filtered {len(results)} prompts to {len(filtered)}")
        return filtered
    
    def _passes_filter(self, result: AnalysisResult, criteria: FilterCriteria) -> bool:
        """Check if a result passes the filter criteria.
        
        Args:
            result: Analysis result to check
            criteria: Filter criteria
            
        Returns:
            True if result passes all filters
        """
        # Safety check (always applied)
        if not self._passes_safety_filter(result, criteria):
            return False
        
        # Quality thresholds
        if not self._passes_quality_filter(result, criteria):
            return False
        
        # Provider filter
        if criteria.allowed_providers and result.ai_provider not in criteria.allowed_providers:
            return False
        
        # Type filter
        if criteria.allowed_types and result.prompt_type not in criteria.allowed_types:
            return False
        
        # Category filters
        if not self._passes_category_filter(result, criteria):
            return False
        
        # Content length filter
        if not self._passes_length_filter(result, criteria):
            return False
        
        # Domain-specific filters
        if not self._passes_domain_filters(result, criteria):
            return False
        
        return True
    
    def _passes_safety_filter(self, result: AnalysisResult, 
                            criteria: FilterCriteria) -> bool:
        """Check if result passes safety filters.
        
        Args:
            result: Analysis result
            criteria: Filter criteria
            
        Returns:
            True if safe
        """
        content_lower = result.content.lower()
        
        # Check for harmful patterns
        for pattern in self.harmful_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                result.safety_flags.append(f"harmful_content: {pattern}")
                if not criteria.include_safety_flagged:
                    return False
        
        # Check for bias patterns
        for pattern in self.bias_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                result.safety_flags.append(f"potential_bias: {pattern}")
                if criteria.filter_level == FilterLevel.STRICT:
                    return False
        
        # Safety score threshold
        thresholds = self.quality_thresholds[criteria.filter_level]
        if result.quality_metrics.safety_score < thresholds['min_safety_score']:
            result.safety_flags.append("low_safety_score")
            return False
        
        return True
    
    def _passes_quality_filter(self, result: AnalysisResult, 
                             criteria: FilterCriteria) -> bool:
        """Check if result passes quality filters.
        
        Args:
            result: Analysis result
            criteria: Filter criteria
            
        Returns:
            True if quality is sufficient
        """
        metrics = result.quality_metrics
        thresholds = self.quality_thresholds[criteria.filter_level]
        
        # Overall quality score
        if metrics.overall_score < criteria.min_quality_score:
            return False
        
        if metrics.overall_score > criteria.max_quality_score:
            return False
        
        # Individual metric thresholds
        if metrics.overall_score < thresholds['min_overall_score']:
            return False
        
        if metrics.clarity_score < thresholds['min_clarity_score']:
            return False
        
        return True
    
    def _passes_category_filter(self, result: AnalysisResult, 
                              criteria: FilterCriteria) -> bool:
        """Check if result passes category filters.
        
        Args:
            result: Analysis result
            criteria: Filter criteria
            
        Returns:
            True if categories match criteria
        """
        # Required categories
        if criteria.required_categories:
            if not any(cat in result.categories for cat in criteria.required_categories):
                return False
        
        # Excluded categories
        if criteria.excluded_categories:
            if any(cat in result.categories for cat in criteria.excluded_categories):
                return False
        
        return True
    
    def _passes_length_filter(self, result: AnalysisResult, 
                            criteria: FilterCriteria) -> bool:
        """Check if result passes length filters.
        
        Args:
            result: Analysis result
            criteria: Filter criteria
            
        Returns:
            True if length is within bounds
        """
        word_count = result.metadata.word_count
        
        # Basic length criteria
        if word_count < criteria.min_word_count:
            return False
        
        if word_count > criteria.max_word_count:
            return False
        
        # Filter level specific thresholds
        thresholds = self.quality_thresholds[criteria.filter_level]
        
        if word_count < thresholds['min_word_count']:
            return False
        
        if word_count > thresholds['max_word_count']:
            return False
        
        return True
    
    def _passes_domain_filters(self, result: AnalysisResult, 
                             criteria: FilterCriteria) -> bool:
        """Check if result passes domain-specific filters.
        
        Args:
            result: Analysis result
            criteria: Filter criteria
            
        Returns:
            True if domain requirements are met
        """
        content_lower = result.content.lower()
        
        # Apply filters for each category the prompt belongs to
        for category in result.categories:
            if category in self.domain_filters:
                domain_filter = self.domain_filters[category]
                
                # Required keywords check
                required = domain_filter.get('required_keywords', [])
                if required:
                    if not any(keyword in content_lower for keyword in required):
                        return False
                
                # Excluded keywords check
                excluded = domain_filter.get('excluded_keywords', [])
                if any(keyword in content_lower for keyword in excluded):
                    return False
        
        return True
    
    def get_filter_statistics(self, original_results: List[AnalysisResult],
                            filtered_results: List[AnalysisResult]) -> Dict:
        """Get statistics about filtering results.
        
        Args:
            original_results: Original results before filtering
            filtered_results: Results after filtering
            
        Returns:
            Dictionary with filter statistics
        """
        original_count = len(original_results)
        filtered_count = len(filtered_results)
        removed_count = original_count - filtered_count
        
        # Analyze reasons for filtering
        filter_reasons = {}
        
        for result in original_results:
            if result not in filtered_results:
                # Determine why it was filtered
                if result.safety_flags:
                    for flag in result.safety_flags:
                        filter_reasons[flag] = filter_reasons.get(flag, 0) + 1
                
                if result.quality_metrics.overall_score < 5.0:
                    filter_reasons['low_quality'] = filter_reasons.get('low_quality', 0) + 1
        
        # Provider distribution
        provider_dist_original = {}
        provider_dist_filtered = {}
        
        for result in original_results:
            provider = result.ai_provider.value
            provider_dist_original[provider] = provider_dist_original.get(provider, 0) + 1
        
        for result in filtered_results:
            provider = result.ai_provider.value
            provider_dist_filtered[provider] = provider_dist_filtered.get(provider, 0) + 1
        
        # Quality distribution
        quality_ranges = {'0-3': 0, '3-5': 0, '5-7': 0, '7-10': 0}
        
        for result in filtered_results:
            score = result.quality_metrics.overall_score
            if score < 3:
                quality_ranges['0-3'] += 1
            elif score < 5:
                quality_ranges['3-5'] += 1
            elif score < 7:
                quality_ranges['5-7'] += 1
            else:
                quality_ranges['7-10'] += 1
        
        return {
            'original_count': original_count,
            'filtered_count': filtered_count,
            'removed_count': removed_count,
            'removal_rate': removed_count / max(original_count, 1),
            'filter_reasons': filter_reasons,
            'provider_distribution': {
                'original': provider_dist_original,
                'filtered': provider_dist_filtered
            },
            'quality_distribution': quality_ranges,
            'avg_quality_original': np.mean([r.quality_metrics.overall_score for r in original_results]) if original_results else 0,
            'avg_quality_filtered': np.mean([r.quality_metrics.overall_score for r in filtered_results]) if filtered_results else 0
        }
    
    def create_custom_filter_profile(self, name: str, 
                                   requirements: Dict) -> FilterCriteria:
        """Create a custom filter profile for specific use cases.
        
        Args:
            name: Profile name
            requirements: Requirements dictionary
            
        Returns:
            Custom filter criteria
        """
        # Predefined profiles
        profiles = {
            'agent_optimization': FilterCriteria(
                min_quality_score=7.0,
                allowed_types=[PromptType.SYSTEM, PromptType.INSTRUCTION],
                required_categories=['agent', 'optimization', 'performance'],
                filter_level=FilterLevel.STRICT,
                min_word_count=50,
                max_word_count=500
            ),
            'coding_assistance': FilterCriteria(
                min_quality_score=6.0,
                allowed_providers=[AIProvider.OPENAI, AIProvider.ANTHROPIC, AIProvider.CURSOR],
                required_categories=['coding', 'programming'],
                excluded_categories=['harmful', 'inappropriate'],
                filter_level=FilterLevel.MODERATE,
                min_word_count=20,
                max_word_count=1000
            ),
            'creative_writing': FilterCriteria(
                min_quality_score=5.0,
                required_categories=['creative', 'writing'],
                excluded_categories=['harmful', 'inappropriate', 'plagiarism'],
                filter_level=FilterLevel.MODERATE,
                min_word_count=30,
                max_word_count=2000
            ),
            'educational': FilterCriteria(
                min_quality_score=8.0,
                required_categories=['education', 'learning'],
                excluded_categories=['cheating', 'academic_dishonesty'],
                filter_level=FilterLevel.STRICT,
                min_word_count=40,
                max_word_count=800
            ),
            'research_analysis': FilterCriteria(
                min_quality_score=7.5,
                required_categories=['analysis', 'research'],
                excluded_categories=['biased', 'unethical'],
                filter_level=FilterLevel.STRICT,
                min_word_count=60,
                max_word_count=1500
            )
        }
        
        if name in profiles:
            # Merge with custom requirements
            profile = profiles[name]
            for key, value in requirements.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            return profile
        
        # Create new profile from requirements
        return FilterCriteria(**requirements)
    
    def validate_filter_criteria(self, criteria: FilterCriteria) -> List[str]:
        """Validate filter criteria and return any issues.
        
        Args:
            criteria: Filter criteria to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Quality score validation
        if criteria.min_quality_score < 0 or criteria.min_quality_score > 10:
            issues.append("min_quality_score must be between 0 and 10")
        
        if criteria.max_quality_score < 0 or criteria.max_quality_score > 10:
            issues.append("max_quality_score must be between 0 and 10")
        
        if criteria.min_quality_score > criteria.max_quality_score:
            issues.append("min_quality_score cannot be greater than max_quality_score")
        
        # Word count validation
        if criteria.min_word_count < 0:
            issues.append("min_word_count cannot be negative")
        
        if criteria.max_word_count < criteria.min_word_count:
            issues.append("max_word_count cannot be less than min_word_count")
        
        # Category validation
        if criteria.required_categories and criteria.excluded_categories:
            overlap = set(criteria.required_categories) & set(criteria.excluded_categories)
            if overlap:
                issues.append(f"Categories cannot be both required and excluded: {overlap}")
        
        return issues