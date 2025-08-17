"""
Summarization CLI module

Command-line interface for summarizing videos or transcripts.
"""

import click
import sys
import os
from typing import Optional

# Add parent directory to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from yoyaktube.utils import extract_video_id, build_llm_summary_context
from yoyaktube.transcript import collect_transcript_entries, collect_transcript
from yoyaktube.metadata import fetch_video_metadata
from yoyaktube.llm import get_or_create_llm, ChatMessage


SUMMARY_PROMPT = """다음 YouTube 영상의 자막을 바탕으로 한국어로 구조화된 요약을 작성해주세요.

요약 형식:
1. **핵심 주제**: 영상의 메인 주제를 1-2문장으로 설명
2. **주요 내용**: 
   - 중요한 포인트들을 불릿 포인트로 정리
   - 시간대별 주요 내용이 있다면 [MM:SS] 형식으로 표시
3. **핵심 메시지**: 영상에서 전달하고자 하는 핵심 메시지나 결론

자막 내용:
{context}

위 내용을 바탕으로 체계적이고 이해하기 쉬운 요약을 한국어로 작성해주세요."""


def get_api_key() -> str:
    """Get OpenAI API key from environment."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        click.echo("Error: OPENAI_API_KEY environment variable is required", err=True)
        sys.exit(1)
    return api_key


def read_transcript_from_file(file_path: str) -> str:
    """Read transcript content from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        click.echo(f"Error reading file {file_path}: {e}", err=True)
        sys.exit(1)


def read_transcript_from_stdin() -> str:
    """Read transcript content from stdin."""
    try:
        return sys.stdin.read().strip()
    except Exception as e:
        click.echo(f"Error reading from stdin: {e}", err=True)
        sys.exit(1)


def summarize_command(video_url_or_id: Optional[str], input_file: Optional[str], use_stdin: bool, 
                     provider: str, model: str, output: Optional[str], languages: str):
    """Summarize video or transcript."""
    
    # Get API key
    api_key = get_api_key()
    
    # Determine input source
    context = None
    source_url = None
    
    if use_stdin:
        # Read from stdin
        transcript_text = read_transcript_from_stdin()
        context = build_llm_summary_context(plain_transcript=transcript_text)
    elif input_file:
        # Read from file
        transcript_text = read_transcript_from_file(input_file)
        context = build_llm_summary_context(plain_transcript=transcript_text)
    elif video_url_or_id:
        # Extract from video
        video_id = extract_video_id(video_url_or_id)
        if not video_id:
            click.echo("Error: Invalid video URL or ID", err=True)
            sys.exit(1)
        
        # Parse languages
        lang_list = [lang.strip() for lang in languages.split(',')]
        
        # Get transcript with timestamps if possible
        entries_result = collect_transcript_entries(video_id, lang_list)
        
        # Get metadata
        metadata = fetch_video_metadata(video_id)
        
        if entries_result:
            entries, language = entries_result
            duration_sec = metadata.get('duration') if metadata else None
            upload_date = metadata.get('upload_date') if metadata else None
            source_url = f"https://www.youtube.com/watch?v={video_id}"
            
            context = build_llm_summary_context(
                source_url=source_url,
                duration_sec=duration_sec,
                upload_date=upload_date,
                transcript_entries=entries
            )
        else:
            # Fallback to plain transcript
            text_result = collect_transcript(video_id, lang_list)
            if not text_result:
                click.echo("Error: Could not extract transcript", err=True)
                sys.exit(1)
            
            text, language = text_result
            context = build_llm_summary_context(plain_transcript=text)
    else:
        click.echo("Error: Must provide video URL/ID, --file, or --stdin", err=True)
        sys.exit(1)
    
    if not context:
        click.echo("Error: No transcript content to summarize", err=True)
        sys.exit(1)
    
    # Create LLM client
    try:
        llm = get_or_create_llm(provider, model, api_key)
    except Exception as e:
        click.echo(f"Error creating LLM client: {e}", err=True)
        sys.exit(1)
    
    # Generate summary
    try:
        messages = [
            ChatMessage(role="user", content=SUMMARY_PROMPT.format(context=context))
        ]
        
        response = llm.chat(messages, temperature=0.2)
        summary = response.content
        
        # Output summary
        if output:
            try:
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(summary)
                click.echo(f"Summary saved to {output}")
            except Exception as e:
                click.echo(f"Error writing to file: {e}", err=True)
                sys.exit(1)
        else:
            click.echo(summary)
            
    except Exception as e:
        click.echo(f"Error generating summary: {e}", err=True)
        sys.exit(1)


@click.command()
@click.argument('video_url_or_id', required=False)
@click.option('--file', 'input_file', help='Read transcript from file')
@click.option('--stdin', 'use_stdin', is_flag=True, help='Read transcript from stdin')
@click.option('--provider', default='openai', help='AI provider')
@click.option('--model', default='gpt-5-mini', help='Model name')
@click.option('--output', help='Output file name')
@click.option('--languages', default='ko,en,ja', help='Transcript language priority')
def main(video_url_or_id, input_file, use_stdin, provider, model, output, languages):
    """Summarize video or transcript"""
    summarize_command(video_url_or_id, input_file, use_stdin, provider, model, output, languages)


if __name__ == '__main__':
    main()