# AI Prompt Analyzer Bot

A sophisticated bot system that processes and analyzes AI system prompts with advanced filtering, analysis, and optimization capabilities.

## Features

- **Repository Processing**: Auto-clone and monitor CL4R1T4S repository for AI system prompts
- **Advanced Analysis**: Semantic analysis, pattern recognition, quality scoring
- **Intelligent Filtering**: Multi-level filtering with safety compliance
- **Summarization Engine**: Multi-level summaries with actionable insights
- **REST API**: FastAPI-based API for programmatic access
- **Web Dashboard**: Interactive user interface
- **CLI Tool**: Command-line interface for developers

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

#### CLI Tool
```bash
# Analyze prompts from CL4R1T4S repository
python -m ai_prompt_analyzer analyze --repo-url https://github.com/elder-plinius/CL4R1T4S

# Start web server
python -m ai_prompt_analyzer serve --host 0.0.0.0 --port 8000
```

#### Python API
```python
from ai_prompt_analyzer import PromptAnalyzer

analyzer = PromptAnalyzer()
results = analyzer.analyze_repository("https://github.com/elder-plinius/CL4R1T4S")
print(f"Analyzed {len(results)} prompts")
```

## Architecture

The system follows a modular architecture:

```
GitHub Monitor → File Parser → Content Extractor → Semantic Analyzer → 
Quality Scorer → Filter Engine → Categorizer → Summarizer → Export Manager
```

## Configuration

Create a `.env` file with your configuration:

```env
# Database settings
DATABASE_URL=sqlite:///./ai_prompts.db

# GitHub settings (optional, for private repos)
GITHUB_TOKEN=your_github_token

# API settings
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=False

# Analysis settings
MIN_QUALITY_SCORE=5.0
MAX_PROCESSING_BATCH_SIZE=100
```

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Quality
```bash
black ai_prompt_analyzer/
flake8 ai_prompt_analyzer/
```

## License

MIT License - see LICENSE file for details.
