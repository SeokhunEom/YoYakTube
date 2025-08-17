"""
Main CLI interface for YoYakTube

Provides unified access to all YoYakTube functionality.
"""

import click
import sys
import os

# Add parent directory to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """YoYakTube - YouTube Video Summarization and Q&A Chatbot"""
    pass


@cli.command()
@click.argument('video_url_or_id')
@click.option('--languages', default='ko,en,ja', help='Preferred language order (comma-separated)')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json', 'srt']), default='text', help='Output format')
@click.option('--output', help='Output file name')
@click.option('--timestamps/--no-timestamps', default=False, help='Include timestamps')
def transcript(video_url_or_id, languages, output_format, output, timestamps):
    """Extract transcript from YouTube video"""
    from .yyt_transcript import extract_transcript_command
    extract_transcript_command(video_url_or_id, languages, output_format, output, timestamps)


@cli.command()
@click.argument('video_url_or_id', required=False)
@click.option('--file', 'input_file', help='Read transcript from file')
@click.option('--stdin', 'use_stdin', is_flag=True, help='Read transcript from stdin')
@click.option('--provider', default='openai', help='AI provider')
@click.option('--model', default='gpt-5-mini', help='Model name')
@click.option('--output', help='Output file name')
@click.option('--languages', default='ko,en,ja', help='Transcript language priority')
def summarize(video_url_or_id, input_file, use_stdin, provider, model, output, languages):
    """Summarize video or transcript"""
    from .yyt_summarize import summarize_command
    summarize_command(video_url_or_id, input_file, use_stdin, provider, model, output, languages)


@cli.command()
@click.argument('video_url_or_id', required=False)
@click.option('--file', 'input_file', help='Read transcript from file')
@click.option('--interactive', is_flag=True, help='Interactive mode')
@click.option('--question', help='Single question')
@click.option('--provider', default='openai', help='AI provider')
@click.option('--model', default='gpt-5-mini', help='Model name')
def chat(video_url_or_id, input_file, interactive, question, provider, model):
    """Chat with video transcript"""
    from .yyt_chat import chat_command
    chat_command(video_url_or_id, input_file, interactive, question, provider, model)


@cli.group()
def ai():
    """AI model management"""
    pass


@ai.command('list')
@click.option('--provider', help='Show models for specific provider')
def list_models(provider):
    """List available models"""
    from .yyt_ai import list_models_command
    list_models_command(provider)


@ai.command('test')
@click.argument('provider')
@click.argument('model')
@click.option('--prompt', default='Hello, please respond with a simple greeting.', help='Test prompt')
def test_model(provider, model, prompt):
    """Test model connection"""
    from .yyt_ai import test_model_command
    test_model_command(provider, model, prompt)


@ai.command('chat')
@click.option('--provider', default='openai', help='AI provider')
@click.option('--model', default='gpt-5-mini', help='Model name')
def ai_chat(provider, model):
    """Direct chat with AI model"""
    from .yyt_ai import direct_chat_command
    direct_chat_command(provider, model)


@ai.command('benchmark')
@click.option('--models', help='Comma-separated list of models to benchmark')
@click.option('--prompt', default='Summarize the concept of machine learning in 2 sentences.', help='Benchmark prompt')
@click.option('--output', help='Save results to file')
def benchmark(models, prompt, output):
    """Benchmark model performance"""
    from .yyt_ai import benchmark_command
    benchmark_command(models, prompt, output)


@cli.command()
@click.argument('video_url_or_id')
def meta(video_url_or_id):
    """Extract video metadata"""
    from yoyaktube.utils import extract_video_id
    from yoyaktube.metadata import fetch_video_metadata
    import json
    
    video_id = extract_video_id(video_url_or_id)
    if not video_id:
        click.echo("Error: Invalid video URL or ID", err=True)
        sys.exit(1)
    
    metadata = fetch_video_metadata(video_id)
    if metadata:
        click.echo(json.dumps(metadata, indent=2, ensure_ascii=False))
    else:
        click.echo("Error: Could not extract metadata", err=True)
        sys.exit(1)


@cli.group()
def config():
    """Configuration management"""
    pass


@config.command('show')
def show_config():
    """Show current configuration"""
    click.echo("Current configuration:")
    click.echo(f"OPENAI_API_KEY: {'Set' if os.getenv('OPENAI_API_KEY') else 'Not set'}")
    click.echo(f"YYT_CONFIG: {os.getenv('YYT_CONFIG', 'Not set')}")


@cli.group()
def pipeline():
    """Pipeline commands"""
    pass


@pipeline.command('channel-summary')
@click.argument('channel_url')
@click.option('--max-videos', default=10, help='Maximum videos to process')
@click.option('--output-dir', default='./results', help='Output directory')
def channel_summary(channel_url, max_videos, output_dir):
    """Summarize recent videos from a channel"""
    click.echo(f"Channel summary pipeline for {channel_url} (max {max_videos} videos)")
    click.echo(f"Output directory: {output_dir}")
    click.echo("This feature is not yet implemented.")


@pipeline.command('full-analysis')
@click.argument('video_url')
@click.option('--output-dir', default='./results', help='Output directory')
def full_analysis(video_url, output_dir):
    """Complete video analysis pipeline"""
    click.echo(f"Full analysis pipeline for {video_url}")
    click.echo(f"Output directory: {output_dir}")
    click.echo("This feature is not yet implemented.")


if __name__ == '__main__':
    cli()