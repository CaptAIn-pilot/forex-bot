"""Main analyzer class that orchestrates the analysis pipeline."""

import asyncio
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, AsyncGenerator, Tuple
from uuid import uuid4

from loguru import logger

from ..models import (
    AnalysisResult, FilterCriteria, Summary, SummaryLevel,
    PromptMetadata, QualityMetrics, AIProvider, PromptType,
    ProcessingJob, ProcessingStatus, RepositoryInfo
)
from .repository_monitor import RepositoryMonitor
from .file_parser import FileParser
from .semantic_analyzer import SemanticAnalyzer
from .quality_scorer import QualityScorer
from .filter_engine import FilterEngine
from .summarizer import Summarizer


class PromptAnalyzer:
    """Main analyzer class that orchestrates the entire analysis pipeline."""
    
    def __init__(self):
        """Initialize the prompt analyzer."""
        self.repository_monitor = RepositoryMonitor()
        self.file_parser = FileParser()
        self.semantic_analyzer = SemanticAnalyzer()
        self.quality_scorer = QualityScorer()
        self.filter_engine = FilterEngine()
        self.summarizer = Summarizer()
        
        # In-memory storage for processed results (in production, use database)
        self.processed_results: Dict[str, List[AnalysisResult]] = {}
        self.processing_jobs: Dict[str, ProcessingJob] = {}
    
    async def analyze_repository(self, repo_url: str, 
                               filter_criteria: Optional[FilterCriteria] = None,
                               force_refresh: bool = False) -> List[AnalysisResult]:
        """Analyze all prompts in a repository.
        
        Args:
            repo_url: Repository URL to analyze
            filter_criteria: Optional filter criteria
            force_refresh: Force refresh of cached data
            
        Returns:
            List of analysis results
        """
        logger.info(f"Starting analysis of repository: {repo_url}")
        
        # Create processing job
        job_id = str(uuid4())
        job = ProcessingJob(
            id=job_id,
            repository_url=repo_url,
            status=ProcessingStatus.PENDING
        )
        self.processing_jobs[job_id] = job
        
        try:
            # Check if already processed and not forcing refresh
            cache_key = self._get_cache_key(repo_url)
            if not force_refresh and cache_key in self.processed_results:
                logger.info("Using cached results")
                job.status = ProcessingStatus.COMPLETED
                job.results_available = True
                results = self.processed_results[cache_key]
            else:
                # Process repository
                results = await self._process_repository(repo_url, job)
                self.processed_results[cache_key] = results
                
                job.status = ProcessingStatus.COMPLETED
                job.results_available = True
                job.processed_files = len(results)
            
            # Apply filters if provided
            if filter_criteria:
                results = self.filter_engine.filter_prompts(results, filter_criteria)
            
            logger.info(f"Analysis completed: {len(results)} prompts processed")
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing repository: {e}")
            job.status = ProcessingStatus.FAILED
            job.error_message = str(e)
            raise
        finally:
            job.updated_at = datetime.utcnow()
    
    async def _process_repository(self, repo_url: str, 
                                job: ProcessingJob) -> List[AnalysisResult]:
        """Process all files in a repository.
        
        Args:
            repo_url: Repository URL
            job: Processing job for progress tracking
            
        Returns:
            List of analysis results
        """
        results = []
        
        job.status = ProcessingStatus.PROCESSING
        
        async with self.repository_monitor:
            # Get repository files
            file_count = 0
            async for file_path, relative_path in self.repository_monitor.scan_repository_files(repo_url):
                file_count += 1
            
            job.total_files = file_count
            job.progress = 0.0
            
            # Process each file
            processed_count = 0
            async for file_path, relative_path in self.repository_monitor.scan_repository_files(repo_url):
                try:
                    file_results = await self._process_file(file_path, relative_path)
                    results.extend(file_results)
                    
                    processed_count += 1
                    job.processed_files = processed_count
                    job.progress = processed_count / max(job.total_files, 1) * 100
                    job.updated_at = datetime.utcnow()
                    
                    logger.debug(f"Processed file {processed_count}/{job.total_files}: {relative_path}")
                    
                except Exception as e:
                    logger.error(f"Error processing file {relative_path}: {e}")
                    continue
        
        return results
    
    async def _process_file(self, file_path: Path, relative_path: str) -> List[AnalysisResult]:
        """Process a single file.
        
        Args:
            file_path: Path to the file
            relative_path: Relative path from repository root
            
        Returns:
            List of analysis results for prompts in the file
        """
        # Parse file content
        prompts, metadata = self.file_parser.parse_file(file_path)
        
        if not prompts:
            return []
        
        results = []
        
        for i, prompt_content in enumerate(prompts):
            try:
                # Generate unique ID for this prompt
                prompt_id = self._generate_prompt_id(prompt_content, relative_path, i)
                
                # Detect AI provider and prompt type
                ai_provider = self.file_parser.detect_ai_provider(prompt_content)
                prompt_type = self.file_parser.detect_prompt_type(prompt_content)
                
                # Semantic analysis
                semantic_analysis = await self.semantic_analyzer.analyze_semantic_content(prompt_content)
                
                # Quality scoring
                quality_metrics = self.quality_scorer.score_prompt(
                    prompt_content, 
                    prompt_type, 
                    ai_provider,
                    semantic_analysis.get('techniques', [])
                )
                
                # Create analysis result
                result = AnalysisResult(
                    id=prompt_id,
                    content=prompt_content,
                    prompt_type=prompt_type,
                    ai_provider=ai_provider,
                    categories=semantic_analysis.get('categories', []),
                    techniques=semantic_analysis.get('techniques', []),
                    quality_metrics=quality_metrics,
                    metadata=metadata,
                    extracted_patterns=semantic_analysis.get('patterns', []),
                    safety_flags=[]
                )
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing prompt {i} in {relative_path}: {e}")
                continue
        
        return results
    
    def _generate_prompt_id(self, content: str, file_path: str, index: int) -> str:
        """Generate a unique ID for a prompt.
        
        Args:
            content: Prompt content
            file_path: File path
            index: Prompt index in file
            
        Returns:
            Unique prompt ID
        """
        unique_string = f"{file_path}:{index}:{content[:100]}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    def _get_cache_key(self, repo_url: str) -> str:
        """Get cache key for repository.
        
        Args:
            repo_url: Repository URL
            
        Returns:
            Cache key
        """
        return hashlib.md5(repo_url.encode()).hexdigest()
    
    async def get_repository_info(self, repo_url: str) -> RepositoryInfo:
        """Get repository information.
        
        Args:
            repo_url: Repository URL
            
        Returns:
            Repository information
        """
        async with self.repository_monitor:
            return await self.repository_monitor.get_repository_info(repo_url)
    
    def filter_results(self, results: List[AnalysisResult], 
                      criteria: FilterCriteria) -> List[AnalysisResult]:
        """Filter analysis results.
        
        Args:
            results: Results to filter
            criteria: Filter criteria
            
        Returns:
            Filtered results
        """
        return self.filter_engine.filter_prompts(results, criteria)
    
    def generate_summary(self, results: List[AnalysisResult], 
                        level: SummaryLevel) -> Summary:
        """Generate summary of analysis results.
        
        Args:
            results: Analysis results
            level: Summary level
            
        Returns:
            Generated summary
        """
        return self.summarizer.generate_summary(results, level)
    
    async def cluster_prompts(self, results: List[AnalysisResult], 
                            n_clusters: int = 5) -> Dict[int, List[AnalysisResult]]:
        """Cluster prompts by semantic similarity.
        
        Args:
            results: Analysis results
            n_clusters: Number of clusters
            
        Returns:
            Dictionary mapping cluster IDs to results
        """
        prompt_texts = [r.content for r in results]
        clusters = await self.semantic_analyzer.cluster_prompts(prompt_texts, n_clusters)
        
        # Map indices back to results
        clustered_results = {}
        for cluster_id, indices in clusters.items():
            clustered_results[cluster_id] = [results[i] for i in indices]
        
        return clustered_results
    
    def get_processing_job(self, job_id: str) -> Optional[ProcessingJob]:
        """Get processing job status.
        
        Args:
            job_id: Job ID
            
        Returns:
            Processing job or None if not found
        """
        return self.processing_jobs.get(job_id)
    
    def get_best_prompts(self, results: List[AnalysisResult], 
                        n: int = 10) -> List[AnalysisResult]:
        """Get the best prompts by quality score.
        
        Args:
            results: Analysis results
            n: Number of top prompts to return
            
        Returns:
            Top N prompts by quality
        """
        return sorted(results, 
                     key=lambda x: x.quality_metrics.overall_score, 
                     reverse=True)[:n]
    
    def get_prompts_by_category(self, results: List[AnalysisResult], 
                              category: str) -> List[AnalysisResult]:
        """Get prompts in a specific category.
        
        Args:
            results: Analysis results
            category: Category to filter by
            
        Returns:
            Prompts in the specified category
        """
        return [r for r in results if category in r.categories]
    
    def get_prompts_by_provider(self, results: List[AnalysisResult], 
                              provider: AIProvider) -> List[AnalysisResult]:
        """Get prompts from a specific AI provider.
        
        Args:
            results: Analysis results
            provider: AI provider to filter by
            
        Returns:
            Prompts from the specified provider
        """
        return [r for r in results if r.ai_provider == provider]
    
    def get_prompts_by_technique(self, results: List[AnalysisResult], 
                               technique: str) -> List[AnalysisResult]:
        """Get prompts using a specific technique.
        
        Args:
            results: Analysis results
            technique: Technique to filter by
            
        Returns:
            Prompts using the specified technique
        """
        return [r for r in results if technique in r.techniques]
    
    def export_results(self, results: List[AnalysisResult], 
                      format: str = 'json') -> str:
        """Export analysis results in specified format.
        
        Args:
            results: Results to export
            format: Export format ('json', 'csv', 'markdown')
            
        Returns:
            Exported data as string
        """
        if format.lower() == 'json':
            import json
            return json.dumps([r.dict() for r in results], indent=2, default=str)
        
        elif format.lower() == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            fieldnames = ['id', 'ai_provider', 'prompt_type', 'overall_quality', 
                         'categories', 'techniques', 'content_preview']
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                writer.writerow({
                    'id': result.id,
                    'ai_provider': result.ai_provider.value,
                    'prompt_type': result.prompt_type.value,
                    'overall_quality': result.quality_metrics.overall_score,
                    'categories': ', '.join(result.categories),
                    'techniques': ', '.join(result.techniques),
                    'content_preview': result.content[:100] + '...' if len(result.content) > 100 else result.content
                })
            
            return output.getvalue()
        
        elif format.lower() == 'markdown':
            lines = ['# AI Prompt Analysis Results\n']
            
            for i, result in enumerate(results, 1):
                lines.extend([
                    f"## Prompt {i}\n",
                    f"**ID:** {result.id}",
                    f"**Provider:** {result.ai_provider.value}",
                    f"**Type:** {result.prompt_type.value}",
                    f"**Quality Score:** {result.quality_metrics.overall_score:.1f}/10",
                    f"**Categories:** {', '.join(result.categories)}",
                    f"**Techniques:** {', '.join(result.techniques)}",
                    "",
                    "**Content:**",
                    "```",
                    result.content,
                    "```",
                    ""
                ])
            
            return '\n'.join(lines)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    async def monitor_repository_changes(self, repo_url: str, 
                                       callback=None, 
                                       check_interval: int = 300) -> AsyncGenerator[bool, None]:
        """Monitor repository for changes.
        
        Args:
            repo_url: Repository URL to monitor
            callback: Optional callback function for changes
            check_interval: Check interval in seconds
            
        Yields:
            True when changes are detected
        """
        async with self.repository_monitor:
            async for has_updates in self.repository_monitor.monitor_repository(repo_url, check_interval):
                if callback:
                    await callback(repo_url, has_updates)
                yield has_updates