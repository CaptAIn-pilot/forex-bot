"""Data models for the AI Prompt Analyzer."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class PromptType(str, Enum):
    """Types of AI prompts."""
    SYSTEM = "system"
    USER = "user" 
    ASSISTANT = "assistant"
    FUNCTION = "function"
    INSTRUCTION = "instruction"


class AIProvider(str, Enum):
    """AI service providers."""
    OPENAI = "openai"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    XAI = "xai"
    PERPLEXITY = "perplexity"
    CURSOR = "cursor"
    WINDSURF = "windsurf"
    DEVIN = "devin"
    OTHER = "other"


class FilterLevel(str, Enum):
    """Filter strictness levels."""
    STRICT = "strict"
    MODERATE = "moderate"
    PERMISSIVE = "permissive"


class QualityMetrics(BaseModel):
    """Quality metrics for a prompt."""
    clarity_score: float = Field(ge=0.0, le=10.0, description="Clarity of instructions")
    effectiveness_score: float = Field(ge=0.0, le=10.0, description="Predicted effectiveness")
    specificity_score: float = Field(ge=0.0, le=10.0, description="Specificity of requirements")
    completeness_score: float = Field(ge=0.0, le=10.0, description="Completeness of instructions")
    safety_score: float = Field(ge=0.0, le=10.0, description="Safety assessment")
    overall_score: float = Field(ge=0.0, le=10.0, description="Overall quality score")


class PromptMetadata(BaseModel):
    """Metadata for a prompt."""
    file_path: str
    file_format: str
    size_bytes: int
    line_count: int
    word_count: int
    character_count: int
    detected_language: str = "en"
    encoding: str = "utf-8"
    last_modified: Optional[datetime] = None


class AnalysisResult(BaseModel):
    """Result of prompt analysis."""
    id: str
    content: str
    prompt_type: PromptType
    ai_provider: AIProvider
    categories: List[str] = []
    techniques: List[str] = []
    quality_metrics: QualityMetrics
    metadata: PromptMetadata
    extracted_patterns: List[str] = []
    safety_flags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    
class FilterCriteria(BaseModel):
    """Criteria for filtering prompts."""
    min_quality_score: float = 5.0
    max_quality_score: float = 10.0
    allowed_providers: List[AIProvider] = []
    allowed_types: List[PromptType] = []
    required_categories: List[str] = []
    excluded_categories: List[str] = []
    filter_level: FilterLevel = FilterLevel.MODERATE
    include_safety_flagged: bool = False
    min_word_count: int = 10
    max_word_count: int = 10000


class SummaryLevel(str, Enum):
    """Summary detail levels."""
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    IMPLEMENTATION = "implementation"


class Summary(BaseModel):
    """Summary of analyzed prompts."""
    level: SummaryLevel
    total_prompts: int
    filtered_prompts: int
    average_quality: float
    top_categories: List[str]
    top_techniques: List[str]
    key_insights: List[str]
    recommendations: List[str]
    provider_distribution: Dict[str, int]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExportFormat(str, Enum):
    """Export format options."""
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    YAML = "yaml"


class RepositoryInfo(BaseModel):
    """Information about a monitored repository."""
    url: str
    name: str
    last_updated: datetime
    total_files: int
    processed_files: int
    last_commit_sha: Optional[str] = None
    
    
class ProcessingStatus(str, Enum):
    """Processing status for async operations."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    

class ProcessingJob(BaseModel):
    """Processing job status."""
    id: str
    repository_url: str
    status: ProcessingStatus
    progress: float = 0.0
    total_files: int = 0
    processed_files: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    results_available: bool = False