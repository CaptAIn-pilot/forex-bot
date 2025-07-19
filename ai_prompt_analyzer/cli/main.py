"""Command-line interface for the AI Prompt Analyzer."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

from ..core.analyzer import PromptAnalyzer
from ..core.filter_engine import FilterEngine
from ..models import FilterCriteria, FilterLevel, SummaryLevel, AIProvider, PromptType


app = typer.Typer(
    name="ai-prompt-analyzer",
    help="Advanced AI Prompt Analyzer Bot - Analyze and optimize AI system prompts",
    no_args_is_help=True
)

console = Console()


@app.command()
def analyze(
    repo_url: str = typer.Argument(..., help="Repository URL to analyze"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("json", "--format", "-f", help="Output format (json, csv, markdown)"),
    filter_level: str = typer.Option("moderate", "--filter", help="Filter level (strict, moderate, permissive)"),
    min_quality: float = typer.Option(5.0, "--min-quality", help="Minimum quality score"),
    max_results: Optional[int] = typer.Option(None, "--max-results", help="Maximum number of results"),
    force_refresh: bool = typer.Option(False, "--force-refresh", help="Force refresh of cached data"),
    include_summary: bool = typer.Option(True, "--summary/--no-summary", help="Include summary"),
    summary_level: str = typer.Option("executive", "--summary-level", help="Summary level (executive, technical, implementation)")
):
    """Analyze prompts from a repository."""
    
    console.print(Panel.fit(
        f"[bold blue]AI Prompt Analyzer[/bold blue]\n"
        f"Analyzing repository: {repo_url}",
        title="Analysis Started"
    ))
    
    async def run_analysis():
        analyzer = PromptAnalyzer()
        
        # Create filter criteria
        try:
            filter_level_enum = FilterLevel(filter_level.lower())
        except ValueError:
            console.print(f"[red]Invalid filter level: {filter_level}[/red]")
            return
        
        criteria = FilterCriteria(
            min_quality_score=min_quality,
            filter_level=filter_level_enum
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Analyzing repository...", total=None)
            
            try:
                # Run analysis
                results = await analyzer.analyze_repository(
                    repo_url, 
                    criteria, 
                    force_refresh
                )
                
                progress.update(task, description="Analysis complete!")
                
                # Limit results if specified
                if max_results and len(results) > max_results:
                    results = results[:max_results]
                
                # Display results summary
                _display_results_summary(results)
                
                # Generate summary if requested
                if include_summary:
                    try:
                        summary_level_enum = SummaryLevel(summary_level.lower())
                        summary = analyzer.generate_summary(results, summary_level_enum)
                        _display_summary(summary)
                    except ValueError:
                        console.print(f"[yellow]Invalid summary level: {summary_level}[/yellow]")
                
                # Export results
                if output_file:
                    exported_data = analyzer.export_results(results, format)
                    Path(output_file).write_text(exported_data)
                    console.print(f"[green]Results exported to {output_file}[/green]")
                else:
                    # Display sample results
                    _display_sample_results(results[:5])
                
            except Exception as e:
                progress.update(task, description=f"Error: {str(e)}")
                console.print(f"[red]Analysis failed: {e}[/red]")
                raise typer.Exit(1)
    
    asyncio.run(run_analysis())


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode")
):
    """Start the web API server."""
    
    console.print(Panel.fit(
        f"[bold green]Starting AI Prompt Analyzer Server[/bold green]\n"
        f"Host: {host}\n"
        f"Port: {port}\n"
        f"Debug: {debug}",
        title="Server Configuration"
    ))
    
    try:
        import uvicorn
        from ..api.main import app as fastapi_app
        
        uvicorn.run(
            "ai_prompt_analyzer.api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="debug" if debug else "info"
        )
    except ImportError:
        console.print("[red]FastAPI not installed. Install with: pip install fastapi uvicorn[/red]")
        raise typer.Exit(1)


@app.command()
def filter_prompts(
    input_file: str = typer.Argument(..., help="Input file with analysis results (JSON format)"),
    output_file: str = typer.Argument(..., help="Output file for filtered results"),
    profile: Optional[str] = typer.Option(None, "--profile", help="Filter profile (coding, creative, educational, etc.)"),
    min_quality: float = typer.Option(5.0, "--min-quality", help="Minimum quality score"),
    max_quality: float = typer.Option(10.0, "--max-quality", help="Maximum quality score"),
    providers: Optional[str] = typer.Option(None, "--providers", help="Comma-separated list of allowed providers"),
    types: Optional[str] = typer.Option(None, "--types", help="Comma-separated list of allowed types"),
    categories: Optional[str] = typer.Option(None, "--categories", help="Comma-separated list of required categories"),
    exclude_categories: Optional[str] = typer.Option(None, "--exclude-categories", help="Comma-separated list of excluded categories"),
    filter_level: str = typer.Option("moderate", "--filter", help="Filter level (strict, moderate, permissive)")
):
    """Filter previously analyzed prompts."""
    
    import json
    from ..models import AnalysisResult
    
    # Load results
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        # Convert to AnalysisResult objects
        results = [AnalysisResult(**item) for item in data]
        console.print(f"[green]Loaded {len(results)} results from {input_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error loading input file: {e}[/red]")
        raise typer.Exit(1)
    
    # Create filter criteria
    filter_engine = FilterEngine()
    
    try:
        filter_level_enum = FilterLevel(filter_level.lower())
    except ValueError:
        console.print(f"[red]Invalid filter level: {filter_level}[/red]")
        raise typer.Exit(1)
    
    # Build criteria
    criteria_dict = {
        'min_quality_score': min_quality,
        'max_quality_score': max_quality,
        'filter_level': filter_level_enum
    }
    
    if providers:
        try:
            criteria_dict['allowed_providers'] = [
                AIProvider(p.strip().lower()) for p in providers.split(',')
            ]
        except ValueError as e:
            console.print(f"[red]Invalid provider: {e}[/red]")
            raise typer.Exit(1)
    
    if types:
        try:
            criteria_dict['allowed_types'] = [
                PromptType(t.strip().lower()) for t in types.split(',')
            ]
        except ValueError as e:
            console.print(f"[red]Invalid type: {e}[/red]")
            raise typer.Exit(1)
    
    if categories:
        criteria_dict['required_categories'] = [c.strip() for c in categories.split(',')]
    
    if exclude_categories:
        criteria_dict['excluded_categories'] = [c.strip() for c in exclude_categories.split(',')]
    
    # Use profile if specified
    if profile:
        criteria = filter_engine.create_custom_filter_profile(profile, criteria_dict)
    else:
        criteria = FilterCriteria(**criteria_dict)
    
    # Validate criteria
    issues = filter_engine.validate_filter_criteria(criteria)
    if issues:
        console.print("[red]Filter criteria validation errors:[/red]")
        for issue in issues:
            console.print(f"  - {issue}")
        raise typer.Exit(1)
    
    # Apply filters
    filtered_results = filter_engine.filter_prompts(results, criteria)
    
    # Get statistics
    stats = filter_engine.get_filter_statistics(results, filtered_results)
    
    # Display statistics
    _display_filter_statistics(stats)
    
    # Save filtered results
    try:
        exported_data = json.dumps([r.dict() for r in filtered_results], indent=2, default=str)
        Path(output_file).write_text(exported_data)
        console.print(f"[green]Filtered results saved to {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error saving output file: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def monitor(
    repo_url: str = typer.Argument(..., help="Repository URL to monitor"),
    interval: int = typer.Option(300, "--interval", help="Check interval in seconds"),
    auto_analyze: bool = typer.Option(False, "--auto-analyze", help="Automatically analyze when changes detected")
):
    """Monitor a repository for changes."""
    
    console.print(Panel.fit(
        f"[bold yellow]Monitoring Repository[/bold yellow]\n"
        f"URL: {repo_url}\n"
        f"Interval: {interval} seconds\n"
        f"Auto-analyze: {auto_analyze}",
        title="Repository Monitor"
    ))
    
    async def monitor_repo():
        analyzer = PromptAnalyzer()
        
        async def change_callback(url: str, has_changes: bool):
            if has_changes:
                console.print(f"[green]Changes detected in {url}[/green]")
                
                if auto_analyze:
                    console.print("Starting automatic analysis...")
                    try:
                        results = await analyzer.analyze_repository(url, force_refresh=True)
                        console.print(f"[green]Analysis complete: {len(results)} prompts processed[/green]")
                    except Exception as e:
                        console.print(f"[red]Auto-analysis failed: {e}[/red]")
        
        try:
            console.print("Starting monitoring... Press Ctrl+C to stop")
            
            async for has_updates in analyzer.monitor_repository_changes(
                repo_url, change_callback, interval
            ):
                if has_updates:
                    console.print(f"[blue]Update detected at {typer.datetime.now()}[/blue]")
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Monitoring stopped by user[/yellow]")
        except Exception as e:
            console.print(f"[red]Monitoring error: {e}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(monitor_repo())


@app.command()
def info(
    repo_url: str = typer.Argument(..., help="Repository URL to get info for")
):
    """Get repository information."""
    
    async def get_info():
        analyzer = PromptAnalyzer()
        
        try:
            info = await analyzer.get_repository_info(repo_url)
            
            # Display repository info
            table = Table(title="Repository Information")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("URL", info.url)
            table.add_row("Name", info.name)
            table.add_row("Last Updated", str(info.last_updated))
            table.add_row("Total Files", str(info.total_files))
            table.add_row("Processable Files", str(info.processed_files))
            table.add_row("Last Commit", info.last_commit_sha or "Unknown")
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error getting repository info: {e}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(get_info())


def _display_results_summary(results):
    """Display summary of analysis results."""
    
    table = Table(title="Analysis Results Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    if results:
        avg_quality = sum(r.quality_metrics.overall_score for r in results) / len(results)
        providers = list(set(r.ai_provider.value for r in results))
        categories = list(set(cat for r in results for cat in r.categories))
        techniques = list(set(tech for r in results for tech in r.techniques))
        
        table.add_row("Total Prompts", str(len(results)))
        table.add_row("Average Quality", f"{avg_quality:.2f}/10")
        table.add_row("Providers", ", ".join(providers))
        table.add_row("Categories", f"{len(categories)} unique")
        table.add_row("Techniques", f"{len(techniques)} unique")
    else:
        table.add_row("Total Prompts", "0")
        table.add_row("Status", "No prompts found")
    
    console.print(table)


def _display_summary(summary):
    """Display analysis summary."""
    
    console.print(Panel.fit(
        f"[bold]{summary.level.value.title()} Summary[/bold]",
        title="Analysis Summary"
    ))
    
    # Key insights
    if summary.key_insights:
        console.print("\n[bold cyan]Key Insights:[/bold cyan]")
        for insight in summary.key_insights:
            console.print(f"  • {insight}")
    
    # Recommendations
    if summary.recommendations:
        console.print("\n[bold green]Recommendations:[/bold green]")
        for rec in summary.recommendations:
            console.print(f"  • {rec}")
    
    # Top categories and techniques
    if summary.top_categories:
        console.print(f"\n[bold yellow]Top Categories:[/bold yellow] {', '.join(summary.top_categories[:5])}")
    
    if summary.top_techniques:
        console.print(f"\n[bold yellow]Top Techniques:[/bold yellow] {', '.join(summary.top_techniques[:5])}")


def _display_sample_results(results):
    """Display sample results in a table."""
    
    if not results:
        return
    
    table = Table(title="Sample Results")
    table.add_column("ID", width=12)
    table.add_column("Provider", width=12)
    table.add_column("Type", width=12)
    table.add_column("Quality", width=8)
    table.add_column("Categories", width=20)
    table.add_column("Preview", width=30)
    
    for result in results:
        preview = result.content[:50] + "..." if len(result.content) > 50 else result.content
        
        table.add_row(
            result.id[:12],
            result.ai_provider.value,
            result.prompt_type.value,
            f"{result.quality_metrics.overall_score:.1f}",
            ", ".join(result.categories[:2]),
            preview
        )
    
    console.print(table)


def _display_filter_statistics(stats):
    """Display filter statistics."""
    
    table = Table(title="Filter Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Original Count", str(stats['original_count']))
    table.add_row("Filtered Count", str(stats['filtered_count']))
    table.add_row("Removed Count", str(stats['removed_count']))
    table.add_row("Removal Rate", f"{stats['removal_rate']:.1%}")
    
    if stats['avg_quality_original'] > 0:
        table.add_row("Avg Quality (Original)", f"{stats['avg_quality_original']:.2f}")
    
    if stats['avg_quality_filtered'] > 0:
        table.add_row("Avg Quality (Filtered)", f"{stats['avg_quality_filtered']:.2f}")
    
    console.print(table)
    
    # Filter reasons
    if stats['filter_reasons']:
        console.print("\n[bold yellow]Filter Reasons:[/bold yellow]")
        for reason, count in stats['filter_reasons'].items():
            console.print(f"  • {reason}: {count}")


if __name__ == "__main__":
    app()