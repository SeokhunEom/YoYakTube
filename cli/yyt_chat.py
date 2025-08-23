"""
Chat CLI module

Command-line interface for Q&A chat with video transcripts.
"""

import click
import sys
import os
from typing import Optional, List

# Add parent directory to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from Core.utils import extract_video_id, build_llm_summary_context
from Core.transcript import collect_transcript_entries, collect_transcript
from Core.metadata import fetch_video_metadata
from Core.llm import get_or_create_llm, ChatMessage


CHAT_SYSTEM_PROMPT = """당신은 YouTube 영상의 자막을 바탕으로 질문에 답변하는 AI 어시스턴트입니다.

다음 규칙을 따라주세요:
1. 제공된 자막 내용을 바탕으로만 답변하세요
2. 자막에 없는 내용에 대해서는 "자막에서 해당 내용을 찾을 수 없습니다"라고 답변하세요
3. 답변할 때 관련된 시간대가 있다면 [MM:SS] 형식으로 표시해주세요
4. 한국어로 친근하고 정확하게 답변하세요
5. 질문이 영상 내용과 관련이 없다면 영상 내용으로 돌아가도록 안내하세요

영상 자막 내용:
{context}

위 자막 내용을 참고하여 사용자의 질문에 답변해주세요."""


def get_api_key() -> str:
    """Get OpenAI API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        click.echo("Error: OPENAI_API_KEY environment variable is required", err=True)
        sys.exit(1)
    return api_key


def read_transcript_from_file(file_path: str) -> str:
    """Read transcript content from file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        click.echo(f"Error reading file {file_path}: {e}", err=True)
        sys.exit(1)


def setup_context(video_url_or_id: Optional[str], input_file: Optional[str]) -> str:
    """Setup chat context from video or file."""
    if input_file:
        # Read from file
        transcript_text = read_transcript_from_file(input_file)
        return build_llm_summary_context(plain_transcript=transcript_text)

    elif video_url_or_id:
        # Extract from video
        video_id = extract_video_id(video_url_or_id)
        if not video_id:
            click.echo("Error: Invalid video URL or ID", err=True)
            sys.exit(1)

        # Default languages
        lang_list = ["ko", "en", "ja"]

        # Get transcript with timestamps if possible
        entries_result = collect_transcript_entries(video_id, lang_list)

        # Get metadata
        metadata = fetch_video_metadata(video_id)

        if entries_result:
            entries, language = entries_result
            duration_sec = metadata.get("duration") if metadata else None
            upload_date = metadata.get("upload_date") if metadata else None
            source_url = f"https://www.youtube.com/watch?v={video_id}"

            return build_llm_summary_context(
                source_url=source_url,
                duration_sec=duration_sec,
                upload_date=upload_date,
                transcript_entries=entries,
            )
        else:
            # Fallback to plain transcript
            text_result = collect_transcript(video_id, lang_list)
            if not text_result:
                click.echo("Error: Could not extract transcript", err=True)
                sys.exit(1)

            text, language = text_result
            return build_llm_summary_context(plain_transcript=text)

    else:
        click.echo("Error: Must provide video URL/ID or --file", err=True)
        sys.exit(1)


def interactive_chat(llm, context: str):
    """Run interactive chat session."""
    click.echo("=== YoYakTube 대화형 채팅 ===")
    click.echo(
        "영상 내용에 대해 질문해보세요. 종료하려면 'quit' 또는 'exit'를 입력하세요."
    )
    click.echo()

    # Initialize conversation with system prompt
    conversation: List[ChatMessage] = [
        ChatMessage(role="system", content=CHAT_SYSTEM_PROMPT.format(context=context))
    ]

    while True:
        try:
            # Get user input
            user_input = input("질문: ").strip()

            # Check for exit commands
            if user_input.lower() in ["quit", "exit", "종료", "나가기"]:
                click.echo("채팅을 종료합니다.")
                break

            if not user_input:
                continue

            # Add user message to conversation
            conversation.append(ChatMessage(role="user", content=user_input))

            # Get AI response
            response = llm.chat(conversation, temperature=0.3)
            assistant_response = response.content

            # Add assistant response to conversation
            conversation.append(
                ChatMessage(role="assistant", content=assistant_response)
            )

            # Display response
            click.echo(f"답변: {assistant_response}")
            click.echo()

        except KeyboardInterrupt:
            click.echo("\n채팅을 종료합니다.")
            break
        except Exception as e:
            click.echo(f"오류가 발생했습니다: {e}")
            click.echo()


def single_question(llm, context: str, question: str):
    """Answer a single question."""
    messages = [
        ChatMessage(role="system", content=CHAT_SYSTEM_PROMPT.format(context=context)),
        ChatMessage(role="user", content=question),
    ]

    try:
        response = llm.chat(messages, temperature=0.3)
        click.echo(response.content)
    except Exception as e:
        click.echo(f"Error generating response: {e}", err=True)
        sys.exit(1)


def chat_command(
    video_url_or_id: Optional[str],
    input_file: Optional[str],
    interactive: bool,
    question: Optional[str],
    provider: str,
    model: str,
):
    """Chat with video transcript."""

    # Get API key
    api_key = get_api_key()

    # Setup context
    context = setup_context(video_url_or_id, input_file)

    # Create LLM client
    try:
        llm = get_or_create_llm(provider, model, api_key)
    except Exception as e:
        click.echo(f"Error creating LLM client: {e}", err=True)
        sys.exit(1)

    # Run chat
    if interactive:
        interactive_chat(llm, context)
    elif question:
        single_question(llm, context, question)
    else:
        click.echo("Error: Must provide --interactive or --question", err=True)
        sys.exit(1)


@click.command()
@click.argument("video_url_or_id", required=False)
@click.option("--file", "input_file", help="Read transcript from file")
@click.option("--interactive", is_flag=True, help="Interactive mode")
@click.option("--question", help="Single question")
@click.option("--provider", default="openai", help="AI provider")
@click.option("--model", default="gpt-5-mini", help="Model name")
def main(video_url_or_id, input_file, interactive, question, provider, model):
    """Chat with video transcript"""
    chat_command(video_url_or_id, input_file, interactive, question, provider, model)


if __name__ == "__main__":
    main()
