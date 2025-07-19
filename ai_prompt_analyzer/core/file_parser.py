"""File parsing utilities for different formats."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import frontmatter
import markdown
import yaml
from bs4 import BeautifulSoup
from loguru import logger

from ..models import PromptMetadata, AIProvider, PromptType


class FileParser:
    """Parses different file formats to extract AI prompts."""
    
    def __init__(self):
        """Initialize the file parser."""
        self.ai_provider_patterns = {
            AIProvider.OPENAI: [
                r"openai", r"gpt-", r"chatgpt", r"dall-e", r"whisper",
                r"system.*role", r"user.*role", r"assistant.*role"
            ],
            AIProvider.GOOGLE: [
                r"google", r"bard", r"palm", r"gemini", r"vertex",
                r"ai\.google"
            ],
            AIProvider.ANTHROPIC: [
                r"anthropic", r"claude", r"constitutional ai",
                r"assistant:", r"human:"
            ],
            AIProvider.XAI: [
                r"x\.ai", r"xai", r"grok"
            ],
            AIProvider.PERPLEXITY: [
                r"perplexity", r"pplx"
            ],
            AIProvider.CURSOR: [
                r"cursor", r"cursor\.sh"
            ],
            AIProvider.WINDSURF: [
                r"windsurf", r"codeium"
            ],
            AIProvider.DEVIN: [
                r"devin", r"cognition"
            ]
        }
        
        self.prompt_type_patterns = {
            PromptType.SYSTEM: [
                r"system\s*:", r"system\s*prompt", r"system\s*message",
                r"instructions?:", r"role\s*:\s*system"
            ],
            PromptType.USER: [
                r"user\s*:", r"human\s*:", r"input\s*:",
                r"role\s*:\s*user", r"query\s*:"
            ],
            PromptType.ASSISTANT: [
                r"assistant\s*:", r"ai\s*:", r"response\s*:",
                r"role\s*:\s*assistant", r"output\s*:"
            ],
            PromptType.FUNCTION: [
                r"function\s*:", r"tool\s*:", r"api\s*:",
                r"role\s*:\s*function"
            ],
            PromptType.INSTRUCTION: [
                r"instruction\s*:", r"task\s*:", r"objective\s*:",
                r"goal\s*:", r"purpose\s*:"
            ]
        }
    
    def parse_file(self, file_path: Path) -> Tuple[List[str], PromptMetadata]:
        """Parse a file and extract prompts.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (prompt_contents, metadata)
        """
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Create metadata
            metadata = self._create_metadata(file_path, content)
            
            # Parse based on file format
            if file_path.suffix.lower() == '.md':
                prompts = self._parse_markdown(content)
            elif file_path.suffix.lower() == '.json':
                prompts = self._parse_json(content)
            elif file_path.suffix.lower() in ['.yaml', '.yml']:
                prompts = self._parse_yaml(content)
            else:
                # Plain text
                prompts = self._parse_text(content)
            
            return prompts, metadata
            
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return [], self._create_metadata(file_path, "")
    
    def _create_metadata(self, file_path: Path, content: str) -> PromptMetadata:
        """Create metadata for a file.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            File metadata
        """
        return PromptMetadata(
            file_path=str(file_path),
            file_format=file_path.suffix.lower(),
            size_bytes=len(content.encode('utf-8')),
            line_count=len(content.splitlines()),
            word_count=len(content.split()),
            character_count=len(content),
            detected_language="en",  # TODO: Add language detection
            encoding="utf-8"
        )
    
    def _parse_markdown(self, content: str) -> List[str]:
        """Parse markdown content for prompts.
        
        Args:
            content: Markdown content
            
        Returns:
            List of extracted prompts
        """
        prompts = []
        
        try:
            # Parse frontmatter
            post = frontmatter.loads(content)
            
            # Check frontmatter for prompts
            if hasattr(post, 'metadata'):
                prompts.extend(self._extract_prompts_from_dict(post.metadata))
            
            # Parse markdown content
            md = markdown.Markdown(extensions=['fenced_code', 'tables'])
            html = md.convert(post.content)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract code blocks (often contain prompts)
            for code_block in soup.find_all('code'):
                text = code_block.get_text().strip()
                if self._is_likely_prompt(text):
                    prompts.append(text)
            
            # Extract text from headers and paragraphs
            for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
                text = element.get_text().strip()
                if self._is_likely_prompt(text):
                    prompts.append(text)
            
            # Look for conversation format
            prompts.extend(self._extract_conversation_format(post.content))
            
        except Exception as e:
            logger.error(f"Error parsing markdown: {e}")
            # Fallback to text parsing
            prompts.extend(self._parse_text(content))
        
        return [p for p in prompts if p.strip()]
    
    def _parse_json(self, content: str) -> List[str]:
        """Parse JSON content for prompts.
        
        Args:
            content: JSON content
            
        Returns:
            List of extracted prompts
        """
        prompts = []
        
        try:
            data = json.loads(content)
            prompts.extend(self._extract_prompts_from_dict(data))
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
        
        return [p for p in prompts if p.strip()]
    
    def _parse_yaml(self, content: str) -> List[str]:
        """Parse YAML content for prompts.
        
        Args:
            content: YAML content
            
        Returns:
            List of extracted prompts
        """
        prompts = []
        
        try:
            data = yaml.safe_load(content)
            if data:
                prompts.extend(self._extract_prompts_from_dict(data))
                
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML: {e}")
        
        return [p for p in prompts if p.strip()]
    
    def _parse_text(self, content: str) -> List[str]:
        """Parse plain text content for prompts.
        
        Args:
            content: Text content
            
        Returns:
            List of extracted prompts
        """
        prompts = []
        
        # Split by common delimiters
        sections = re.split(r'\n\s*\n|---+|===+|\*\*\*+', content)
        
        for section in sections:
            section = section.strip()
            if self._is_likely_prompt(section):
                prompts.append(section)
        
        # Extract conversation format
        prompts.extend(self._extract_conversation_format(content))
        
        return [p for p in prompts if p.strip()]
    
    def _extract_prompts_from_dict(self, data: Any) -> List[str]:
        """Extract prompts from dictionary/object recursively.
        
        Args:
            data: Dictionary or other data structure
            
        Returns:
            List of extracted prompts
        """
        prompts = []
        
        if isinstance(data, dict):
            # Look for common prompt keys
            prompt_keys = [
                'prompt', 'system', 'user', 'assistant', 'instruction',
                'content', 'message', 'text', 'input', 'output',
                'system_prompt', 'user_prompt', 'system_message'
            ]
            
            for key, value in data.items():
                if key.lower() in prompt_keys and isinstance(value, str):
                    if self._is_likely_prompt(value):
                        prompts.append(value)
                elif isinstance(value, (dict, list)):
                    prompts.extend(self._extract_prompts_from_dict(value))
                    
        elif isinstance(data, list):
            for item in data:
                prompts.extend(self._extract_prompts_from_dict(item))
        
        return prompts
    
    def _extract_conversation_format(self, content: str) -> List[str]:
        """Extract prompts from conversation format.
        
        Args:
            content: Content to search
            
        Returns:
            List of extracted prompts
        """
        prompts = []
        
        # Pattern for role-based conversations
        role_pattern = r'(?:^|\n)\s*(?:System|User|Assistant|Human|AI|Function):\s*(.+?)(?=\n\s*(?:System|User|Assistant|Human|AI|Function):|$)'
        matches = re.findall(role_pattern, content, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            text = match.strip()
            if self._is_likely_prompt(text):
                prompts.append(text)
        
        return prompts
    
    def _is_likely_prompt(self, text: str) -> bool:
        """Check if text is likely a prompt.
        
        Args:
            text: Text to check
            
        Returns:
            True if likely a prompt
        """
        if not text or len(text.strip()) < 10:
            return False
        
        # Check for prompt indicators
        prompt_indicators = [
            r'you are', r'your role', r'act as', r'behave as',
            r'instructions?:', r'task:', r'objective:', r'goal:',
            r'system\s*:', r'user\s*:', r'assistant\s*:',
            r'prompt\s*:', r'command\s*:', r'query\s*:',
            r'please', r'help', r'generate', r'create', r'write',
            r'explain', r'describe', r'analyze', r'summarize'
        ]
        
        text_lower = text.lower()
        for pattern in prompt_indicators:
            if re.search(pattern, text_lower):
                return True
        
        # Check for conversation patterns
        if re.search(r'(human|user|system|assistant):\s*', text_lower):
            return True
        
        # Check length and structure
        if len(text.split()) > 5 and len(text) < 5000:
            return True
        
        return False
    
    def detect_ai_provider(self, content: str) -> AIProvider:
        """Detect AI provider from content.
        
        Args:
            content: Content to analyze
            
        Returns:
            Detected AI provider
        """
        content_lower = content.lower()
        
        for provider, patterns in self.ai_provider_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    return provider
        
        return AIProvider.OTHER
    
    def detect_prompt_type(self, content: str) -> PromptType:
        """Detect prompt type from content.
        
        Args:
            content: Content to analyze
            
        Returns:
            Detected prompt type
        """
        content_lower = content.lower()
        
        for prompt_type, patterns in self.prompt_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    return prompt_type
        
        # Default classification based on content
        if any(keyword in content_lower for keyword in ['you are', 'your role', 'act as']):
            return PromptType.SYSTEM
        elif any(keyword in content_lower for keyword in ['please', 'help me', 'can you']):
            return PromptType.USER
        else:
            return PromptType.INSTRUCTION