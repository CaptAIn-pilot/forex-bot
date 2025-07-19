"""GitHub repository monitoring and cloning functionality."""

import asyncio
import hashlib
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, AsyncGenerator, Tuple
from urllib.parse import urlparse

import aiohttp
import git
from loguru import logger

from ..models import RepositoryInfo, ProcessingStatus
from .config import settings


class RepositoryMonitor:
    """Monitors GitHub repositories for AI prompt files."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize the repository monitor.
        
        Args:
            cache_dir: Directory to cache cloned repositories
        """
        self.cache_dir = Path(cache_dir or tempfile.gettempdir()) / "ai_prompt_analyzer"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        headers = {}
        if settings.github_token:
            headers["Authorization"] = f"token {settings.github_token}"
        
        self.session = aiohttp.ClientSession(headers=headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _get_repo_cache_path(self, repo_url: str) -> Path:
        """Get the cache path for a repository.
        
        Args:
            repo_url: Repository URL
            
        Returns:
            Path to cache directory for this repository
        """
        repo_hash = hashlib.md5(repo_url.encode()).hexdigest()[:8]
        parsed = urlparse(repo_url)
        repo_name = parsed.path.strip('/').replace('/', '_')
        return self.cache_dir / f"{repo_name}_{repo_hash}"
    
    async def clone_repository(self, repo_url: str, force_refresh: bool = False) -> Path:
        """Clone or update a repository.
        
        Args:
            repo_url: GitHub repository URL
            force_refresh: Force refresh even if already cached
            
        Returns:
            Path to the cloned repository
        """
        cache_path = self._get_repo_cache_path(repo_url)
        
        if force_refresh and cache_path.exists():
            import shutil
            shutil.rmtree(cache_path)
        
        if cache_path.exists():
            try:
                # Update existing repository
                repo = git.Repo(cache_path)
                repo.remotes.origin.pull()
                logger.info(f"Updated repository: {repo_url}")
            except Exception as e:
                logger.warning(f"Failed to update repository {repo_url}: {e}")
                # Fall back to re-cloning
                import shutil
                shutil.rmtree(cache_path)
                repo = git.Repo.clone_from(repo_url, cache_path)
                logger.info(f"Re-cloned repository: {repo_url}")
        else:
            # Clone new repository
            repo = git.Repo.clone_from(repo_url, cache_path)
            logger.info(f"Cloned repository: {repo_url}")
        
        return cache_path
    
    async def get_repository_info(self, repo_url: str) -> RepositoryInfo:
        """Get repository information.
        
        Args:
            repo_url: Repository URL
            
        Returns:
            Repository information
        """
        cache_path = self._get_repo_cache_path(repo_url)
        
        if not cache_path.exists():
            await self.clone_repository(repo_url)
        
        repo = git.Repo(cache_path)
        
        # Count files
        total_files = 0
        processed_files = 0
        
        for file_path in cache_path.rglob("*"):
            if file_path.is_file():
                total_files += 1
                if file_path.suffix.lower() in settings.supported_extensions:
                    processed_files += 1
        
        return RepositoryInfo(
            url=repo_url,
            name=repo_url.split('/')[-1],
            last_updated=datetime.fromtimestamp(repo.head.commit.committed_date),
            total_files=total_files,
            processed_files=processed_files,
            last_commit_sha=repo.head.commit.hexsha
        )
    
    async def scan_repository_files(self, repo_url: str) -> AsyncGenerator[Tuple[Path, str], None]:
        """Scan repository for supported files.
        
        Args:
            repo_url: Repository URL
            
        Yields:
            Tuples of (file_path, relative_path)
        """
        cache_path = await self.clone_repository(repo_url)
        
        for file_path in cache_path.rglob("*"):
            if not file_path.is_file():
                continue
                
            if file_path.suffix.lower() not in settings.supported_extensions:
                continue
                
            # Skip files that are too large
            if file_path.stat().st_size > settings.max_file_size_mb * 1024 * 1024:
                logger.warning(f"Skipping large file: {file_path}")
                continue
                
            relative_path = str(file_path.relative_to(cache_path))
            yield file_path, relative_path
    
    async def check_for_updates(self, repo_url: str) -> bool:
        """Check if repository has updates.
        
        Args:
            repo_url: Repository URL
            
        Returns:
            True if updates are available
        """
        if not self.session:
            raise RuntimeError("Monitor not initialized. Use async context manager.")
        
        try:
            # Parse GitHub API URL
            parsed = urlparse(repo_url)
            if "github.com" not in parsed.netloc:
                return False
                
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) < 2:
                return False
                
            owner, repo = path_parts[0], path_parts[1]
            api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
            
            async with self.session.get(api_url, params={"per_page": 1}) as response:
                if response.status != 200:
                    logger.error(f"Failed to check updates for {repo_url}: {response.status}")
                    return False
                
                commits = await response.json()
                if not commits:
                    return False
                
                latest_sha = commits[0]["sha"]
                
                # Compare with cached version
                cache_path = self._get_repo_cache_path(repo_url)
                if cache_path.exists():
                    repo = git.Repo(cache_path)
                    current_sha = repo.head.commit.hexsha
                    return latest_sha != current_sha
                
                return True  # No cache, so updates available
                
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return False
    
    async def monitor_repository(self, repo_url: str, check_interval: int = 300) -> AsyncGenerator[bool, None]:
        """Monitor repository for updates.
        
        Args:
            repo_url: Repository URL
            check_interval: Check interval in seconds
            
        Yields:
            True when updates are detected
        """
        while True:
            try:
                has_updates = await self.check_for_updates(repo_url)
                if has_updates:
                    yield True
                    
                await asyncio.sleep(check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring repository: {e}")
                await asyncio.sleep(check_interval)