"""
Utility functions for YoYakTube

Provides helper functions for video ID extraction, time formatting,
and context building for LLM processing.
"""

import re
from typing import Optional, List, Dict
from urllib.parse import urlparse, parse_qs


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from various URL formats.
    
    Args:
        url: YouTube video URL or video ID
        
    Returns:
        11-character video ID or None if invalid
        
    Supports:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/shorts/VIDEO_ID
        - VIDEO_ID (if already 11 characters)
    """
    if not url:
        return None
    
    # If it's already an 11-character video ID
    if len(url) == 11 and re.match(r'^[a-zA-Z0-9_-]+$', url):
        return url
    
    # YouTube URL patterns - only match valid YouTube domains
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check for valid YouTube domains
        valid_domains = ['youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be']
        if domain in valid_domains:
            patterns = [
                r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
                r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
                r'youtube\.com/v/([a-zA-Z0-9_-]{11})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    video_id = match.group(1)
                    # Validate that it's exactly 11 characters
                    if len(video_id) == 11:
                        return video_id
    except Exception:
        pass
    
    # Alternative: Try parsing query parameters for valid YouTube domains
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        valid_domains = ['youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be']
        
        if domain in valid_domains:
            query_params = parse_qs(parsed.query)
            if 'v' in query_params:
                video_id = query_params['v'][0]
                if len(video_id) == 11 and re.match(r'^[a-zA-Z0-9_-]+$', video_id):
                    return video_id
    except Exception:
        pass
    
    return None


def format_hms(seconds: Optional[float]) -> str:
    """
    Format seconds to H:MM:SS format.
    
    Args:
        seconds: Time in seconds (can be None)
        
    Returns:
        Formatted time string (H:MM:SS)
    """
    if seconds is None:
        return "0:00:00"
    
    try:
        total_seconds = int(float(seconds))
        
        # Handle negative seconds
        if total_seconds < 0:
            return "0:00:00"
            
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        
        return f"{hours}:{minutes:02d}:{secs:02d}"
    except (ValueError, TypeError):
        return "0:00:00"


def build_llm_summary_context(
    source_url: str = None,
    duration_sec: float = None, 
    upload_date: str = None,
    transcript_entries: List[Dict] = None,
    plain_transcript: str = None
) -> str:
    """
    Build structured context for LLM summarization.
    
    Args:
        source_url: Source video URL
        duration_sec: Video duration in seconds
        upload_date: Upload date string
        transcript_entries: List of transcript entries with timestamps
        plain_transcript: Plain transcript text without timestamps
        
    Returns:
        Structured context string for LLM processing
    """
    context_parts = []
    
    # Add metadata section
    if source_url or duration_sec or upload_date:
        context_parts.append("=== 영상 정보 ===")
        if source_url:
            context_parts.append(f"소스: {source_url}")
        if duration_sec:
            context_parts.append(f"재생시간: {format_hms(duration_sec)}")
        if upload_date:
            context_parts.append(f"업로드: {upload_date}")
        context_parts.append("")
    
    # Add transcript section
    context_parts.append("=== 자막 내용 ===")
    
    if transcript_entries:
        # Use timestamped entries if available
        for entry in transcript_entries:
            try:
                start_time = entry.get('start', 0)
                text = entry.get('text', '').strip()
                if text:
                    # Format timestamp as [MM:SS]
                    minutes = int(start_time // 60)
                    seconds = int(start_time % 60)
                    timestamp = f"[{minutes:02d}:{seconds:02d}]"
                    context_parts.append(f"{timestamp} {text}")
            except (KeyError, TypeError, ValueError):
                # Skip malformed entries
                continue
    elif plain_transcript:
        # Use plain transcript as fallback
        context_parts.append(plain_transcript.strip())
    else:
        context_parts.append("(자막 없음)")
    
    return "\n".join(context_parts)