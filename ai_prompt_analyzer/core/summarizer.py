"""Summarization engine for multi-level analysis reports."""

from typing import Dict, List, Counter
from datetime import datetime
import statistics

from ..models import AnalysisResult, Summary, SummaryLevel, AIProvider


class Summarizer:
    """Generates multi-level summaries with actionable insights."""
    
    def __init__(self):
        """Initialize the summarizer."""
        pass
    
    def generate_summary(self, results: List[AnalysisResult], 
                        level: SummaryLevel) -> Summary:
        """Generate a summary at the specified level.
        
        Args:
            results: Analysis results to summarize
            level: Summary detail level
            
        Returns:
            Generated summary
        """
        if level == SummaryLevel.EXECUTIVE:
            return self._generate_executive_summary(results)
        elif level == SummaryLevel.TECHNICAL:
            return self._generate_technical_summary(results)
        elif level == SummaryLevel.IMPLEMENTATION:
            return self._generate_implementation_summary(results)
        else:
            raise ValueError(f"Unknown summary level: {level}")
    
    def _generate_executive_summary(self, results: List[AnalysisResult]) -> Summary:
        """Generate executive-level summary.
        
        Args:
            results: Analysis results
            
        Returns:
            Executive summary
        """
        total_prompts = len(results)
        
        if not results:
            return Summary(
                level=SummaryLevel.EXECUTIVE,
                total_prompts=0,
                filtered_prompts=0,
                average_quality=0.0,
                top_categories=[],
                top_techniques=[],
                key_insights=["No prompts analyzed"],
                recommendations=["Ensure repository contains valid prompt files"],
                provider_distribution={}
            )
        
        # Calculate metrics
        avg_quality = statistics.mean(r.quality_metrics.overall_score for r in results)
        
        # Top categories
        all_categories = [cat for r in results for cat in r.categories]
        top_categories = [cat for cat, _ in Counter(all_categories).most_common(5)]
        
        # Top techniques
        all_techniques = [tech for r in results for tech in r.techniques]
        top_techniques = [tech for tech, _ in Counter(all_techniques).most_common(5)]
        
        # Provider distribution
        providers = [r.ai_provider.value for r in results]
        provider_dist = dict(Counter(providers))
        
        # Key insights
        insights = self._generate_executive_insights(results, avg_quality)
        
        # Recommendations
        recommendations = self._generate_executive_recommendations(results, avg_quality)
        
        return Summary(
            level=SummaryLevel.EXECUTIVE,
            total_prompts=total_prompts,
            filtered_prompts=total_prompts,  # After filtering
            average_quality=avg_quality,
            top_categories=top_categories,
            top_techniques=top_techniques,
            key_insights=insights,
            recommendations=recommendations,
            provider_distribution=provider_dist
        )
    
    def _generate_technical_summary(self, results: List[AnalysisResult]) -> Summary:
        """Generate technical-level summary.
        
        Args:
            results: Analysis results
            
        Returns:
            Technical summary
        """
        if not results:
            return Summary(
                level=SummaryLevel.TECHNICAL,
                total_prompts=0,
                filtered_prompts=0,
                average_quality=0.0,
                top_categories=[],
                top_techniques=[],
                key_insights=[],
                recommendations=[],
                provider_distribution={}
            )
        
        total_prompts = len(results)
        avg_quality = statistics.mean(r.quality_metrics.overall_score for r in results)
        
        # Detailed analysis
        all_categories = [cat for r in results for cat in r.categories]
        top_categories = [cat for cat, _ in Counter(all_categories).most_common(10)]
        
        all_techniques = [tech for r in results for tech in r.techniques]
        top_techniques = [tech for tech, _ in Counter(all_techniques).most_common(10)]
        
        provider_dist = dict(Counter(r.ai_provider.value for r in results))
        
        # Technical insights
        insights = self._generate_technical_insights(results, avg_quality)
        
        # Technical recommendations
        recommendations = self._generate_technical_recommendations(results)
        
        return Summary(
            level=SummaryLevel.TECHNICAL,
            total_prompts=total_prompts,
            filtered_prompts=total_prompts,
            average_quality=avg_quality,
            top_categories=top_categories,
            top_techniques=top_techniques,
            key_insights=insights,
            recommendations=recommendations,
            provider_distribution=provider_dist
        )
    
    def _generate_implementation_summary(self, results: List[AnalysisResult]) -> Summary:
        """Generate implementation-level summary.
        
        Args:
            results: Analysis results
            
        Returns:
            Implementation summary
        """
        if not results:
            return Summary(
                level=SummaryLevel.IMPLEMENTATION,
                total_prompts=0,
                filtered_prompts=0,
                average_quality=0.0,
                top_categories=[],
                top_techniques=[],
                key_insights=[],
                recommendations=[],
                provider_distribution={}
            )
        
        total_prompts = len(results)
        avg_quality = statistics.mean(r.quality_metrics.overall_score for r in results)
        
        # Focus on actionable patterns
        all_categories = [cat for r in results for cat in r.categories]
        top_categories = [cat for cat, _ in Counter(all_categories).most_common(8)]
        
        all_techniques = [tech for r in results for tech in r.techniques]
        top_techniques = [tech for tech, _ in Counter(all_techniques).most_common(15)]
        
        provider_dist = dict(Counter(r.ai_provider.value for r in results))
        
        # Implementation insights
        insights = self._generate_implementation_insights(results)
        
        # Implementation recommendations
        recommendations = self._generate_implementation_recommendations(results)
        
        return Summary(
            level=SummaryLevel.IMPLEMENTATION,
            total_prompts=total_prompts,
            filtered_prompts=total_prompts,
            average_quality=avg_quality,
            top_categories=top_categories,
            top_techniques=top_techniques,
            key_insights=insights,
            recommendations=recommendations,
            provider_distribution=provider_dist
        )
    
    def _generate_executive_insights(self, results: List[AnalysisResult], 
                                   avg_quality: float) -> List[str]:
        """Generate executive-level insights.
        
        Args:
            results: Analysis results
            avg_quality: Average quality score
            
        Returns:
            List of insights
        """
        insights = []
        
        # Quality assessment
        if avg_quality >= 8.0:
            insights.append("Excellent overall prompt quality detected")
        elif avg_quality >= 6.0:
            insights.append("Good prompt quality with room for optimization")
        elif avg_quality >= 4.0:
            insights.append("Moderate prompt quality - significant improvement opportunities")
        else:
            insights.append("Low prompt quality - major optimization needed")
        
        # Safety assessment
        safety_flagged = sum(1 for r in results if r.safety_flags)
        if safety_flagged > 0:
            safety_rate = safety_flagged / len(results)
            if safety_rate > 0.1:
                insights.append(f"Safety concerns detected in {safety_rate:.1%} of prompts")
            else:
                insights.append("Minimal safety concerns detected")
        else:
            insights.append("No significant safety concerns identified")
        
        # Provider insights
        providers = Counter(r.ai_provider.value for r in results)
        if len(providers) > 3:
            insights.append("Diverse AI provider representation found")
        elif len(providers) == 1:
            main_provider = list(providers.keys())[0]
            insights.append(f"Prompts primarily from {main_provider}")
        
        # Category insights
        categories = [cat for r in results for cat in r.categories]
        if categories:
            top_category = Counter(categories).most_common(1)[0]
            insights.append(f"Primary focus area: {top_category[0]} ({top_category[1]} prompts)")
        
        return insights
    
    def _generate_executive_recommendations(self, results: List[AnalysisResult], 
                                          avg_quality: float) -> List[str]:
        """Generate executive-level recommendations.
        
        Args:
            results: Analysis results
            avg_quality: Average quality score
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Quality improvement
        if avg_quality < 7.0:
            recommendations.append("Implement prompt engineering best practices training")
            recommendations.append("Establish quality review process for new prompts")
        
        # Safety recommendations
        safety_flagged = sum(1 for r in results if r.safety_flags)
        if safety_flagged > 0:
            recommendations.append("Implement automated safety screening for all prompts")
            recommendations.append("Establish clear content guidelines and review processes")
        
        # Standardization
        techniques_used = set(tech for r in results for tech in r.techniques)
        if len(techniques_used) < 5:
            recommendations.append("Expand prompt engineering technique repertoire")
        
        # ROI focus
        high_quality = sum(1 for r in results if r.quality_metrics.overall_score >= 8.0)
        if high_quality > 0:
            high_quality_rate = high_quality / len(results)
            recommendations.append(f"Prioritize deployment of {high_quality_rate:.1%} high-quality prompts")
        
        return recommendations
    
    def _generate_technical_insights(self, results: List[AnalysisResult], 
                                   avg_quality: float) -> List[str]:
        """Generate technical-level insights.
        
        Args:
            results: Analysis results
            avg_quality: Average quality score
            
        Returns:
            List of technical insights
        """
        insights = []
        
        # Quality distribution analysis
        quality_scores = [r.quality_metrics.overall_score for r in results]
        quality_std = statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0
        
        insights.append(f"Quality score distribution: μ={avg_quality:.2f}, σ={quality_std:.2f}")
        
        # Technique analysis
        techniques = [tech for r in results for tech in r.techniques]
        technique_counts = Counter(techniques)
        
        if technique_counts:
            top_technique = technique_counts.most_common(1)[0]
            insights.append(f"Most effective technique: {top_technique[0]} (used in {top_technique[1]} prompts)")
        
        # Pattern analysis
        patterns = [pattern for r in results for pattern in r.extracted_patterns]
        if patterns:
            pattern_counts = Counter(patterns)
            top_pattern = pattern_counts.most_common(1)[0]
            insights.append(f"Dominant pattern: {top_pattern[0]} (found in {top_pattern[1]} prompts)")
        
        # Length analysis
        word_counts = [r.metadata.word_count for r in results]
        avg_length = statistics.mean(word_counts)
        insights.append(f"Average prompt length: {avg_length:.0f} words")
        
        # Provider effectiveness
        provider_quality = {}
        for result in results:
            provider = result.ai_provider.value
            if provider not in provider_quality:
                provider_quality[provider] = []
            provider_quality[provider].append(result.quality_metrics.overall_score)
        
        for provider, scores in provider_quality.items():
            avg_score = statistics.mean(scores)
            insights.append(f"{provider} average quality: {avg_score:.2f}")
        
        return insights
    
    def _generate_technical_recommendations(self, results: List[AnalysisResult]) -> List[str]:
        """Generate technical-level recommendations.
        
        Args:
            results: Analysis results
            
        Returns:
            List of technical recommendations
        """
        recommendations = []
        
        # Technique optimization
        techniques = [tech for r in results for tech in r.techniques]
        technique_counts = Counter(techniques)
        
        underused_techniques = [
            'chain_of_thought', 'few_shot_learning', 'role_playing',
            'constraint_specification', 'output_formatting'
        ]
        
        missing_techniques = [t for t in underused_techniques if t not in technique_counts]
        if missing_techniques:
            recommendations.append(f"Consider implementing: {', '.join(missing_techniques[:3])}")
        
        # Quality optimization
        low_quality = [r for r in results if r.quality_metrics.overall_score < 6.0]
        if low_quality:
            clarity_issues = [r for r in low_quality if r.quality_metrics.clarity_score < 5.0]
            if clarity_issues:
                recommendations.append("Focus on improving prompt clarity and specificity")
            
            effectiveness_issues = [r for r in low_quality if r.quality_metrics.effectiveness_score < 5.0]
            if effectiveness_issues:
                recommendations.append("Implement structured prompt templates for consistency")
        
        # Pattern optimization
        patterns = [pattern for r in results for pattern in r.extracted_patterns]
        if 'template_structure' not in patterns:
            recommendations.append("Implement template-based prompt structures")
        
        # Safety optimization
        safety_issues = [r for r in results if r.safety_flags]
        if safety_issues:
            recommendations.append("Implement automated content safety validation")
        
        return recommendations
    
    def _generate_implementation_insights(self, results: List[AnalysisResult]) -> List[str]:
        """Generate implementation-level insights.
        
        Args:
            results: Analysis results
            
        Returns:
            List of implementation insights
        """
        insights = []
        
        # Ready-to-use prompts
        high_quality = [r for r in results if r.quality_metrics.overall_score >= 8.0]
        insights.append(f"{len(high_quality)} prompts ready for immediate deployment")
        
        # Category-specific insights
        categories = [cat for r in results for cat in r.categories]
        category_counts = Counter(categories)
        
        for category, count in category_counts.most_common(3):
            avg_quality = statistics.mean(
                r.quality_metrics.overall_score for r in results 
                if category in r.categories
            )
            insights.append(f"{category} category: {count} prompts, avg quality {avg_quality:.1f}")
        
        # Technique effectiveness
        technique_quality = {}
        for result in results:
            for technique in result.techniques:
                if technique not in technique_quality:
                    technique_quality[technique] = []
                technique_quality[technique].append(result.quality_metrics.overall_score)
        
        for technique, scores in technique_quality.items():
            if len(scores) >= 3:  # Only report on techniques with sufficient data
                avg_score = statistics.mean(scores)
                insights.append(f"{technique}: avg quality {avg_score:.1f} ({len(scores)} samples)")
        
        return insights
    
    def _generate_implementation_recommendations(self, results: List[AnalysisResult]) -> List[str]:
        """Generate implementation-level recommendations.
        
        Args:
            results: Analysis results
            
        Returns:
            List of implementation recommendations
        """
        recommendations = []
        
        # Deployment recommendations
        high_quality = [r for r in results if r.quality_metrics.overall_score >= 8.0]
        if high_quality:
            recommendations.append("Deploy high-quality prompts immediately for maximum impact")
            
            # Category-specific deployment
            categories = [cat for r in high_quality for cat in r.categories]
            if categories:
                top_category = Counter(categories).most_common(1)[0][0]
                recommendations.append(f"Prioritize {top_category} prompts for quick wins")
        
        # Optimization recommendations
        medium_quality = [r for r in results 
                         if 5.0 <= r.quality_metrics.overall_score < 8.0]
        if medium_quality:
            recommendations.append("Optimize medium-quality prompts using best practice templates")
        
        # Template creation
        best_prompts = sorted(results, key=lambda x: x.quality_metrics.overall_score, reverse=True)[:5]
        if best_prompts:
            techniques = set(tech for r in best_prompts for tech in r.techniques)
            recommendations.append(f"Create templates based on top techniques: {', '.join(list(techniques)[:3])}")
        
        # A/B testing recommendations
        similar_prompts = {}
        for result in results:
            for category in result.categories:
                if category not in similar_prompts:
                    similar_prompts[category] = []
                similar_prompts[category].append(result)
        
        for category, prompts in similar_prompts.items():
            if len(prompts) >= 3:
                recommendations.append(f"A/B test {category} prompts to identify best performers")
        
        # Monitoring recommendations
        recommendations.append("Implement performance tracking for deployed prompts")
        recommendations.append("Set up feedback loops to continuously improve prompt quality")
        
        return recommendations