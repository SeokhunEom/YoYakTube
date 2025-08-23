"""
Transcript extraction CLI module

Command-line interface for extracting YouTube transcripts.
"""

import click
import json
import sys
import os
from typing import List, Dict

# Add parent directory to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from Core.utils import extract_video_id
from Core.transcript import collect_transcript, collect_transcript_entries


def format_as_srt(entries: List[Dict], language: str) -> str:
    """Format transcript entries as SRT subtitle format."""
    srt_lines = []

    for i, entry in enumerate(entries, 1):
        start_time = entry["start"]
        end_time = start_time + entry["duration"]

        # Convert to SRT time format (HH:MM:SS,mmm)
        def to_srt_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millisecs = int((seconds % 1) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

        start_srt = to_srt_time(start_time)
        end_srt = to_srt_time(end_time)

        srt_lines.append(f"{i}")
        srt_lines.append(f"{start_srt} --> {end_srt}")
        srt_lines.append(entry["text"])
        srt_lines.append("")  # Empty line between entries

    return "\n".join(srt_lines)


def extract_transcript_command(
    video_url_or_id: str,
    languages: str,
    output_format: str,
    output: str,
    timestamps: bool,
):
    """Extract transcript from YouTube video."""
    # Extract video ID
    video_id = extract_video_id(video_url_or_id)
    if not video_id:
        click.echo("Error: Invalid video URL or ID", err=True)
        sys.exit(1)

    # Parse languages
    lang_list = [lang.strip() for lang in languages.split(",")]

    # Determine what to extract based on format and options
    if output_format == "srt" or timestamps:
        # Need entries with timestamps
        result = collect_transcript_entries(video_id, lang_list)
        if not result:
            click.echo("Error: Could not extract transcript", err=True)
            sys.exit(1)

        entries, language = result

        if output_format == "text":
            # Text format with timestamps
            output_lines = []
            for entry in entries:
                start_mins = int(entry["start"] // 60)
                start_secs = int(entry["start"] % 60)
                timestamp = f"[{start_mins:02d}:{start_secs:02d}]"
                output_lines.append(f"{timestamp} {entry['text']}")
            content = "\n".join(output_lines)
        elif output_format == "json":
            # JSON format
            content = json.dumps(
                {"video_id": video_id, "language": language, "entries": entries},
                indent=2,
                ensure_ascii=False,
            )
        elif output_format == "srt":
            # SRT format
            content = format_as_srt(entries, language)
    else:
        # Plain text without timestamps
        result = collect_transcript(video_id, lang_list)
        if not result:
            click.echo("Error: Could not extract transcript", err=True)
            sys.exit(1)

        text, language = result

        if output_format == "json":
            content = json.dumps(
                {"video_id": video_id, "language": language, "text": text},
                indent=2,
                ensure_ascii=False,
            )
        else:
            content = text

    # Output to file or stdout
    if output:
        try:
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
            click.echo(f"Transcript saved to {output}")
        except Exception as e:
            click.echo(f"Error writing to file: {e}", err=True)
            sys.exit(1)
    else:
        click.echo(content)


@click.command()
@click.argument("video_url_or_id")
@click.option(
    "--languages", default="ko,en,ja", help="Preferred language order (comma-separated)"
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "srt"]),
    default="text",
    help="Output format",
)
@click.option("--output", help="Output file name")
@click.option("--timestamps/--no-timestamps", default=False, help="Include timestamps")
def main(video_url_or_id, languages, output_format, output, timestamps):
    """Extract transcript from YouTube video"""
    extract_transcript_command(
        video_url_or_id, languages, output_format, output, timestamps
    )


if __name__ == "__main__":
    main()
