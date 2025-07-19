"""FastAPI web application for the AI Prompt Analyzer."""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict
from uuid import uuid4

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..core.analyzer import PromptAnalyzer
from ..core.filter_engine import FilterEngine
from ..models import (
    AnalysisResult, FilterCriteria, Summary, SummaryLevel,
    ProcessingJob, ProcessingStatus, RepositoryInfo,
    AIProvider, PromptType, FilterLevel, ExportFormat
)


# API Models
class AnalysisRequest(BaseModel):
    repository_url: str
    filter_criteria: Optional[FilterCriteria] = None
    force_refresh: bool = False


class FilterRequest(BaseModel):
    criteria: FilterCriteria


class ExportRequest(BaseModel):
    format: ExportFormat = ExportFormat.JSON
    include_summary: bool = True
    summary_level: SummaryLevel = SummaryLevel.EXECUTIVE


class SummaryRequest(BaseModel):
    level: SummaryLevel = SummaryLevel.EXECUTIVE


# Initialize FastAPI app
app = FastAPI(
    title="AI Prompt Analyzer API",
    description="Advanced AI Prompt Analysis and Optimization Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize analyzer
analyzer = PromptAnalyzer()
filter_engine = FilterEngine()

# In-memory storage for API results (use database in production)
api_results: Dict[str, List[AnalysisResult]] = {}


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with basic web interface."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Prompt Analyzer</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
            .section { margin: 20px 0; }
            .endpoint { background: #e8f4fd; padding: 10px; margin: 5px 0; border-radius: 3px; }
            .method { font-weight: bold; color: #0066cc; }
            pre { background: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🤖 AI Prompt Analyzer API</h1>
            <p>Advanced AI system prompt analysis and optimization platform</p>
        </div>
        
        <div class="section">
            <h2>Quick Start</h2>
            <div class="endpoint">
                <span class="method">POST</span> /analyze - Analyze a repository
            </div>
            <div class="endpoint">
                <span class="method">GET</span> /jobs/{job_id} - Check analysis progress
            </div>
            <div class="endpoint">
                <span class="method">POST</span> /filter - Filter analysis results
            </div>
            <div class="endpoint">
                <span class="method">GET</span> /results/{session_id}/summary - Get analysis summary
            </div>
        </div>
        
        <div class="section">
            <h2>Example Usage</h2>
            <pre>
# Analyze CL4R1T4S repository
curl -X POST "http://localhost:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{"repository_url": "https://github.com/elder-plinius/CL4R1T4S"}'

# Check analysis progress
curl "http://localhost:8000/jobs/{job_id}"

# Get results summary
curl "http://localhost:8000/results/{session_id}/summary"
            </pre>
        </div>
        
        <div class="section">
            <h2>Documentation</h2>
            <p><a href="/docs">Interactive API Documentation (Swagger UI)</a></p>
            <p><a href="/redoc">Alternative API Documentation (ReDoc)</a></p>
        </div>
    </body>
    </html>
    """


@app.post("/analyze", response_model=Dict[str, str])
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Start analysis of a repository."""
    
    # Create session for this analysis
    session_id = str(uuid4())
    
    # Start background analysis
    background_tasks.add_task(
        run_analysis_background,
        session_id,
        request.repository_url,
        request.filter_criteria,
        request.force_refresh
    )
    
    return {
        "session_id": session_id,
        "message": "Analysis started",
        "status": "processing"
    }


async def run_analysis_background(session_id: str, repo_url: str, 
                                filter_criteria: Optional[FilterCriteria],
                                force_refresh: bool):
    """Run analysis in background."""
    try:
        results = await analyzer.analyze_repository(
            repo_url, filter_criteria, force_refresh
        )
        api_results[session_id] = results
    except Exception as e:
        # In production, log this error properly
        print(f"Analysis error for session {session_id}: {e}")


@app.get("/jobs/{job_id}", response_model=ProcessingJob)
async def get_job_status(job_id: str):
    """Get processing job status."""
    job = analyzer.get_processing_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/results/{session_id}")
async def get_results(
    session_id: str,
    limit: Optional[int] = Query(None, description="Limit number of results"),
    offset: int = Query(0, description="Offset for pagination"),
    min_quality: Optional[float] = Query(None, description="Minimum quality score"),
    provider: Optional[str] = Query(None, description="Filter by AI provider"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """Get analysis results for a session."""
    
    if session_id not in api_results:
        raise HTTPException(status_code=404, detail="Results not found")
    
    results = api_results[session_id]
    
    # Apply filters
    if min_quality is not None:
        results = [r for r in results if r.quality_metrics.overall_score >= min_quality]
    
    if provider:
        try:
            provider_enum = AIProvider(provider.lower())
            results = [r for r in results if r.ai_provider == provider_enum]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid provider")
    
    if category:
        results = [r for r in results if category in r.categories]
    
    # Apply pagination
    total = len(results)
    if limit:
        results = results[offset:offset + limit]
    else:
        results = results[offset:]
    
    return {
        "results": results,
        "total": total,
        "offset": offset,
        "limit": limit
    }


@app.get("/results/{session_id}/summary", response_model=Summary)
async def get_summary(session_id: str, level: SummaryLevel = SummaryLevel.EXECUTIVE):
    """Get analysis summary for a session."""
    
    if session_id not in api_results:
        raise HTTPException(status_code=404, detail="Results not found")
    
    results = api_results[session_id]
    summary = analyzer.generate_summary(results, level)
    return summary


@app.post("/results/{session_id}/filter")
async def filter_results(session_id: str, request: FilterRequest):
    """Filter analysis results."""
    
    if session_id not in api_results:
        raise HTTPException(status_code=404, detail="Results not found")
    
    results = api_results[session_id]
    
    # Validate filter criteria
    issues = filter_engine.validate_filter_criteria(request.criteria)
    if issues:
        raise HTTPException(status_code=400, detail=f"Invalid filter criteria: {', '.join(issues)}")
    
    # Apply filters
    filtered_results = filter_engine.filter_prompts(results, request.criteria)
    
    # Get statistics
    stats = filter_engine.get_filter_statistics(results, filtered_results)
    
    return {
        "filtered_results": filtered_results,
        "statistics": stats
    }


@app.get("/results/{session_id}/export")
async def export_results(
    session_id: str,
    format: ExportFormat = ExportFormat.JSON,
    include_summary: bool = True,
    summary_level: SummaryLevel = SummaryLevel.EXECUTIVE
):
    """Export analysis results."""
    
    if session_id not in api_results:
        raise HTTPException(status_code=404, detail="Results not found")
    
    results = api_results[session_id]
    
    # Export results
    exported_data = analyzer.export_results(results, format.value)
    
    # Add summary if requested
    if include_summary:
        summary = analyzer.generate_summary(results, summary_level)
        
        if format == ExportFormat.JSON:
            import json
            data = json.loads(exported_data)
            data = {
                "summary": summary.dict(),
                "results": data
            }
            exported_data = json.dumps(data, indent=2, default=str)
        
        elif format == ExportFormat.MARKDOWN:
            summary_text = f"""# Analysis Summary

**Level:** {summary.level.value.title()}
**Total Prompts:** {summary.total_prompts}
**Average Quality:** {summary.average_quality:.2f}/10

## Key Insights
{chr(10).join(f"- {insight}" for insight in summary.key_insights)}

## Recommendations
{chr(10).join(f"- {rec}" for rec in summary.recommendations)}

## Top Categories
{', '.join(summary.top_categories)}

## Top Techniques
{', '.join(summary.top_techniques)}

---

"""
            exported_data = summary_text + exported_data
    
    # Return as file download
    filename = f"prompt_analysis_{session_id}.{format.value}"
    
    # Create temporary file
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format.value}', delete=False) as f:
        f.write(exported_data)
        temp_path = f.name
    
    return FileResponse(
        temp_path,
        filename=filename,
        media_type="application/octet-stream"
    )


@app.get("/results/{session_id}/clusters")
async def get_clusters(session_id: str, n_clusters: int = 5):
    """Get clustered prompts."""
    
    if session_id not in api_results:
        raise HTTPException(status_code=404, detail="Results not found")
    
    results = api_results[session_id]
    clusters = await analyzer.cluster_prompts(results, n_clusters)
    
    # Convert to serializable format
    cluster_data = {}
    for cluster_id, cluster_results in clusters.items():
        cluster_data[str(cluster_id)] = {
            "count": len(cluster_results),
            "avg_quality": sum(r.quality_metrics.overall_score for r in cluster_results) / len(cluster_results),
            "results": cluster_results
        }
    
    return cluster_data


@app.get("/results/{session_id}/best")
async def get_best_prompts(session_id: str, n: int = 10):
    """Get the best prompts by quality score."""
    
    if session_id not in api_results:
        raise HTTPException(status_code=404, detail="Results not found")
    
    results = api_results[session_id]
    best_prompts = analyzer.get_best_prompts(results, n)
    
    return {"best_prompts": best_prompts}


@app.get("/repository/info")
async def get_repository_info(repo_url: str):
    """Get repository information."""
    
    try:
        info = await analyzer.get_repository_info(repo_url)
        return info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/filter/profiles")
async def get_filter_profiles():
    """Get available filter profiles."""
    
    profiles = {
        "agent_optimization": {
            "description": "Optimized for AI agent development",
            "focus": "System prompts and instructions",
            "quality_threshold": 7.0
        },
        "coding_assistance": {
            "description": "Code generation and programming help",
            "focus": "Programming and development prompts",
            "quality_threshold": 6.0
        },
        "creative_writing": {
            "description": "Creative content generation",
            "focus": "Writing and storytelling prompts",
            "quality_threshold": 5.0
        },
        "educational": {
            "description": "Learning and teaching content",
            "focus": "Educational and instructional prompts",
            "quality_threshold": 8.0
        },
        "research_analysis": {
            "description": "Research and analytical tasks",
            "focus": "Analysis and evaluation prompts",
            "quality_threshold": 7.5
        }
    }
    
    return {"profiles": profiles}


@app.post("/filter/profiles/{profile_name}")
async def create_filter_criteria_from_profile(
    profile_name: str,
    custom_requirements: Optional[Dict] = None
):
    """Create filter criteria from a profile."""
    
    try:
        requirements = custom_requirements or {}
        criteria = filter_engine.create_custom_filter_profile(profile_name, requirements)
        return criteria
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0"
    }


@app.get("/stats")
async def get_api_stats():
    """Get API usage statistics."""
    
    total_sessions = len(api_results)
    total_prompts = sum(len(results) for results in api_results.values())
    
    return {
        "total_sessions": total_sessions,
        "total_prompts_analyzed": total_prompts,
        "active_sessions": list(api_results.keys())
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Resource not found", "detail": str(exc)}


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error", "detail": "An unexpected error occurred"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)