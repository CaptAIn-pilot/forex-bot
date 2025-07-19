#!/usr/bin/env python3
"""
AI Prompt Analyzer - Example Usage Script

This script demonstrates the core functionality of the AI Prompt Analyzer
without requiring heavy ML dependencies.
"""

import asyncio
import json
from pathlib import Path

from ai_prompt_analyzer.core.analyzer import PromptAnalyzer
from ai_prompt_analyzer.core.filter_engine import FilterEngine
from ai_prompt_analyzer.models import FilterCriteria, FilterLevel, SummaryLevel


async def main():
    """Main example function."""
    
    print("🤖 AI Prompt Analyzer - Example Usage")
    print("=" * 50)
    
    # Initialize the analyzer
    analyzer = PromptAnalyzer()
    
    # Example 1: Get repository information
    print("\n1. Getting repository information...")
    repo_url = "https://github.com/elder-plinius/CL4R1T4S"
    
    try:
        repo_info = await analyzer.get_repository_info(repo_url)
        print(f"✓ Repository: {repo_info.name}")
        print(f"✓ Total files: {repo_info.total_files}")
        print(f"✓ Processable files: {repo_info.processed_files}")
        print(f"✓ Last updated: {repo_info.last_updated}")
    except Exception as e:
        print(f"✗ Error getting repository info: {e}")
        return
    
    # Example 2: Analyze repository (limited sample)
    print("\n2. Analyzing repository prompts...")
    
    try:
        # Create basic filter criteria
        criteria = FilterCriteria(
            min_quality_score=3.0,  # Lower threshold for demo
            filter_level=FilterLevel.PERMISSIVE,
            min_word_count=5,
            max_word_count=2000
        )
        
        results = await analyzer.analyze_repository(repo_url, criteria, force_refresh=False)
        print(f"✓ Analyzed {len(results)} prompts")
        
        if results:
            # Show some sample results
            print("\n3. Sample analysis results:")
            for i, result in enumerate(results[:3]):  # Show first 3
                print(f"\nResult {i+1}:")
                print(f"  ID: {result.id[:12]}...")
                print(f"  Provider: {result.ai_provider.value}")
                print(f"  Type: {result.prompt_type.value}")
                print(f"  Quality: {result.quality_metrics.overall_score:.1f}/10")
                print(f"  Categories: {', '.join(result.categories[:3])}")
                print(f"  Techniques: {', '.join(result.techniques[:3])}")
                print(f"  Preview: {result.content[:100]}...")
            
            # Example 4: Generate summary
            print("\n4. Executive summary:")
            summary = analyzer.generate_summary(results, SummaryLevel.EXECUTIVE)
            
            print(f"  Total prompts: {summary.total_prompts}")
            print(f"  Average quality: {summary.average_quality:.2f}/10")
            print(f"  Top categories: {', '.join(summary.top_categories[:3])}")
            print(f"  Top techniques: {', '.join(summary.top_techniques[:3])}")
            
            print("\n  Key insights:")
            for insight in summary.key_insights[:3]:
                print(f"    • {insight}")
            
            print("\n  Recommendations:")
            for rec in summary.recommendations[:3]:
                print(f"    • {rec}")
            
            # Example 5: Filter results
            print("\n5. Applying strict filters...")
            filter_engine = FilterEngine()
            
            strict_criteria = FilterCriteria(
                min_quality_score=7.0,
                filter_level=FilterLevel.STRICT,
                min_word_count=20
            )
            
            filtered_results = filter_engine.filter_prompts(results, strict_criteria)
            print(f"✓ Filtered to {len(filtered_results)} high-quality prompts")
            
            # Example 6: Export results
            print("\n6. Exporting results...")
            
            # Export as JSON
            json_export = analyzer.export_results(filtered_results[:5], 'json')
            
            # Save to file
            output_file = Path("/tmp/sample_analysis.json")
            output_file.write_text(json_export)
            print(f"✓ Exported sample results to {output_file}")
            
            # Export as markdown
            md_export = analyzer.export_results(filtered_results[:3], 'markdown')
            md_file = Path("/tmp/sample_analysis.md")
            md_file.write_text(md_export)
            print(f"✓ Exported markdown report to {md_file}")
            
        else:
            print("✗ No prompts found in repository")
            
    except Exception as e:
        print(f"✗ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("✓ Example completed successfully!")
    print("\nNext steps:")
    print("1. Install ML dependencies: pip install transformers torch sentence-transformers")
    print("2. Install web dependencies: pip install fastapi uvicorn")
    print("3. Run full analysis: python -m ai_prompt_analyzer analyze <repo_url>")
    print("4. Start web server: python -m ai_prompt_analyzer serve")


if __name__ == "__main__":
    asyncio.run(main())