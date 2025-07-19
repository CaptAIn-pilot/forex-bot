"""Configuration management for the AI Prompt Analyzer."""

import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Database settings
    database_url: str = Field(default="sqlite:///./ai_prompts.db", env="DATABASE_URL")
    
    # GitHub settings
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    
    # API settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_debug: bool = Field(default=False, env="API_DEBUG")
    
    # Analysis settings
    min_quality_score: float = Field(default=5.0, env="MIN_QUALITY_SCORE")
    max_processing_batch_size: int = Field(default=100, env="MAX_PROCESSING_BATCH_SIZE")
    
    # Model settings
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    classification_model: str = Field(default="microsoft/DialoGPT-medium", env="CLASSIFICATION_MODEL")
    
    # Vector database settings
    vector_db_path: str = Field(default="./chromadb", env="VECTOR_DB_PATH")
    vector_db_collection: str = Field(default="ai_prompts", env="VECTOR_DB_COLLECTION")
    
    # Processing settings
    max_file_size_mb: int = Field(default=10, env="MAX_FILE_SIZE_MB")
    supported_extensions: list = Field(default=[".md", ".txt", ".json", ".yaml", ".yml"])
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()